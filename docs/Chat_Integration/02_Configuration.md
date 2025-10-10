# LLM Configuration and Safeguards

This document describes the configurable LLM settings and safeguards for PRT's chat interface.

## Design Philosophy

**Developer-First**: All settings are accessible via JSON configuration for experimentation.
**Future-Safe**: Settings structure supports both "dev mode" and future "safe mode" for end users.
**Transparent**: All LLM interactions can be logged and debugged.
**Controlled**: Permissions system prevents unintended data modifications.

---

## Configuration File: `prt_data/prt_config.json`

### Complete LLM Configuration Block

```json
{
  "llm": {
    "provider": "ollama",
    "model": "gpt-oss:20b",
    "base_url": "http://localhost:11434/v1",
    "timeout": 120,
    "keep_alive": "30m",
    "temperature": 0.1,
    "max_tokens": 2048,
    "top_p": 0.9,
    "top_k": 40,
    "repeat_penalty": 1.1
  },

  "llm_permissions": {
    "allow_create": true,
    "allow_update": true,
    "allow_delete": false,
    "require_confirmation": {
      "create": false,
      "update": false,
      "delete": true,
      "bulk_operations": true
    },
    "max_bulk_operations": 100,
    "read_only_mode": false
  },

  "llm_prompts": {
    "system_prompt_override": null,
    "system_prompt_file": null,
    "enable_custom_prompts": true,
    "prompt_templates_dir": "prt_data/prompt_templates"
  },

  "llm_context": {
    "max_conversation_history": 10,
    "context_mode": "adaptive",
    "max_context_tokens": 4000,
    "enable_conversation_memory": true,
    "prune_old_context": true
  },

  "llm_developer": {
    "debug_mode": false,
    "log_prompts": false,
    "log_responses": false,
    "log_file": "prt_data/llm_debug.log",
    "enable_experimental_features": false,
    "show_token_usage": false,
    "show_timing": false
  }
}
```

---

## Configuration Sections

### 1. `llm` - Connection & Model Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `provider` | string | "ollama" | LLM provider (currently only Ollama) |
| `model` | string | "gpt-oss:20b" | Model identifier |
| `base_url` | string | "http://localhost:11434/v1" | Ollama API endpoint |
| `timeout` | int | 120 | Request timeout in seconds |
| `keep_alive` | string | "30m" | How long to keep model in memory ("5m", "30m", "1h", -1 for infinite) |
| `temperature` | float | 0.1 | Sampling temperature (0.0-2.0, lower = more deterministic) |
| `max_tokens` | int | 2048 | Maximum response length |
| `top_p` | float | 0.9 | Nucleus sampling threshold |
| `top_k` | int | 40 | Top-k sampling limit |
| `repeat_penalty` | float | 1.1 | Penalty for repetition (1.0 = no penalty) |

**Developer Notes:**
- **Temperature**: Use 0.1 for consistent parsing, 0.7+ for creative responses
- **Keep-alive**: "30m" prevents model unloading between queries (13GB model takes 20-40s to load)
- **Timeout**: Large models may need 120s+ for complex queries

---

### 2. `llm_permissions` - Safety Controls

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `allow_create` | bool | true | Allow LLM to create new contacts/relationships/notes |
| `allow_update` | bool | true | Allow LLM to modify existing records |
| `allow_delete` | bool | false | Allow LLM to delete records (dangerous!) |
| `require_confirmation` | object | see below | Confirmation requirements per action |
| `max_bulk_operations` | int | 100 | Maximum items in bulk operations |
| `read_only_mode` | bool | false | Disable all write operations (read-only mode) |

**`require_confirmation` sub-object:**
```json
{
  "create": false,      // Confirm before creating records
  "update": false,      // Confirm before updating records
  "delete": true,       // Always confirm deletes (recommended!)
  "bulk_operations": true  // Confirm bulk ops (>10 items)
}
```

