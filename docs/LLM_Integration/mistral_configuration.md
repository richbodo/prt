# Mistral-7B-Instruct-v0.3 Tool Calling Configuration

## Overview

PRT officially supports the Mistral-7B-Instruct-v0.3 model (available as `mistral:7b-instruct` in Ollama) with full tool calling capabilities. This model provides an efficient alternative to the larger GPT-OSS-20B model for systems with limited hardware resources.

## Model Specifications

- **Model Name**: `mistral:7b-instruct` (Ollama)
- **Version**: Mistral-7B-Instruct-v0.3
- **Parameter Count**: 7 billion parameters
- **Model Size**: 4.4GB (Q4_K_M quantization)
- **Context Window**: 32,768 tokens
- **Provider**: Ollama
- **Tool Calling Support**: ✅ Yes (with v3 tokenizer)

## Hardware Requirements

### Minimum Requirements
- **RAM**: 8GB system RAM
- **VRAM**: 4GB (if using GPU acceleration)
- **Storage**: ~5GB free space for model

### Recommended Configuration
- **RAM**: 16GB system RAM for optimal performance
- **VRAM**: 4GB+ for GPU acceleration (optional)
- **CPU**: Multi-core processor for inference without GPU

## Installation and Setup

### 1. Install Ollama (if not already installed)
```bash
# macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

### 2. Download Mistral Model
```bash
# Download the model (will download ~4.4GB)
ollama pull mistral:7b-instruct

# Verify the model is available
ollama list
```

### 3. Verify Tool Calling Support
```bash
# Check model capabilities
ollama show mistral:7b-instruct

# Should show "tools" in the capabilities list
```

### 4. Configure PRT to Use Mistral
```bash
# Test the model with PRT
python -m prt_src --model mistral:7b-instruct

# Or set as default in prt_config.json:
{
  "llm": {
    "model": "mistral:7b-instruct"
  }
}
```

## Tool Calling Optimizations

PRT automatically applies the following optimizations when using Mistral models:

### Temperature Control
- **Default Temperature**: Automatically limited to 0.3 (max)
- **Reasoning**: Lower temperatures improve tool calling reliability
- **Configuration**: Can be set lower (0.1-0.3) but not higher for optimal results

### Tool Call ID Format
- **Format**: 9 alphanumeric characters (e.g., "abc123def")
- **Compliance**: Meets Mistral-v0.3 specifications
- **Generation**: Automatic using secure random generation

### Request Configuration
```json
{
  "model": "mistral:7b-instruct",
  "options": {
    "temperature": 0.3
  }
}
```

## Usage Examples

### Basic Tool Calling
```bash
# Launch TUI with Mistral
python -m prt_src --model mistral:7b-instruct

# In the chat interface:
> "Show me the first few contacts in the db"
> "Find all contacts tagged as 'family'"
> "Create a backup of my database"
```

### CLI Integration
```bash
# Direct chat with Mistral
python -m prt_src.cli chat --model mistral:7b-instruct

# Debug mode with Mistral and fixture data
python -m prt_src --debug --model mistral:7b-instruct
```

## Supported Tools

The following tools are fully supported with Mistral-7B-Instruct-v0.3:

### Read-Only Operations
- `search_contacts` - Search for contacts
- `list_all_contacts` - Get all contacts
- `get_contact_details` - Get detailed contact information
- `list_all_tags` - Get all tags
- `search_tags` - Search for tags
- `list_all_notes` - Get all notes
- `search_notes` - Search for notes
- `get_database_stats` - Database statistics
- `get_database_schema` - Schema information

### Data Modification (with automatic backups)
- `add_tag_to_contact` - Tag a contact
- `remove_tag_from_contact` - Remove tag from contact
- `create_tag` - Create new tag
- `delete_tag` - Delete tag
- `add_note_to_contact` - Add note to contact
- `create_note` - Create new note
- `update_note` - Update existing note
- `delete_note` - Delete note

### Advanced Operations
- `execute_sql` - Run SQL queries (with confirmation)
- `generate_directory` - Create contact visualizations
- `create_backup_with_comment` - Manual backups

## Performance Characteristics

### Response Times (Typical)
- **Simple queries**: 2-5 seconds
- **Tool calling**: 3-8 seconds
- **Complex tool chains**: 8-15 seconds

### Memory Usage
- **Base model**: ~4.4GB VRAM/RAM
- **During inference**: +1-2GB temporary usage
- **Recommended headroom**: 8GB+ total system RAM

## Troubleshooting

### Common Issues

#### Tool Calls Return JSON Artifacts Instead of Executing
**Problem**: Model returns code examples instead of executing tools
**Solution**: Ensure you're using the latest PRT version with Mistral optimizations

#### High Response Times
**Problem**: Tool calling takes longer than expected
**Solutions**:
- Ensure adequate RAM (16GB+ recommended)
- Use GPU acceleration if available
- Check Ollama is running locally (not remotely)

#### Temperature Too High Warning
**Problem**: Tool calling unreliable with high temperature
**Solution**: PRT automatically limits temperature to 0.3 for Mistral models

### Verification Commands

```bash
# Verify model is available
ollama list | grep mistral

