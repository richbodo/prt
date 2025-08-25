# Ollama Integration Guide

This guide covers the integration of Ollama with GPT-OSS-20B for local LLM-powered chat functionality in PRT.

## Overview

PRT now supports Ollama integration for local LLM chat with tool calling capabilities. This allows you to interact with your contacts and relationships using natural language, with the LLM able to perform actions through the PRT API.

## Prerequisites

### Installing Ollama

1. **Install Ollama** from [ollama.ai](https://ollama.ai)
2. **Pull the GPT-OSS-20B model**:
   ```bash
   ollama pull gpt-oss:20b
   ```
3. **Start Ollama service**:
   ```bash
   ollama serve
   ```

### System Requirements

- **RAM**: At least 16GB (32GB recommended for optimal performance)
- **Storage**: ~40GB for the model
- **GPU**: Optional but recommended for faster inference

## Usage

### Command Line Interface

#### Interactive Chat Mode

Start an interactive chat session with Ollama:

```bash
# Start interactive PRT (includes Ollama chat)
python -m prt_src.cli

# Then select option 6: Start LLM Chat

# Or start chat mode directly
python -m prt_src.cli chat
```

#### Single Message Mode

Send a single message and get a response:

```bash
# For single message queries, use the interactive mode
python -m prt_src.cli
# Then select option 6: Start LLM Chat
# And ask your question directly

# Or start chat mode directly for quick access
python -m prt_src.cli chat
```

#### Menu-Driven Interface

From the main PRT menu, select option **6. Start LLM Chat** to enter chat mode.

### Available Tools

The LLM can use the following tools to interact with your data:

#### Contact Management
- `search_contacts` - Search for contacts by name, email, or other criteria
- `list_all_contacts` - Get a list of all contacts in the database
- `get_contact_details` - Get detailed information about a specific contact

#### Tag Management
- `search_tags` - Search for tags by name
- `list_all_tags` - Get a list of all tags in the database
- `get_contacts_by_tag` - Get all contacts that have a specific tag
- `add_tag_to_contact` - Add a tag to a contact's relationship
- `create_tag` - Create a new tag

#### Note Management
- `search_notes` - Search for notes by title or content
- `list_all_notes` - Get a list of all notes in the database
- `get_contacts_by_note` - Get all contacts that have a specific note
- `add_note_to_contact` - Add a note to a contact's relationship
- `create_note` - Create a new note

#### Database Information
- `get_database_stats` - Get database statistics including contact and relationship counts

## Example Conversations

### Finding Contacts

```
You: Find all contacts named John
Assistant: I'll search for contacts named John for you.
[Tool: search_contacts with query="John"]
I found 3 contacts named John:
- John Doe (john.doe@email.com)
- John Smith (john.smith@email.com)
- Johnny Wilson (johnny.w@email.com)
```

### Managing Tags

```
You: Create a tag called "VIP" and add it to John Doe
Assistant: I'll help you create the VIP tag and add it to John Doe.
[Tool: create_tag with name="VIP"]
[Tool: search_contacts with query="John Doe"]
[Tool: add_tag_to_contact with contact_id=1, tag_name="VIP"]
I've successfully created the "VIP" tag and added it to John Doe's contact.
```

### Complex Queries

```
You: Show me all contacts who have the "VIP" tag and also have notes about meetings
Assistant: I'll help you find VIP contacts with meeting notes.
[Tool: get_contacts_by_tag with tag_name="VIP"]
[Tool: search_notes with query="meeting"]
[Tool: get_contacts_by_note with note_title="Meeting Notes"]
I found 2 VIP contacts with meeting notes:
- John Doe (VIP tag, has "Meeting Notes" note)
- Jane Smith (VIP tag, has "Follow-up Meeting" note)
```

## Configuration

### Ollama Settings

The Ollama integration uses the following default settings:

- **Base URL**: `http://localhost:11434/v1`
- **Model**: `gpt-oss:20b`
- **Timeout**: 120 seconds

You can modify these settings by editing the `OllamaLLM` class in `prt/llm_ollama.py`.

### Custom Ollama URL

If you're running Ollama on a different host or port, you can modify the base URL:

```python
from prt_src.llm_ollama import OllamaLLM

# Connect to remote Ollama instance
llm = OllamaLLM(api, base_url="http://your-server:11434")
```

## Troubleshooting

### Common Issues

#### "Connection refused" Error

**Problem**: Cannot connect to Ollama service
**Solution**: 
1. Ensure Ollama is running: `ollama serve`
2. Check if the service is accessible: `curl http://localhost:11434/v1/models`
3. Verify the base URL in your configuration

#### "Model not found" Error

**Problem**: GPT-OSS-20B model is not available
**Solution**:
1. Pull the model: `ollama pull gpt-oss:20b`
2. Check available models: `ollama list`
3. Verify model name spelling

#### Slow Response Times

**Problem**: LLM responses are very slow
**Solutions**:
1. **Use GPU acceleration** (if available)
2. **Increase system RAM** (32GB+ recommended)
3. **Use a smaller model** for faster responses
4. **Check system resources** during inference

#### Tool Call Failures

**Problem**: LLM cannot execute tool calls
**Solutions**:
1. **Check database connection** - ensure PRT database is accessible
2. **Verify API permissions** - ensure the LLM has access to PRT API
3. **Check tool definitions** - verify tool parameters match API expectations

### Performance Optimization

#### GPU Acceleration

For better performance, ensure your system can use GPU acceleration:

```bash
# Check if CUDA is available
nvidia-smi

# Install CUDA-enabled PyTorch if needed
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### Memory Management

- **Close other applications** when using Ollama
- **Monitor memory usage** during inference
- **Consider using a smaller model** for development/testing

## Security Considerations

### Local Processing

- **All data stays local** - no data is sent to external services
- **Model runs on your machine** - complete privacy for your conversations
- **No internet required** - works offline once model is downloaded

### API Access

- **Restricted tool access** - LLM can only use PRT API functions
- **No system access** - cannot execute terminal commands or access files
- **Database safety** - cannot modify database configuration or encryption settings

### Best Practices

1. **Keep Ollama updated** - regularly update to latest version
2. **Monitor resource usage** - ensure system stability during inference
3. **Backup your data** - maintain regular backups of your PRT database
4. **Test in development** - verify functionality before production use

## Development

### Adding New Tools

To add new tools for the LLM to use:

1. **Add the function to PRTAPI** in `prt/api.py`
2. **Create a Tool definition** in `prt/llm_ollama.py`
3. **Update the system prompt** to include the new tool
4. **Test the integration** with the new tool

Example:

```python
# In prt/llm_ollama.py
Tool(
    name="new_tool",
    description="Description of what the tool does",
    parameters={
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "Description of parameter"
            }
        },
        "required": ["param1"]
    },
    function=self.api.new_tool_function
)
```

### Customizing the System Prompt

You can modify the system prompt in the `_create_system_prompt()` method to:

- **Add specific instructions** for the LLM
- **Modify behavior guidelines** 
- **Include context about your data**
- **Set response formatting preferences**

### Testing

Run the Ollama integration tests:

```bash
# Run all Ollama tests
pytest tests/test_ollama_integration.py

# Run specific test
pytest tests/test_ollama_integration.py::TestOllamaLLM::test_chat_with_tool_calls
```

## Support

For issues with Ollama integration:

1. **Check Ollama documentation** at [ollama.ai/docs](https://ollama.ai/docs)
2. **Review PRT logs** for error messages
3. **Test Ollama directly** with `ollama run gpt-oss:20b`
4. **Open an issue** on GitHub with detailed error information

## Future Enhancements

Planned improvements for Ollama integration:

- **Model switching** - support for different Ollama models
- **Streaming responses** - real-time response streaming
- **Custom tool definitions** - user-defined tools
- **Conversation export** - save and load chat sessions
- **Performance monitoring** - track response times and resource usage