**Safety Recommendations:**
- **Delete**: Keep `allow_delete: false` or `require_confirmation.delete: true`
- **Bulk ops**: Always require confirmation for bulk operations
- **Production**: Set `read_only_mode: true` for safe exploration

**Permission Enforcement:**

When LLM returns a command that requires permissions:

```python
if command['intent'] == 'delete':
    if not config.llm_permissions.allow_delete:
        show_error("Delete operations are disabled in settings")
        return

    if config.llm_permissions.require_confirmation.delete:
        confirmed = await show_confirmation_dialog(
            "Delete 5 contacts?",
            "This cannot be undone."
        )
        if not confirmed:
            return
```

---

### 3. `llm_prompts` - System Prompt Configuration

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `system_prompt_override` | string | null | Full system prompt override (multiline string) |
| `system_prompt_file` | string | null | Path to system prompt file |
| `enable_custom_prompts` | bool | true | Allow custom prompts (dev mode) |
| `prompt_templates_dir` | string | "prt_data/prompt_templates" | Directory for prompt templates |

**Usage:**

**Option 1: Inline Override**
```json
{
  "llm_prompts": {
    "system_prompt_override": "You are a helpful assistant...\n\nReturn JSON..."
  }
}
```

**Option 2: File Reference**
```json
{
  "llm_prompts": {
    "system_prompt_file": "prt_data/prompt_templates/custom_system_prompt.txt"
  }
}
```

**Option 3: Default (Built-in)**
```json
{
  "llm_prompts": {
    "system_prompt_override": null,
    "system_prompt_file": null
  }
}
```

**Loading Priority:**
1. If `system_prompt_override` is set → use it
2. Else if `system_prompt_file` is set → load from file
3. Else → use built-in default prompt

**Developer Workflow:**

1. Export current prompt: `python -m prt_src.cli export-prompt > my_prompt.txt`
2. Edit `my_prompt.txt`
3. Set `system_prompt_file` in config
4. Test in chat
5. Iterate

---

### 4. `llm_context` - Context Management

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `max_conversation_history` | int | 10 | Maximum conversation turns to keep |
| `context_mode` | string | "adaptive" | Context inclusion mode (see below) |
| `max_context_tokens` | int | 4000 | Hard limit on context size (tokens) |
| `enable_conversation_memory` | bool | true | Maintain conversation across queries |
| `prune_old_context` | bool | true | Remove old context when limit exceeded |

**Context Modes:**

- **`minimal`**: Always use minimal context (fastest, cheapest)
  - Good for: Simple commands, known workflows
  - Token usage: ~500-1000 per query

- **`detailed`**: Always include full result details
  - Good for: Complex queries, content-based filtering
  - Token usage: ~2000-4000 per query

- **`adaptive`** (recommended): Decide based on query content
  - Uses heuristics to determine when details are needed
  - Token usage: ~500-2000 per query (varies)

**Token Budget Example:**

With `max_context_tokens: 4000`:
- System prompt: ~500 tokens
- Conversation history (3 turns): ~600 tokens
- Current display context: ~500-2000 tokens (adaptive)
- User message: ~50 tokens
- **Total**: ~1650-3150 tokens (within budget)

---

### 5. `llm_developer` - Developer Tools

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `debug_mode` | bool | false | Enable verbose debug logging |
| `log_prompts` | bool | false | Save all prompts to log file |
| `log_responses` | bool | false | Save all LLM responses to log file |
| `log_file` | string | "prt_data/llm_debug.log" | Debug log file path |
| `enable_experimental_features` | bool | false | Enable experimental/unstable features |
| `show_token_usage` | bool | false | Display token counts in UI |
| `show_timing` | bool | false | Display timing info in UI |

**Debug Mode Output:**

When `debug_mode: true`:
```
[LLM] Prompt length: 1542 tokens
[LLM] Context mode: adaptive (using minimal)
[LLM] Sending request to http://localhost:11434/v1
[LLM] Response received in 12.3s
[LLM] Response length: 87 tokens
[LLM] Parsed intent: search
```