# Check model details and capabilities
ollama show mistral:7b-instruct

# Test PRT integration
python -c "
from prt_src.llm_factory import create_llm
llm = create_llm(model='mistral:7b-instruct')
print('✅ Mistral model loaded successfully')
print(f'Temperature: {llm.temperature}')
print(f'Is Mistral: {llm._is_mistral_model()}')
"

# Test basic tool calling
python -c "
from prt_src.llm_factory import create_llm
llm = create_llm(model='mistral:7b-instruct')
response = llm.chat('How many contacts do I have?')
print('Response:', response)
"
```

## Comparison with Other Models

| Feature | Mistral 7B | GPT-OSS 20B | Llama3 8B |
|---------|------------|-------------|-----------|
| Tool Calling | ✅ Full | ✅ Full | ⚠️ Limited |
| Model Size | 4.4GB | ~12GB | ~4.3GB |
| Min RAM | 8GB | 16GB | 8GB |
| Context Size | 32,768 | 4,096 | 8,192 |
| Speed | Fast | Slower | Fast |
| Quality | Good | Excellent | Good |

## Advanced Configuration

### Custom Temperature Settings
```json
{
  "llm": {
    "model": "mistral:7b-instruct",
    "temperature": 0.1  // Even lower for maximum reliability
  }
}
```

### Performance Tuning
```json
{
  "llm": {
    "model": "mistral:7b-instruct",
    "timeout": 45,       // Increase timeout for complex operations
    "keep_alive": "10m"  // Keep model loaded longer
  }
}
```

### GPU Acceleration (if available)
Mistral will automatically use GPU acceleration if:
1. NVIDIA GPU with CUDA support
2. Adequate VRAM (4GB+)
3. Ollama configured for GPU

## Best Practices

1. **Use for moderate hardware**: Ideal when 16GB+ RAM but <32GB
2. **Tool calling focused**: Best for database operations and structured tasks
3. **Backup before modifications**: All write operations create automatic backups
4. **Monitor performance**: Watch for memory pressure on 8GB systems
5. **Update regularly**: Keep Ollama and PRT updated for latest optimizations

## Support and Updates

- **PRT Version**: Requires PRT v1.0+ for full Mistral support
- **Ollama Version**: Compatible with Ollama 0.1.0+
- **Model Updates**: `ollama pull mistral:7b-instruct` updates to latest version
- **Issues**: Report tool calling issues via GitHub Issues with model info

## Example Session

```
$ python -m prt_src --model mistral:7b-instruct

[LLM] Applied Mistral optimization: temperature=0.3 (tool calling optimized)
[LLM] Initialized OllamaLLM: model=mistral:7b-instruct

> Show me my family contacts

I'll search for contacts tagged as 'family' in your database.

[Tool: search_contacts with query="family"]
Found 3 family contacts:
- John Doe (john.doe@email.com)
- Jane Smith (jane.smith@email.com)
- Alice Johnson (alice.johnson@email.com)

> Create a backup before I make changes

I'll create a manual backup of your database.

[Tool: create_backup_with_comment with comment="Manual backup before changes"]
✅ Backup #15 created successfully with comment: "Manual backup before changes"
Your database is now safely backed up.
```