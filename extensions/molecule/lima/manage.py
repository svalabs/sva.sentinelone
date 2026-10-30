#!/usr/bin/env python3
"""Provision and destroy Linux Molecule instances using Lima."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


INSTANCE_START_TIMEOUT = 20 * 60


def run(
    command: list[str],
    *,
    capture_output: bool = False,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            check=True,
            capture_output=capture_output,
            text=True,
            timeout=timeout,
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"Command failed with exit code {error.returncode}: {command[0]}",
        ) from error
    except subprocess.TimeoutExpired as error:
        raise TimeoutError(f"Command timed out: {command[0]}") from error


def molecule_context() -> tuple[Path, Path, list[dict[str, Any]], str]:
    molecule_file = Path(os.environ["MOLECULE_FILE"]).resolve()
    instance_config = Path(os.environ["MOLECULE_INSTANCE_CONFIG"]).resolve()
    with molecule_file.open(encoding="utf-8") as file:
        config = yaml.safe_load(file)

    platforms = config.get("platforms", [])
    if not platforms:
        raise ValueError(f"No platforms configured in {molecule_file}")

    names = [platform.get("name") for platform in platforms]
    if any(not name for name in names) or len(set(names)) != len(names):
        raise ValueError(f"Platform names must be non-empty and unique in {molecule_file}")

    for platform in platforms:
        if not platform.get("lima_template"):
            raise ValueError(f"Missing lima_template for platform {platform['name']}")

    scenario = config.get("scenario", {}).get("name", molecule_file.parent.name)
    safe_scenario = re.sub(r"[^a-zA-Z0-9-]", "-", scenario).strip("-")
    return molecule_file, instance_config, platforms, safe_scenario


def instance_name(scenario: str, platform_name: str) -> str:
    name = f"molecule-{scenario}-{platform_name}"
    if len(name) > 63:
        raise ValueError(f"Generated Lima instance name is too long: {name}")
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9.-]*", name):
        raise ValueError(f"Invalid generated Lima instance name: {name}")
    return name


def lima_home() -> Path:
    configured_home = os.environ.get("LIMA_HOME")
    return Path(configured_home).expanduser() if configured_home else Path.home() / ".lima"


def existing_instances() -> set[str]:
    result = run(["limactl", "list", "--format", "{{.Name}}"], capture_output=True)
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def ssh_connection(instance: str) -> dict[str, str]:
    config_path = lima_home() / instance / "ssh.config"
    if not config_path.is_file():
        raise FileNotFoundError(f"Lima SSH config was not created: {config_path}")

    host_aliases = re.findall(
        r"(?m)^Host\s+([^\s#]+)",
        config_path.read_text(encoding="utf-8"),
    )
    alias = next((host for host in host_aliases if not any(char in host for char in "*?!")), None)
    if not alias:
        raise ValueError(f"No concrete SSH host alias found in {config_path}")

    result = run(["ssh", "-F", str(config_path), "-G", alias], capture_output=True)
    options: dict[str, str] = {}
    for line in result.stdout.splitlines():
        key, _, value = line.partition(" ")
        if key in {"hostname", "port", "user", "identityfile"} and key not in options:
            options[key] = value.strip()
    required = {"hostname", "port", "user", "identityfile"}
    if missing := required - options.keys():
        raise ValueError(f"SSH config {config_path} is missing: {', '.join(sorted(missing))}")
    options["identityfile"] = str(Path(options["identityfile"]).expanduser())
    return options


def start_lima(platform: dict[str, Any], instance: str) -> None:
    command = [
        "limactl",
        "--tty=false",
        "start",
        "--name",
        instance,
        "--cpus",
        str(platform.get("cpus", 2)),
        "--memory",
        str(platform.get("memory", 2)),
        "--disk",
        str(platform.get("disk", 20)),
    ]
    if platform.get("arch"):
        command.extend(["--arch", platform["arch"]])
    run(command + [f"template:{platform['lima_template']}"], timeout=INSTANCE_START_TIMEOUT)


def instance_record(
    platform: dict[str, Any],
    connection: dict[str, str],
) -> dict[str, Any]:
    return {
        "instance": platform["name"],
        "address": connection["hostname"],
        "port": int(connection["port"]),
        "user": platform.get("lima_user", connection["user"]),
        "identity_file": connection["identityfile"],
        "connection": "ssh",
    }


def write_instance_config(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_text(yaml.safe_dump(records, sort_keys=False), encoding="utf-8")
    temporary_path.chmod(0o600)
    temporary_path.replace(path)


def cleanup_created(created: list[str]) -> None:
    failures: list[str] = []
    available = existing_instances()
    for instance in reversed(created):
        if instance not in available:
            continue
        try:
            run(["limactl", "delete", "--force", instance], timeout=10 * 60)
        except (OSError, RuntimeError) as error:
            failures.append(f"Could not delete {instance}: {error}")
    if failures:
        raise RuntimeError("; ".join(failures))


def create_instances() -> None:
    _, instance_config, platforms, scenario = molecule_context()
    existing = existing_instances()
    records: list[dict[str, Any]] = []
    created: list[str] = []
    try:
        for platform in platforms:
            instance = instance_name(scenario, platform["name"])
            if instance in existing:
                raise RuntimeError(
                    f"Lima instance {instance} already exists; run molecule destroy first",
                )

            print(f"Starting {platform['name']} from {platform['lima_template']}")
            created.append(instance)
            start_lima(platform, instance)
            record = instance_record(platform, ssh_connection(instance))
            records.append(record)
            write_instance_config(instance_config, records)
            print(f"Ready: {platform['name']}")
    except (Exception, KeyboardInterrupt) as error:
        try:
            cleanup_created(created)
        except RuntimeError as cleanup_error:
            write_instance_config(instance_config, records)
            raise RuntimeError(
                f"Creation failed: {error}; cleanup failed: {cleanup_error}",
            ) from error
        instance_config.unlink(missing_ok=True)
        raise


def destroy_instances() -> None:
    _, instance_config, platforms, scenario = molecule_context()
    available = existing_instances()
    failures: list[str] = []
    for platform in reversed(platforms):
        instance = instance_name(scenario, platform["name"])
        if instance not in available:
            continue
        try:
            run(["limactl", "delete", "--force", instance], timeout=10 * 60)
            print(f"Destroyed {instance}")
        except (OSError, RuntimeError) as error:
            failures.append(f"{instance}: {error}")

    if failures:
        raise RuntimeError("; ".join(failures))
    instance_config.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("create", "destroy"))
    args = parser.parse_args()
    try:
        if args.action == "create":
            create_instances()
        else:
            destroy_instances()
    except (KeyError, OSError, RuntimeError, TimeoutError, ValueError, yaml.YAMLError) as error:
        print(f"Lima Molecule {args.action} failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