When `log_prompts: true`:
```
# prt_data/llm_debug.log
[2025-01-10 15:30:42] PROMPT
================================================================================
You are a database query assistant...

Current context: 50 tech contacts in San Francisco

User: show me the ones in Oakland
================================================================================

[2025-01-10 15:30:54] RESPONSE
================================================================================
{"intent": "refine", "parameters": {...}}
================================================================================
```

**Experimental Features:**

Future experimental features will be gated behind `enable_experimental_features`:
- Function calling (when Ollama supports it)
- Multi-model fallback
- Streaming responses
- Conversation branching

---

## Settings UI Integration

The Settings screen will display these configurations in editable form:

```
╔══════════════════════════════════════════════════════════════╗
║ SETTINGS > LLM CONFIGURATION                                 ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║ Connection                                                   ║
║   Model: gpt-oss:20b                         [Edit]         ║
║   Timeout: 120s                              [Edit]         ║
║   Keep-alive: 30m                            [Edit]         ║
║   Temperature: 0.1                           [Edit]         ║
║                                                              ║
║ Permissions                                                  ║
║   [✓] Allow Create    [ ] Allow Delete                      ║
║   [✓] Allow Update    [✓] Read-only Mode                    ║
║                                                              ║
║   Require Confirmation:                                      ║
║     [ ] Create        [✓] Delete                            ║
║     [ ] Update        [✓] Bulk Operations                   ║
║                                                              ║
║ System Prompt                                                ║
║   [ ] Use custom prompt                                      ║
║   File: (not set)                            [Browse]       ║
║                                                              ║
║ Developer Options                                            ║
║   [ ] Debug mode      [ ] Log prompts                       ║
║   [ ] Show timing     [ ] Experimental features             ║
║                                                              ║
║ [Save Changes]  [Restore Defaults]  [Export Config]         ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Configuration Loading & Validation

```python
# prt_src/config.py

from dataclasses import dataclass
from typing import Optional
import json
import os

@dataclass
class LLMConfig:
    """LLM connection and model settings."""
    provider: str = "ollama"
    model: str = "gpt-oss:20b"
    base_url: str = "http://localhost:11434/v1"
    timeout: int = 120
    keep_alive: str = "30m"
    temperature: float = 0.1
    max_tokens: int = 2048
    top_p: float = 0.9
    top_k: int = 40
    repeat_penalty: float = 1.1

@dataclass
class LLMPermissions:
    """LLM safety permissions."""
    allow_create: bool = True
    allow_update: bool = True
    allow_delete: bool = False
    require_confirmation: dict = None
    max_bulk_operations: int = 100
    read_only_mode: bool = False

    def __post_init__(self):
        if self.require_confirmation is None:
            self.require_confirmation = {
                'create': False,
                'update': False,
                'delete': True,
                'bulk_operations': True
            }

@dataclass
class LLMPrompts:
    """System prompt configuration."""
    system_prompt_override: Optional[str] = None
    system_prompt_file: Optional[str] = None
    enable_custom_prompts: bool = True
    prompt_templates_dir: str = "prt_data/prompt_templates"

@dataclass
class LLMContext:
    """Context management settings."""
    max_conversation_history: int = 10
    context_mode: str = "adaptive"
    max_context_tokens: int = 4000
    enable_conversation_memory: bool = True
    prune_old_context: bool = True

@dataclass
class LLMDeveloper:
    """Developer tools configuration."""
    debug_mode: bool = False
    log_prompts: bool = False
    log_responses: bool = False
    log_file: str = "prt_data/llm_debug.log"
    enable_experimental_features: bool = False
    show_token_usage: bool = False
    show_timing: bool = False


