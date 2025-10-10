# Ollama Integration for Chat Screen

This guide covers integrating Ollama with PRT's Chat screen for local LLM-powered natural language database queries.

## Overview

PRT's Chat screen uses Ollama to run a local LLM that translates natural language queries into structured database operations. Unlike cloud-based AI services, all processing happens locally on your machine for complete privacy.

**Architecture**: The LLM acts as a **translator**, not a renderer:
- User types natural language: "show me tech contacts in SF"
- LLM parses intent → structured JSON: `{"intent": "search", "filters": {"tags": ["tech"], "location": ["SF"]}}`
- Python code executes the query and formats results
- LLM never sees actual contact data, preventing hallucinations

See [01_Architecture.md](./01_Architecture.md) for complete architecture details.

---

## Prerequisites

### Installing Ollama

1. **Install Ollama** from [ollama.ai](https://ollama.ai)

   **macOS/Linux**:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

   **Manual download**: Visit [ollama.ai/download](https://ollama.ai/download)

2. **Pull the GPT-OSS-20B model**:
   ```bash
   ollama pull gpt-oss:20b
   ```

   **Note**: This is a ~13GB download and will take several minutes.

3. **Start Ollama service**:
   ```bash
   ollama serve
   ```

   **Or** start automatically (macOS):
   ```bash
   brew services start ollama
   ```

4. **Verify installation**:
   ```bash
   curl http://localhost:11434/v1/models
   ```

   You should see a JSON response with available models.

### System Requirements

- **RAM**: At least 16GB (32GB recommended for optimal performance)
- **Storage**: ~40GB for the gpt-oss:20b model
- **GPU**: Optional but recommended for faster inference
- **OS**: macOS, Linux, or Windows with WSL2

### Alternative Models

You can use other Ollama models, but performance may vary:

```bash
# Smaller, faster models (for testing)
ollama pull llama3.2:3b      # ~2GB, much faster
ollama pull mistral:7b       # ~4GB, good balance

# Larger, more accurate models
ollama pull llama3.1:70b     # ~40GB, very accurate but slow
```

**Configuration**: Edit `prt_config.json` to change the model (see [02_Configuration.md](./02_Configuration.md)).

---

## Configuration

### Basic Configuration

Edit `prt_data/prt_config.json` and add the `llm` section:

```json
{
  "llm": {
    "provider": "ollama",
    "model": "gpt-oss:20b",
    "base_url": "http://localhost:11434/v1",
    "timeout": 120,
    "temperature": 0.1,
    "keep_alive": "30m"
  }
}
```

### Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `provider` | `"ollama"` | LLM provider (only Ollama supported currently) |
| `model` | `"gpt-oss:20b"` | Ollama model to use |
| `base_url` | `"http://localhost:11434/v1"` | Ollama API endpoint |
| `timeout` | `120` | Request timeout in seconds |
| `temperature` | `0.1` | Sampling temperature (0.0-1.0, lower = more consistent) |
| `keep_alive` | `"30m"` | How long to keep model in memory after last use |

### Keep-Alive Parameter (Important!)

The `keep_alive` parameter prevents the model from being unloaded from memory:

- **Why it matters**: Loading the model takes 20-40 seconds the first time
- **Recommended value**: `"30m"` (keeps model loaded for 30 minutes)
- **Tradeoff**: Uses more RAM but responses are instant after first query

```json
{
  "llm": {
    "keep_alive": "30m"  // ← Keeps model in memory, faster responses
  }
}
```

### Remote Ollama Instance

If running Ollama on a different machine:

```json
{
  "llm": {
    "base_url": "http://your-server:11434/v1"
  }
}
```

**Security**: Only use remote Ollama on trusted networks. The API is not authenticated.

For complete configuration options (permissions, prompts, context), see [02_Configuration.md](./02_Configuration.md).

---

## Usage

### TUI Chat Screen

1. **Launch PRT TUI**:
   ```bash
   python -m prt_src.tui
   ```

2. **Navigate to Chat screen**: Press `c` from the home screen

3. **Start chatting**:
   - Chat screen starts in EDIT mode (ready to type)
   - Type your message
   - Press ENTER to send
   - LLM processes and responds

**Key bindings**:
- `ENTER` - Send message (in EDIT mode)
- `CTRL+J` - Insert newline without sending
- `ESC` - Toggle between EDIT and NAV modes
- `j/k` - Scroll up/down (in NAV mode)

### Example Conversations

#### Basic Search

```
> show me all my tech contacts
Found 47 contacts tagged 'tech':
[1] Alice Chen (SF) - python, AI
[2] Bob Martinez (Oakland) - devops, cloud
[3] Carol White (Berkeley) - golang, distributed systems
...

> just the ones in San Francisco
Refined to 12 tech contacts in SF:
[1] Alice Chen - python, AI
[2] David Park - security, networking
...

> select 1 and 2
✓ Selected 2 contacts
```

#### Refinement and Export

```
> show me contacts I haven't talked to in 6 months
Found 23 contacts you haven't connected with recently:
[1] Alice Chen - last contact 8 months ago
[2] David Lee - last contact 7 months ago
...

> select the first 5
✓ Selected 5 contacts

> export them for the directory maker
✓ Exported to exports/directory_20250110_153022/

Run: python tools/make_directory.py generate exports/directory_20250110_153022/
```

---

## Performance Optimization

### Model Loading

**First query**: 20-40 seconds (model loads into memory)
**Subsequent queries**: 3-10 seconds (model already loaded)

**To minimize wait times**:
1. Set `keep_alive: "30m"` in config (keeps model in memory)
2. Use a preload mechanism (ChatScreen does this automatically on mount)
3. Consider using a smaller model for development (`llama3.2:3b`)

### GPU Acceleration

**Check if GPU is available**:
```bash
nvidia-smi  # NVIDIA GPUs
```

**If you have a CUDA-compatible GPU**, Ollama will use it automatically. No configuration needed.

**Expected speedup**:
- CPU only: 10-30s per query
- GPU (NVIDIA RTX 3060+): 3-10s per query
- Apple Silicon (M1/M2/M3): 5-15s per query

### Memory Management

**Model memory usage**:
- `llama3.2:3b` - ~2GB RAM
- `gpt-oss:20b` - ~13GB RAM
- `llama3.1:70b` - ~40GB RAM

**Tips**:
- Close other memory-intensive apps when using larger models
- Monitor RAM usage: `htop` (Linux/macOS) or Task Manager (Windows)
- Use smaller models for testing/development
- Set reasonable `keep_alive` (don't leave models loaded indefinitely)

### Response Time Optimization

| Strategy | Benefit | Tradeoff |
|----------|---------|----------|
| Use smaller model | 3-5x faster | Less accurate parsing |
| Enable GPU | 2-3x faster | Requires GPU hardware |
| Set `keep_alive: "30m"` | No cold start delay | Uses more RAM |
| Lower `temperature` to 0.0 | Slightly faster | Less creative responses |

---

## Troubleshooting

### Connection Issues

#### Error: "Cannot connect to Ollama"

**Check 1**: Is Ollama running?
```bash
curl http://localhost:11434/v1/models
```

**If connection fails**:
```bash
# Start Ollama manually
ollama serve

# Or check service status (macOS)
brew services list | grep ollama
```

**Check 2**: Firewall blocking?
- Ensure port 11434 is not blocked
- If using remote Ollama, check network connectivity

#### Error: "Model not found: gpt-oss:20b"

**Solution**: Pull the model
```bash
ollama pull gpt-oss:20b

# Or use a different model
ollama pull llama3.2:3b
```

**Check available models**:
```bash
ollama list
```

### Performance Issues

#### Symptom: Very slow responses (>60 seconds)

**Possible causes**:

1. **Model loading for first time** (normal)
   - Wait 30-40s for initial load
   - Set `keep_alive: "30m"` to avoid reloading

2. **Insufficient RAM**
   - Close other apps
   - Use smaller model: `ollama pull llama3.2:3b`
   - Check memory usage: `free -h` (Linux) or Activity Monitor (macOS)

3. **No GPU acceleration**
   - Verify GPU: `nvidia-smi` (NVIDIA) or `system_profiler SPDisplaysDataType` (macOS)
   - CPU inference is slower but functional

4. **Ollama version outdated**
   - Update Ollama: Visit [ollama.ai/download](https://ollama.ai/download)
   - Check version: `ollama --version`

#### Symptom: Chat screen shows "LLM: ERROR"

**Check TUI logs**:
```bash
tail -f prt_data/prt.log | grep -E 'CHAT|LLM'
```

**Common errors**:

| Error | Cause | Solution |
|-------|-------|----------|
| "Timeout waiting for response" | Slow model, long prompt | Increase `timeout` in config |
| "Invalid JSON response" | LLM hallucinating | Lower `temperature`, improve system prompt |
| "Model not loaded" | Keep-alive expired | Increase `keep_alive`, restart Ollama |

### LLM Parsing Issues

#### Symptom: LLM doesn't understand queries

**Examples**:
- "show me tech contacts" → LLM returns error or wrong intent
- "select 1, 2, 3" → LLM doesn't extract IDs correctly

**Solutions**:

1. **Check system prompt** (see [02_Configuration.md](./02_Configuration.md))
   - Ensure prompt clearly defines JSON schema
   - Include examples of correct responses

2. **Try different model**
   ```bash
   # GPT-OSS-20B is recommended, but alternatives:
   ollama pull mistral:7b       # Good for structured output
   ollama pull llama3.1:70b     # Very accurate but slow
   ```

3. **Run contract tests** (see [06_Contract_Testing.md](./06_Contract_Testing.md))
   ```bash
   npx promptfoo eval -c tests/llm_contracts/promptfoo.yaml
   ```

4. **Enable debug logging** (see [02_Configuration.md](./02_Configuration.md#llm_developer-developer-tools))
   ```json
   {
     "llm_developer": {
       "debug_mode": true,
       "log_prompts": true,
       "log_responses": true
     }
   }
   ```

---

## Security and Privacy

### Local Processing

✅ **Advantages**:
- **Complete privacy** - All data stays on your machine
- **No internet required** - Works offline
- **No API costs** - Free to use
- **No rate limits** - Query as much as you want

⚠️ **Considerations**:
- **System resources** - Requires RAM and CPU/GPU
- **Model download** - Initial 13GB download needed
- **No cloud backups** - You're responsible for data backups

### Data Safety

**What the LLM sees**:
- User queries ("show me tech contacts")
- Context summaries (counts, filters)
- NO raw contact data (names, emails, addresses)

**What the LLM does NOT see**:
- Full contact details
- Relationship data
- Notes content
- Database IDs or internal state

**Why**: The LLM only translates intent to JSON. Code handles all data access and formatting.

### Permission System

Control what the LLM can do via configuration (see [02_Configuration.md](./02_Configuration.md#llm_permissions-safety-controls)):

```json
{
  "llm_permissions": {
    "allow_create": true,      // Can create new contacts/tags/notes
    "allow_update": true,      // Can update existing records
    "allow_delete": false,     // Cannot delete (safe default)
    "require_confirmation": {
      "delete": true,          // Confirm before deletes
      "bulk_operations": true  // Confirm before bulk actions
    }
  }
}
```

**Best practices**:
- Start with `allow_delete: false` until comfortable
- Enable `require_confirmation` for risky operations
- Use `read_only_mode: true` for safe exploration

---

## Development and Testing

### Testing Ollama Connection

**Quick test**:
```bash
# Test Ollama directly
ollama run gpt-oss:20b "What is 2+2?"

# Test via PRT LLM service
python -c "
from prt_src.llm_ollama import OllamaLLM
from prt_src.api import PRTAPI

api = PRTAPI()
llm = OllamaLLM(api)
print(llm.chat('hello'))
"
```

### Running Contract Tests

See [06_Contract_Testing.md](./06_Contract_Testing.md) for details.

**Quick run**:
```bash
cd tests/llm_contracts
npx promptfoo eval -c promptfoo.yaml
```

**What it tests**:
- Intent classification accuracy (>95%)
- Parameter extraction correctness
- JSON schema validation (100%)
- No hallucinations (0%)

### Model Comparison

**To test different models**, change config and run contract tests:

```bash
# Test with llama3.2:3b (fast)
ollama pull llama3.2:3b
# Edit prt_config.json: "model": "llama3.2:3b"
npx promptfoo eval

# Test with gpt-oss:20b (recommended)
ollama pull gpt-oss:20b
# Edit prt_config.json: "model": "gpt-oss:20b"
npx promptfoo eval
```

Compare accuracy, speed, and resource usage.

---

## Advanced Configuration

### Custom System Prompt

See [02_Configuration.md](./02_Configuration.md#llm_prompts-system-prompt-configuration) for complete details.

**Override system prompt**:
```json
{
  "llm_prompts": {
    "override_system_prompt": "Your custom system prompt here...",
    "use_file": false
  }
}
```

**Load from file**:
```json
{
  "llm_prompts": {
    "use_file": true,
    "file_path": "prt_data/custom_prompt.txt"
  }
}
```

### Context Management

Control how much context is sent to the LLM:

```json
{
  "llm_context": {
    "mode": "adaptive",           // minimal | detailed | adaptive
    "max_conversation_history": 3, // Last N exchanges
    "max_context_tokens": 4000     // Total token budget
  }
}
```

See [01_Architecture.md](./01_Architecture.md#context-management-strategy) for details.

---

## Support and Resources

### Documentation
- [Ollama Documentation](https://ollama.ai/docs)
- [Model Library](https://ollama.ai/library)
- [API Reference](https://github.com/ollama/ollama/blob/main/docs/api.md)

### Troubleshooting Resources
- **PRT logs**: `prt_data/prt.log` (check for errors)
- **Ollama logs**: `~/.ollama/logs/` (macOS/Linux)
- **GitHub Issues**: [github.com/richbodo/prt/issues](https://github.com/richbodo/prt/issues)

### Community
- **Ollama Discord**: [discord.gg/ollama](https://discord.gg/ollama)
- **PRT Discussions**: Open an issue on GitHub

---

## Related Documentation

- **[01_Architecture.md](./01_Architecture.md)** - Complete Chat screen architecture
- **[02_Configuration.md](./02_Configuration.md)** - Full LLM configuration reference
- **[03_Implementation_Plan.md](./03_Implementation_Plan.md)** - Development roadmap
- **[04_Testing_Strategy.md](./04_Testing_Strategy.md)** - Testing approach
- **[06_Contract_Testing.md](./06_Contract_Testing.md)** - LLM validation with promptfoo

---

## Future Enhancements

Planned improvements for Ollama integration:

- **Streaming responses** - Real-time token streaming for better UX
- **Multi-model support** - Switch models on-the-fly
- **Auto-model selection** - Choose model based on query complexity
- **Response caching** - Cache common queries for instant responses
- **Custom tool definitions** - User-defined functions for LLM
- **Conversation persistence** - Save and resume chat sessions
- **Performance monitoring** - Track response times and accuracy metrics

See [03_Implementation_Plan.md](./03_Implementation_Plan.md) for implementation timeline.
