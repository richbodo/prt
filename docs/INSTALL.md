# PRT Installation Guide

This document provides installation instructions for macOS and Linux. Windows is currently not supported.

> **Status:** Historical. The project now prefers the lighter-weight workflow documented in [docs/DEV_SETUP.md](./DEV_SETUP.md). Keep this guide for reference if you need to reproduce the old SQLCipher-based environment.

## Table of Contents

- [Prerequisites](#prerequisites)
- [macOS Installation](#macos-installation)
- [Linux Installation](#linux-installation)
- [Troubleshooting](#troubleshooting)
- [Verification](#verification)

## Prerequisites

Before installing PRT, ensure you have:

- **Python 3.8 or higher**
- **Git** (for cloning the repository)

## macOS Installation

### System Requirements
- macOS 10.15 (Catalina) or later
- Homebrew package manager
- Xcode Command Line Tools (for compiling)

### Step-by-Step Installation

#### 1. Install Homebrew
If you don't have Homebrew installed:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. Install Xcode Command Line Tools
```bash
xcode-select --install
```

#### 3. Clone PRT Repository
```bash
git clone https://github.com/richbodo/prt.git
cd prt
```

#### 4. Create Virtual Environment
```bash
source ./init.sh
```

#### 5. Set Up Database
```bash
python -m prt_src.cli setup
```

## Linux Installation

Tested on Ubuntu 22.04+. Other Debian-based distributions should work with minor changes.

### Step-by-Step Installation

1. **Update system and install dependencies**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3 python3-venv python3-dev build-essential git pkg-config
   ```

2. **Clone PRT repository**
   ```bash
   git clone https://github.com/richbodo/prt.git
   cd prt
   ```

3. **Create and activate a virtual environment**
   ```bash
   python3 -m venv prt_env
   source prt_env/bin/activate
   ```

4. **Initialize PRT**
   ```bash
   python -m prt_src.cli setup
   ```

## Troubleshooting

- If `pip` cannot find SQLCipher headers, ensure `libsqlcipher-dev` and `pkg-config` are installed.
- If database setup fails, rerun `python -m prt_src.cli setup --force`.

## Verification

After installation, verify everything is working:

```bash
python -m prt_src.cli --help
python -m prt_src.cli db-status
```