class LLMConfigManager:
    """Load and validate LLM configuration from prt_config.json."""

    def __init__(self, config_path: str = "prt_data/prt_config.json"):
        self.config_path = config_path
        self.llm = LLMConfig()
        self.permissions = LLMPermissions()
        self.prompts = LLMPrompts()
        self.context = LLMContext()
        self.developer = LLMDeveloper()

    def load(self) -> bool:
        """Load configuration from file."""
        if not os.path.exists(self.config_path):
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            return False

        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)

            # Load each section
            if 'llm' in config_data:
                self.llm = LLMConfig(**config_data['llm'])

            if 'llm_permissions' in config_data:
                self.permissions = LLMPermissions(**config_data['llm_permissions'])

            if 'llm_prompts' in config_data:
                self.prompts = LLMPrompts(**config_data['llm_prompts'])

            if 'llm_context' in config_data:
                self.context = LLMContext(**config_data['llm_context'])

            if 'llm_developer' in config_data:
                self.developer = LLMDeveloper(**config_data['llm_developer'])

            self.validate()
            return True

        except Exception as e:
            logger.error(f"Failed to load LLM config: {e}")
            return False

    def validate(self):
        """Validate configuration values."""
        # Validate temperature
        if not 0.0 <= self.llm.temperature <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")

        # Validate context mode
        valid_modes = ['minimal', 'detailed', 'adaptive']
        if self.context.context_mode not in valid_modes:
            raise ValueError(f"context_mode must be one of {valid_modes}")

        # Validate timeout
        if self.llm.timeout < 1:
            raise ValueError("timeout must be at least 1 second")

        # Validate max_bulk_operations
        if self.permissions.max_bulk_operations < 1:
            raise ValueError("max_bulk_operations must be at least 1")

    def save(self) -> bool:
        """Save current configuration to file."""
        config_data = {
            'llm': self.llm.__dict__,
            'llm_permissions': self.permissions.__dict__,
            'llm_prompts': self.prompts.__dict__,
            'llm_context': self.context.__dict__,
            'llm_developer': self.developer.__dict__
        }

        try:
            # Load existing config
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    existing = json.load(f)
            else:
                existing = {}

            # Merge LLM settings
            existing.update(config_data)

            # Write back
            with open(self.config_path, 'w') as f:
                json.dump(existing, f, indent=2)

            return True

        except Exception as e:
            logger.error(f"Failed to save LLM config: {e}")
            return False

    def get_system_prompt(self) -> str:
        """Load system prompt based on configuration.

        Priority:
        1. system_prompt_override (direct string)
        2. system_prompt_file (load from file)
        3. Default built-in prompt
        """
        if self.prompts.system_prompt_override:
            return self.prompts.system_prompt_override

        if self.prompts.system_prompt_file:
            try:
                with open(self.prompts.system_prompt_file, 'r') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Failed to load system prompt file: {e}")
                # Fall through to default

        # Return default built-in prompt
        from prt_src.llm_bridge import DEFAULT_SYSTEM_PROMPT
        return DEFAULT_SYSTEM_PROMPT
```

---

## Safety Guardrails

### Confirmation Dialogs

For risky operations, show confirmation:

```python
async def show_confirmation_dialog(
    title: str,
    message: str,
    items: list = None,
    action: str = "Continue"
) -> bool:
    """Show confirmation dialog and wait for user response."""
    # Textual Modal Dialog
    dialog = ConfirmationDialog(
        title=title,
        message=message,
        items=items,  # Optional: show what will be affected
        action_label=action,
        cancel_label="Cancel"
    )

    result = await self.app.push_screen_wait(dialog)
    return result
```

Example usage:
```python
if command['intent'] == 'delete':
    items = [f"• {item.name}" for item in selected_items]

    confirmed = await show_confirmation_dialog(
        title="⚠️  Delete Contacts",
        message=f"Permanently delete {len(items)} contacts?",
        items=items,
        action="Delete Forever"
    )

    if not confirmed:
        self._add_to_buffer("❌ Deletion cancelled\n")
        return
