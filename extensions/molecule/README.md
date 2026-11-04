# SentinelOne Ansible Collection – Testing Guide

This document explains how to set up and run the [Molecule](https://ansible.readthedocs.io/projects/molecule/) tests for this Ansible collection.

***

## Prerequisites

- Python 3.11+
- [`uv`](https://github.com/astral-sh/uv) (Python package manager)
- [Lima](https://lima-vm.io/) 2.2 or newer
- [Vagrant](https://www.vagrantup.com/) and [VirtualBox](https://www.virtualbox.org/) for the Windows scenario
- [`direnv`](https://direnv.net/) *(optional but recommended)*

***

## Repository Structure (Testing-Relevant Files)

```
.
├── .envrc                  # Automatic environment setup via direnv
├── ansible.env             # Ansible-specific environment variables
├── pyproject.toml          # Python dependencies (managed via uv)
└── extensions/
    └── molecule/
        ├── <szenario>/       # Molecule scenarios e.g. 'default'
        └──vars/
            ├── test_vars.yml.dist  # Template for test variables
            └── test_vars.yml       # Your local test variables (gitignored)
```

***

## Step 1 – Prepare Test Variables

Before running any tests, you must provide the required SentinelOne-specific variables (e.g., API tokens, site IDs, endpoints).

Copy the distribution template and fill in the values:

```bash
cp extensions/molecule/vars/test_vars.yml.dist extensions/molecule/vars/test_vars.yml
```

Then open `extensions/molecule/vars/test_vars.yml` in your editor and fill in all required values:

```bash
# Example:
vim extensions/molecule/vars/test_vars.yml
```

> **Note:** `extensions/molecule/vars/test_vars.yml` is gitignored and must never be committed to the repository, as it may contain sensitive credentials.

***

## Step 2 – Set Up the Python Environment

Dependencies are managed via [`uv`](https://github.com/astral-sh/uv) and declared in `pyproject.toml`. This includes Ansible, Molecule, and all required test dependencies.

### Option A – Automatic Setup with direnv (Recommended)

If you have [`direnv`](https://direnv.net/) installed, the environment is set up automatically when you `cd` into the project root:

```bash
cd <project-root>
direnv allow   # Only required once
```

The `.envrc` file executes the following steps automatically:

```bash
uv sync --all-extras && source .venv/bin/activate
source ansible.env
```

This installs all dependencies (including extras) into a local virtual environment and loads the necessary Ansible environment variables.

### Option B – Manual Setup

If you prefer not to use direnv, run the commands from `.envrc` manually:

```bash
# Install all dependencies into a local virtual environment
uv sync --all-extras

# Activate the virtual environment
source .venv/bin/activate

# Load Ansible environment variables
source ansible.env
```

***

## Step 3 – Run Molecule Tests

Once the environment is active, you can run Molecule tests from the repository root.

### Available Scenarios

| Scenario | Description |
|---|---|
| `default` | Tests install_agent against current Ubuntu and Fedora releases, as well as every module |
| `multi-os` | Same tests across current Ubuntu, Debian, Fedora, Rocky Linux, and SUSE releases |
| `windows` | Runs the Windows tests using the existing Vagrant/VirtualBox setup |
| `no-api-access` | Tests the parts of the `install_agent` role that work without API access — a custom download URL and a registration token are provided manually |

The Linux scenarios create and destroy their Lima instances using native Ansible tasks in local playbooks. Those tasks write the connection details Molecule needs to its instance configuration. The Windows scenario remains on the existing Vagrant/VirtualBox setup for now; it is deliberately excluded from the Lima-backed Linux scenarios.

### Run the Default Scenario

```bash
molecule test --report --command-borders
```

### Run a Specific Scenario

```bash
molecule test -s <scenario_name> --report --command-borders

# Examples:
molecule test -s multi-os --report --command-borders
molecule test -s no-api-access --report --command-borders
molecule test -s windows --report --command-borders
```

### Cover all necessary tests
```bash
molecule test --all -e default --report --command-borders
```
You don't need to run default scenario when you run multi-os. Default scenario is included in multi-os scenario.

### Run Individual Molecule Steps

For development and debugging, you can run individual lifecycle steps instead of the full `test` sequence:

```bash
molecule create      # Provision test instances
molecule converge    # Apply the role
molecule verify      # Run assertions/tests
molecule destroy     # Tear down instances
molecule login       # SSH into a running Linux instance
```

***

## Guest Architecture

Lima uses the host architecture by default, so Apple Silicon hosts run Linux guests natively. The `rocky-8` test explicitly requests `x86_64` to preserve its existing platform coverage; this guest is emulated on ARM hosts and may be slow. The Windows scenario keeps using its existing ARM64 Vagrant box.

```bash
# Lima selects the native host architecture
molecule test

# Windows scenario (requires Vagrant and VirtualBox)
molecule test -s windows
```

***

## macOS-Specific Notes

### Fork Safety on macOS

When running Molecule on macOS, Ansible may crash with an error related to Objective-C runtime fork safety, such as:

```
objc[...]: +[NSCFString initialize] may have been in progress in another thread when fork() was called.
```

This is a known macOS restriction. To work around it, export the following environment variable before running Molecule:

```bash
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
```

This **is covered** if you use the ansible.env file in this repository as described in the chapter **Set Up the Python Environment**. Alternatively you can add this to your shell profile (e.g. `~/.zshrc`) to avoid setting it manually every time.

***

### Windows guest access

The Windows scenario continues to use Vagrant and VirtualBox. To open a shell for troubleshooting, use Molecule's login command:

```bash
molecule login -s windows
```

***

## Quick Start Summary

```bash
# 1. Copy and fill in test variables
cp extensions/molecule/vars/test_vars.yml.dist extensions/molecule/vars/test_vars.yml
vim extensions/molecule/vars/test_vars.yml

# 2a. Set up environment (with direnv)
direnv allow

# 2b. Set up environment (without direnv)
uv sync --all-extras && source .venv/bin/activate && source ansible.env

# 3a. Run default scenario (native Lima architecture)
molecule test --report --command-borders

# 3b. Run all necessary scenarios
molecule test --all -e default --report --command-borders

# 3c. Run the Windows scenario (requires Vagrant and VirtualBox)
molecule test -s windows --report --command-borders
```