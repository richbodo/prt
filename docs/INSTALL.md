# PRT Installation Guide

This document provides installation instructions for macOS and Linux. Windows is currently not supported.

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

#### 3. Install SQLCipher
```bash
brew install sqlcipher
```

#### 4. Clone PRT Repository
```bash
git clone https://github.com/richbodo/prt.git
cd prt
```

#### 5. Create Virtual Environment
```bash
source ./init.sh
```

#### 6. Install pysqlcipher3
```bash
# Get SQLCipher installation path
SQLCIPHER_PATH=$(brew --prefix sqlcipher)

# Set environment variables for compilation
export CFLAGS="-I$SQLCIPHER_PATH/include"
export LDFLAGS="-L$SQLCIPHER_PATH/lib"

# Install pysqlcipher3
pip install pysqlcipher3
```

#### 7. Set Up Database
```bash
python -m prt_src.cli setup
```

## Linux Installation

Tested on Ubuntu 22.04+. Other Debian-based distributions should work with minor changes.

### Step-by-Step Installation

1. **Update system and install dependencies**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3 python3-venv python3-dev build-essential git libsqlcipher-dev pkg-config
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

4. **Install Python dependencies**
   ```bash
   python -m pip install -r requirements.txt
   ```

5. **Install pysqlcipher3 linked against SQLCipher**
   ```bash
   export CFLAGS="$(pkg-config --cflags sqlcipher)"
   export LDFLAGS="$(pkg-config --libs sqlcipher)"
   python -m pip install pysqlcipher3
   ```

6. **Initialize PRT**
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
