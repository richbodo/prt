# PRT Installation Guide

This document provides detailed installation instructions for PRT across different platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [macOS Installation](#macos-installation)
- [Linux Installation](#linux-installation)
- [Windows Installation](#windows-installation)
- [Troubleshooting](#troubleshooting)
- [Verification](#verification)

## Prerequisites

Before installing PRT, ensure you have:

- **Python 3.8 or higher**
- **Git** (for cloning the repository)
- **Platform-specific dependencies** (see sections below)

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

### macOS Troubleshooting

#### Common Issues

**Issue**: `command not found: brew`
**Solution**: Install Homebrew first using the command in step 1.

**Issue**: `fatal error: 'sqlcipher/sqlite3.h' file not found`
**Solution**: Ensure SQLCipher is installed and CFLAGS/LDFLAGS are set correctly.

**Issue**: `Permission denied` during pip install
**Solution**: Use the virtual environment created by `init.sh`.

**Issue**: pysqlcipher3 fails to compile
**Solution**: 
```bash
# Check SQLCipher installation
brew list sqlcipher

# Verify paths
echo $CFLAGS
echo $LDFLAGS

# Try reinstalling SQLCipher
brew uninstall sqlcipher
brew install sqlcipher
```

## Linux Installation

### Supported Distributions
- Ubuntu 20.04+
- Debian 11+
- CentOS 8+
- RHEL 8+
- Fedora 34+

### Ubuntu/Debian Installation

#### 1. Update System
```bash
sudo apt-get update
sudo apt-get upgrade
```

#### 2. Install System Dependencies
```bash
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    libsqlcipher-dev \
    build-essential \
    git
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

#### 5. Install pysqlcipher3
```bash
pip install pysqlcipher3
```

#### 6. Set Up Database
```bash
python -m prt_src.cli setup
```

### CentOS/RHEL/Fedora Installation

#### 1. Install System Dependencies
```bash
# For CentOS/RHEL 8+
sudo yum install -y \
    python3 \
    python3-pip \
    python3-devel \
    sqlcipher-devel \
    gcc \
    git

# For Fedora
sudo dnf install -y \
    python3 \
    python3-pip \
    python3-devel \
    sqlcipher-devel \
    gcc \
    git
```

#### 2. Follow Steps 3-6 from Ubuntu/Debian Installation

### Arch Linux Installation

#### 1. Install System Dependencies
```bash
sudo pacman -S \
    python \
    python-pip \
    sqlcipher \
    base-devel \
    git
```

#### 2. Follow Steps 3-6 from Ubuntu/Debian Installation

### Linux Troubleshooting

#### Common Issues

**Issue**: `libsqlcipher-dev not found`
**Solution**: 
```bash
# Ubuntu/Debian
sudo apt-get install sqlcipher-dev

# CentOS/RHEL
sudo yum install sqlcipher-devel

# Fedora
sudo dnf install sqlcipher-devel
```

**Issue**: `Permission denied` during pip install
**Solution**: Use the virtual environment or add `--user` flag:
```bash
pip install --user pysqlcipher3
```

**Issue**: `gcc: command not found`
**Solution**: Install build tools:
```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# CentOS/RHEL
sudo yum groupinstall "Development Tools"

# Fedora
sudo dnf groupinstall "Development Tools"
```

## Windows Installation

### Status: TBD (To Be Determined)

Windows support is planned but not yet implemented. The encrypted database functionality requires additional work for Windows compatibility.

### Planned Requirements
- Windows 10/11 (64-bit)
- Python 3.8+
- Visual Studio Build Tools 2019 or later
- SQLCipher Windows binaries
- Git for Windows

### Planned Installation Steps
1. Install Python 3.8+ from python.org
2. Install Visual Studio Build Tools
3. Install SQLCipher Windows binaries
4. Clone repository and setup virtual environment
5. Install pysqlcipher3 with Windows-specific configuration
6. Configure database

### Current Limitations
- Encrypted database functionality not tested on Windows
- pysqlcipher3 compilation may require additional configuration
- Some CLI features may need Windows-specific adjustments

## Troubleshooting

### General Issues

#### Python Version Issues
**Problem**: "Python 3.8+ required"
**Solution**: 
```bash
# Check Python version
python3 --version

# Install newer Python if needed
# macOS: brew install python@3.11
# Ubuntu: sudo apt-get install python3.11
```

#### Virtual Environment Issues
**Problem**: "No module named 'prt'"
**Solution**: Ensure you're in the virtual environment:
```bash
# Activate virtual environment
source prt_env/bin/activate  # Linux/macOS
# or
prt_env\Scripts\activate     # Windows (when implemented)
```

#### Permission Issues
**Problem**: "Permission denied" during installation
**Solution**: 
```bash
# Use virtual environment
source ./init.sh

# Or install with user flag
pip install --user pysqlcipher3
```

### Platform-Specific Issues

#### macOS Issues

**Problem**: Homebrew not found
**Solution**: Install Homebrew first, then restart terminal.

**Problem**: Xcode Command Line Tools missing
**Solution**: 
```bash
xcode-select --install
```

#### Linux Issues

**Problem**: Package manager errors
**Solution**: Update package lists and try again:
```bash
# Ubuntu/Debian
sudo apt-get update

# CentOS/RHEL
sudo yum update

# Fedora
sudo dnf update
```

**Problem**: SELinux blocking operations
**Solution**: Temporarily disable SELinux or configure appropriate policies.

## Verification

### Test Installation

After installation, verify everything is working:

#### 1. Check Python Environment
```bash
python --version
pip list | grep pysqlcipher3
```

#### 2. Test Database Setup
```bash
python -m prt_src.cli setup
python -m prt_src.cli db-status
```

#### 3. Test Encryption (Optional)
```bash
# Create test database
python -m prt_src.cli setup --encrypted

# Check encryption status
python -m prt_src.cli db-status
```

#### 4. Run Tests
```bash
# Run all tests
pytest

# Run specific test suites
pytest tests/test_encrypted_db.py
pytest tests/test_migrations.py
```

### Expected Output

Successful installation should show:
- Python 3.8+ version
- pysqlcipher3 in pip list
- Database setup completes without errors
- Tests pass (with some skipped for missing pysqlcipher3)

## Getting Help

If you encounter issues:

1. **Check this guide** for platform-specific solutions
2. **Review the main [README.md](../README.md)** for general troubleshooting
3. **Check the test files** for usage examples
4. **Open an issue** on GitHub with:
   - Your platform and version
   - Python version
   - Complete error message
   - Steps to reproduce

## Contributing to Installation

If you successfully install PRT on a new platform or find solutions to installation issues:

1. **Update this document** with your findings
2. **Test the installation** on a clean system
3. **Submit a pull request** with your improvements
4. **Include troubleshooting steps** for common issues