```

### Read-Only Mode

When `read_only_mode: true`:

```python
# All write operations rejected
if config.permissions.read_only_mode:
    if command['intent'] in ['create', 'update', 'delete']:
        show_error("Read-only mode is enabled. Change settings to allow modifications.")
        return
```

### Audit Logging

All LLM-initiated data operations should be logged:

```python
# prt_src/audit_log.py

def log_llm_operation(
    operation: str,
    entity_type: str,
    entity_ids: list,
    success: bool,
    error: str = None
):
    """Log LLM-initiated data operations to audit log."""
    audit_entry = {
        'timestamp': datetime.now().isoformat(),
        'source': 'llm_chat',
        'operation': operation,  # 'create', 'update', 'delete'
        'entity_type': entity_type,
        'entity_ids': entity_ids,
        'count': len(entity_ids),
        'success': success,
        'error': error
    }

    # Append to audit log
    with open('prt_data/audit.log', 'a') as f:
        f.write(json.dumps(audit_entry) + '\n')
```

---

## Future: Safe Mode vs Dev Mode

**Future Architecture** (Phase 7+):

```json
{
  "llm": {
    "mode": "dev",  // or "safe"
    ...
  }
}
```

**Safe Mode** (default for end users):
- `allow_delete: false` (forced)
- `require_confirmation.bulk_operations: true` (forced)
- `enable_custom_prompts: false`
- `system_prompt_override: null` (ignored if set)
- Limited to pre-approved prompt templates

**Dev Mode** (for developers):
- All settings available
- Custom prompts allowed
- Full permission control
- Debug tools enabled

---

## Example Configurations

### 1. Conservative (Recommended for Start)

```json
{
  "llm": {
    "model": "gpt-oss:20b",
    "timeout": 120,
    "temperature": 0.1
  },
  "llm_permissions": {
    "allow_create": true,
    "allow_update": false,
    "allow_delete": false,
    "require_confirmation": {
      "create": true,
      "bulk_operations": true
    }
  }
}
```

### 2. Developer Mode (Full Control)

```json
{
  "llm": {
    "model": "gpt-oss:20b",
    "timeout": 120,
    "temperature": 0.1
  },
  "llm_permissions": {
    "allow_create": true,
    "allow_update": true,
    "allow_delete": true,
    "require_confirmation": {
      "delete": true,
      "bulk_operations": true
    }
  },
  "llm_developer": {
    "debug_mode": true,
    "log_prompts": true,
    "log_responses": true,
    "show_timing": true
  }
}
```

### 3. Read-Only Exploration

```json
{
  "llm_permissions": {
    "read_only_mode": true
  }
}
```

---

## Migration from Existing Config

Current `llm_ollama.py` hardcodes settings. Migration plan:

**Phase 1: Add config loading** (backward compatible)
- Load from config if available
- Fall back to hardcoded defaults
- No breaking changes

**Phase 2: Deprecate hardcoded values**
- Log warnings if config not found
- Encourage migration

**Phase 3: Require config**
- Remove hardcoded defaults
- Config file required

---

## CLI Commands for Configuration

```bash
# Export current system prompt
python -m prt_src.cli export-llm-prompt > my_prompt.txt

# Validate configuration
python -m prt_src.cli validate-llm-config

# Show current LLM settings
python -m prt_src.cli show-llm-config

# Test LLM connection
python -m prt_src.cli test-llm
```

---

## Summary

This configuration system provides:
- ✅ **Flexible**: All settings exposed for experimentation
- ✅ **Safe**: Permissions and confirmation controls
- ✅ **Transparent**: Full logging and debug capabilities
- ✅ **Developer-friendly**: JSON editing, file-based prompts
- ✅ **Future-proof**: Ready for "safe mode" in production
- ✅ **Auditable**: All data operations logged

Developers can experiment freely while maintaining safety guardrails.
