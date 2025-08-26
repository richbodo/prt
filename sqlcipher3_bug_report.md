# sqlcipher3 Compilation Bug Report

## Issue Summary

sqlcipher3 fails to compile on macOS ARM64 (Apple Silicon) due to header file path issues. The package is hardcoded to look for `sqlcipher/sqlite3.h` but cannot find the headers even when SQLCipher is properly installed via Homebrew.

## Environment Details

### System Information
- **OS**: macOS 15.6 (Sequoia)
- **Architecture**: ARM64 (Apple Silicon)
- **Python Version**: 3.13.1
- **Platform**: macOS-15.6-arm64-arm-64bit-Mach-O

### Package Versions
- **sqlcipher3**: 0.5.4 (latest)
- **SQLCipher**: 4.6.1 (installed via Homebrew)
- **pip**: 24.3.1
- **setuptools**: Latest

### Installation Method
```bash
# SQLCipher installation
brew install sqlcipher

# sqlcipher3 installation attempt
pip install sqlcipher3
```

## Error Details

### Compilation Error
```
clang -Qunused-arguments -DMODULE_NAME=\"sqlcipher3.dbapi2\" -DSQLITE_HAS_CODEC=1 -I/usr/include -I/Users/richardbodo/src/prt/prt_env/include -I/opt/homebrew/opt/python@3.13/Frameworks/Python.framework/Versions/3.13/include/python3.13 -c src/blob.c -o build/temp.macosx-14.0-arm64-cpython-313/src/blob.o

In file included from src/blob.c:1:
src/blob.h:4:10: fatal error: 'sqlcipher/sqlite3.h' file not found
    4 | #include "sqlcipher/sqlite3.h"
      |          ^~~~~~~~~~~~~~~~~~~~~
1 error generated.
error: command '/usr/bin/clang' failed with exit code 1
```

### SQLCipher Installation Verification
```bash
# SQLCipher is properly installed
$ brew list | grep sqlcipher
sqlcipher

# Headers exist in the expected location
$ ls -la /opt/homebrew/opt/sqlcipher/include/sqlcipher/
total 1344
drwxr-xr-x@ 4 richardbodo  admin     128 Aug 14  2024 .
drwxr-xr-x@ 3 richardbodo  admin      96 Aug 14  2024 ..
-rw-r--r--@ 1 richardbodo  admin  646009 Aug 14  2024 sqlite3.h
-rw-r--r--@ 1 richardbodo  admin   38149 Aug 14  2024 sqlite3ext.h
```

## Attempted Solutions

### 1. Environment Variables
```bash
export CFLAGS="-I/opt/homebrew/opt/sqlcipher/include"
export LDFLAGS="-L/opt/homebrew/opt/sqlcipher/lib"
pip install sqlcipher3
```
**Result**: Same error - headers not found

### 2. Direct Include Path
```bash
export CFLAGS="-I/opt/homebrew/opt/sqlcipher/include/sqlcipher"
export LDFLAGS="-L/opt/homebrew/opt/sqlcipher/lib"
pip install sqlcipher3
```
**Result**: Same error - headers not found

### 3. pkg-config Approach
```bash
export CFLAGS="$(pkg-config --cflags sqlcipher)"
export LDFLAGS="$(pkg-config --libs sqlcipher)"
pip install sqlcipher3
```
**Result**: pkg-config not available for sqlcipher on macOS

## Root Cause Analysis

The issue appears to be that:

1. **sqlcipher3 expects headers at**: `sqlcipher/sqlite3.h`
2. **SQLCipher installs headers at**: `/opt/homebrew/opt/sqlcipher/include/sqlcipher/sqlite3.h`
3. **Compiler cannot find headers** even with correct include paths

This suggests the sqlcipher3 build system is not properly handling the include paths on macOS ARM64.

## Impact

This bug prevents sqlcipher3 from being used on macOS ARM64 systems, which is a significant limitation given the growing adoption of Apple Silicon Macs.

## Requested Fix

1. **Update build system** to properly detect SQLCipher installation on macOS ARM64
2. **Add proper include path handling** for Homebrew installations
3. **Consider adding macOS ARM64 wheels** to avoid compilation issues
4. **Update documentation** with macOS ARM64-specific installation instructions

## Additional Context

- sqlcipher3-binary package is not available for macOS (Linux only)
- pysqlcipher3 has the same compilation issues
- This affects the broader ecosystem of encrypted SQLite applications on macOS ARM64

## Reproduction Steps

1. Install macOS on Apple Silicon Mac
2. Install Homebrew
3. Install SQLCipher: `brew install sqlcipher`
4. Create Python virtual environment
5. Attempt to install sqlcipher3: `pip install sqlcipher3`
6. Observe compilation failure

## Contact Information

- **Reporter**: [Your Name]
- **Project**: Personal Relationship Tool (PRT)
- **GitHub Issue**: [Link to your issue if you create one]

---

**Note**: This bug report is being submitted because sqlcipher3 compilation issues are preventing adoption of encrypted SQLite databases on macOS ARM64 systems, which is a significant platform limitation for privacy-focused applications.
