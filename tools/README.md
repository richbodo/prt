# PRT Tools

This directory contains standalone tools that work with PRT exports and data.

## Available Tools

### make_directory.py

**Purpose**: Generate interactive single-page websites from PRT JSON exports showing contact relationships as navigable 2D graphs.

**Usage**:
```bash
# Basic usage
python tools/make_directory.py generate exports/contacts_search_20250826_191055/

# Custom output directory  
python tools/make_directory.py generate exports/tags_search_20250826_191055/ --output ./my_directory

# Force overwrite existing directory
python tools/make_directory.py generate exports/contacts_search_20250826_191055/ --force

# Get help
python tools/make_directory.py --help
python tools/make_directory.py generate --help
```

**Features**:
- ✅ **Phase 1**: Basic HTML generation with contact cards
- ✅ **Phase 2**: D3.js interactive graph visualization with mobile support
- 🔄 **Phase 3 (Future)**: Contact detail modals and export integration

**Input**: PRT JSON export directories (from search exports)
**Output**: Self-contained HTML websites in `directories/` folder

**Requirements**: 
- Python 3.8+
- Dependencies: `typer`, `rich`, `jinja2`, `pillow`

## Tool Development Guidelines

When adding new tools to this directory:

1. **Standalone Design**: Tools should work independently of the main PRT application
2. **PRT Export Compatible**: Should work with standard PRT JSON export format
3. **Professional CLI**: Use `typer` for consistent command-line interface
4. **Rich Output**: Use `rich` for beautiful console output
5. **Self-Documenting**: Include `--help` and clear error messages
6. **Testing**: Add tests to validate functionality

## Integration with PRT

Tools in this directory are designed to work with PRT export data but remain independent. This allows:
- **Standalone distribution**: Tools can be shared without the full PRT application
- **Flexible development**: Different tools can use different technology stacks
- **User choice**: Users can pick and choose which tools they need

---

For questions about specific tools, use their individual `--help` commands or see the main PRT documentation.
