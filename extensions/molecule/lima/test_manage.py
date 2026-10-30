from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from extensions.molecule.lima import manage


class LimaManagerTests(unittest.TestCase):
    def test_instance_name_is_scenario_scoped(self) -> None:
        self.assertEqual(
            manage.instance_name("multi-os", "ubuntu-2404"),
            "molecule-multi-os-ubuntu-2404",
        )

    def test_linux_start_uses_template_resources_and_architecture(self) -> None:
        with patch.object(manage, "run") as run:
            manage.start_lima(
                {
                    "lima_template": "rocky-8",
                    "arch": "x86_64",
                    "memory": 2,
                    "cpus": 2,
                },
                "molecule-no-api-rocky-8",
            )

        command = run.call_args.args[0]
        self.assertIn("template:rocky-8", command)
        self.assertIn("--arch", command)
        self.assertIn("x86_64", command)
        self.assertEqual(command[command.index("--cpus") + 1], "2")
        self.assertEqual(command[command.index("--memory") + 1], "2")
        self.assertEqual(command[command.index("--disk") + 1], "20")
        self.assertEqual(run.call_args.kwargs["timeout"], manage.INSTANCE_START_TIMEOUT)

    def test_instance_record_uses_lima_ssh_connection(self) -> None:
        record = manage.instance_record(
            {"name": "ubuntu-2404"},
            {
                "hostname": "127.0.0.1",
                "port": "60022",
                "user": "lima",
                "identityfile": "/tmp/lima-key",
            },
        )
        self.assertEqual(record["instance"], "ubuntu-2404")
        self.assertEqual(record["connection"], "ssh")
        self.assertEqual(record["port"], 60022)
        self.assertEqual(record["user"], "lima")

    def test_instance_config_is_private(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "instance_config.yml"
            manage.write_instance_config(config, [{"instance": "linux"}])
            self.assertEqual(config.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
