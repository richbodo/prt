# sqlcipher3 Documentation Bug Report: Cross-Platform Support Gap

## Issue Summary

sqlcipher3 lacks comprehensive documentation for cross-platform installation, particularly for macOS ARM64 (Apple Silicon). While the package works, the installation process requires undocumented workarounds that are not mentioned in any official documentation.

## Background

The broader issue is that **there are no cross-platform encrypted SQLite drivers with reliable installation support**. This affects the entire ecosystem of privacy-focused applications that need encrypted databases.

### Current State of Encrypted SQLite Drivers

1. **sqlcipher3**: Works but requires undocumented workarounds on macOS ARM64
2. **pysqlcipher3**: Same compilation issues, inactive maintenance (last release 2021)
3. **sqlcipher3-binary**: Linux-only, no macOS support
4. **SQLAlchemy + pysqlcipher3**: Known compatibility issues with `create_function` signature mismatch

## Documentation Gaps

### Missing Installation Instructions

The sqlcipher3 project lacks documentation for:

1. **macOS ARM64 installation** - No mention of the symlink workaround
2. **Cross-platform compatibility matrix** - Which platforms are supported
3. **Troubleshooting guide** - Common installation issues and solutions
4. **Alternative installation methods** - When compilation fails

### Current Documentation Issues

- **README.md**: No platform-specific installation instructions
- **No troubleshooting section**: Users must discover workarounds independently
- **No compatibility matrix**: Unclear which Python versions/platforms are supported
- **No alternative approaches**: When compilation fails, users have no guidance

## Impact

This documentation gap affects:

1. **Privacy-focused applications** that need encrypted databases
2. **macOS ARM64 users** (growing user base)
3. **Cross-platform projects** that need reliable installation
4. **Open source projects** that depend on encrypted SQLite

## Requested Documentation Improvements

### 1. Platform-Specific Installation Guides

Add documentation for each supported platform:

```markdown
## Installation by Platform

### Linux
```bash
pip install sqlcipher3-binary  # Pre-compiled wheels available
```

### macOS Intel
```bash
brew install sqlcipher
pip install sqlcipher3
```

### macOS ARM64 (Apple Silicon)
```bash
brew install sqlcipher
# Create symlinks for compiler compatibility
sudo mkdir -p /usr/local/lib /usr/local/include
sudo ln -s /opt/homebrew/lib/libsqlcipher.a /usr/local/lib/libsqlcipher.a
sudo ln -s /opt/homebrew/include/sqlcipher /usr/local/include/sqlcipher
pip install sqlcipher3
```

### Windows
```bash
# Installation instructions for Windows
```
```

### 2. Troubleshooting Section

```markdown
## Troubleshooting

### "sqlcipher/sqlite3.h file not found" Error

**Platform**: macOS ARM64
**Solution**: Create symlinks as shown in macOS ARM64 installation guide

### Compilation Fails on macOS

**Cause**: Header path issues with Homebrew installation
**Solution**: Use the symlink workaround or try sqlcipher3-binary (Linux only)

### Import Error After Installation

**Cause**: Build succeeded but module not properly linked
**Solution**: Verify SQLCipher installation and try symlink workaround
```

### 3. Compatibility Matrix

```markdown
## Compatibility Matrix

| Platform | Python 3.8 | Python 3.9 | Python 3.10 | Python 3.11 | Python 3.12 | Python 3.13 |
|----------|------------|------------|-------------|-------------|-------------|-------------|
| Linux    | ✅         | ✅         | ✅          | ✅          | ✅          | ✅          |
| macOS Intel | ✅      | ✅         | ✅          | ✅          | ✅          | ✅          |
| macOS ARM64 | ⚠️      | ⚠️         | ⚠️          | ⚠️          | ⚠️          | ⚠️          |
| Windows  | ❓         | ❓         | ❓          | ❓          | ❓          | ❓          |

⚠️ = Requires workaround, ❓ = Unknown/Untested
```

### 4. Alternative Solutions Section

```markdown
## Alternative Solutions

If sqlcipher3 installation fails, consider:

1. **sqlcipher3-binary**: Pre-compiled wheels (Linux only)
2. **File-level encryption**: Use regular SQLite with application-level encryption
3. **Different ORM**: Peewee + sqlcipher3 (same maintainer, better compatibility)
4. **Different approach**: Use cryptography library for file encryption
```

## Broader Ecosystem Issue

The real problem is that **no encrypted SQLite driver provides reliable cross-platform support**:

- **sqlcipher3**: Works but requires undocumented workarounds
- **pysqlcipher3**: Inactive maintenance, same compilation issues
- **sqlcipher3-binary**: Linux-only
- **SQLAlchemy integration**: Known compatibility issues

This forces developers to choose between:
1. Fighting with compilation issues
2. Using platform-specific solutions
3. Implementing custom encryption
4. Abandoning encryption entirely

## Requested Actions

1. **Add comprehensive installation documentation** for all platforms
2. **Document the symlink workaround** for macOS ARM64
3. **Create a troubleshooting guide** for common issues
4. **Add a compatibility matrix** showing supported platforms
5. **Consider adding macOS ARM64 wheels** to avoid compilation issues
6. **Update README.md** with platform-specific instructions

## Reproduction Steps

1. Install macOS on Apple Silicon Mac
2. Install Homebrew and SQLCipher
3. Try to install sqlcipher3: `pip install sqlcipher3`
4. Observe compilation failure
5. Search for documentation on how to fix it
6. Find no official guidance
7. Discover symlink workaround through community issues

## Contact Information

- **Reporter**: [Your Name]
- **Project**: Personal Relationship Tool (PRT)
- **Impact**: Cannot use encrypted databases on macOS ARM64 without undocumented workarounds

---

**Note**: This documentation gap is preventing adoption of encrypted SQLite databases on macOS ARM64 systems, which is a significant limitation for privacy-focused applications. The symlink workaround works but should be documented officially.
