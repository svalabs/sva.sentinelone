# SentinelOne Ansible Collection – Testing Guide

This document explains how to set up and run the [Molecule](https://ansible.readthedocs.io/projects/molecule/) tests for this Ansible collection.

***

## Prerequisites

- Python 3.9+
- [`uv`](https://github.com/astral-sh/uv) (Python package manager)
- [Vagrant](https://www.vagrantup.com/) and [VirtualBox](https://www.virtualbox.org/)
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
| `default` | Tests install_agent against against the current Ubuntu and Fedora release aswell as every module|
| `multi-os` | Same but with all current versions of Ubuntu, Debian, Fedora, Rocky Linux, and SUSE |
| `windows` | Same but tests against Windows systems (check `molecule.yml` and re-enable the relevant code if needed) |
| `no-api-access` | Tests the parts of the `install_agent` role that work without API access — a custom download URL and a registration token are provided manually |


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
molecule login       # SSH/shell into a running instance
```

***

## Architecture Selection (ARM64 / AMD64)

Molecule uses [Vagrant](https://www.vagrantup.com/) with [VirtualBox](https://www.virtualbox.org/) as the driver. By default, AMD64 Vagrant boxes are used.

If you are running tests on an ARM-based machine (e.g., an Apple Silicon Mac), set the `ARCH` environment variable to `ARM64` so that the appropriate Vagrant boxes are selected:

```bash
# Default (AMD64 — standard x86_64 machines)
molecule test

# ARM64 (e.g., Apple Silicon Mac)
ARCH=ARM64 molecule test

# Works with any scenario
ARCH=ARM64 molecule test -s multi-os
```

| Value | Description |
|---|---|
| `AMD64` | x86_64 Vagrant boxes *(default)* |
| `ARM64` | ARM64 Vagrant boxes — use this on Apple Silicon or other ARM hosts |

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

### Using VirtualBox with AMD64 VMs on Apple Silicon

VirtualBox on Apple Silicon supports running **x86_64 (AMD64) virtual machines** via software emulation as of VirtualBox 7.1+. This allows you to use the same AMD64 Vagrant boxes as on standard Intel/AMD machines, at the cost of significantly reduced performance due to emulation.

Before x86_64 VMs can be started, you must explicitly enable AMD64 emulation once via the `VBoxManage` CLI:

```bash
VBoxManage setextradata global "VBoxInternal2/EnableX86OnArm" 1
```

This sets a global VirtualBox flag persistently. After enabling it, proceed normally with `ARCH=AMD64` (or omit the variable):

```bash
# Run with AMD64 boxes on Apple Silicon (after enabling x86 emulation above)
ARCH=AMD64 molecule test
```

> **Note:** x86_64 emulation on Apple Silicon is **not officially supported** by Oracle and is considered experimental. Expect significantly lower performance compared to native ARM64 VMs. For best results, prefer `ARCH=ARM64` with native ARM64 Vagrant boxes whenever possible.

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

# 3a. Run default scenario (AMD64)
molecule test --report --command-borders

# 3b. Run default scenario (ARM64, e.g. Apple Silicon Mac)
ARCH=ARM64 molecule test --report --command-borders

# 3c. Run all necessary scenarios (AMD64)
molecule test --all -e default --report --command-borders

# 3d. Run tests (AMD64 emulated on Apple Silicon — enable x86 emulation first)
VBoxManage setextradata global "VBoxInternal2/EnableX86OnArm" 1
ARCH=AMD64 molecule test --report --command-borders
```