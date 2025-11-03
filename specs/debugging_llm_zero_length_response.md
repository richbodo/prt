# Debugging Plan: LLM Zero-Length Response with Real-World Data

## Problem Statement

Tests pass with fixture data, but real-world data produces zero-length LLM responses when executing "create a directory of contacts with images" workflow. Need comprehensive instrumentation to identify where the tool chaining breaks.

### Note on testing with real-world data

It is perfectly fine to destructively test with the real world data currently in prt.db.  That can be reconstructed easily and it is the ideal testbed for what we are trying to test.

## Implementation Plan: Phase 1 - Comprehensive Instrumentation

### 1. Multi-Channel Logging Setup

**Files to Modify:**
- `prt_src/logging_config.py` - Add debug level configuration and new log file
- Create new debug log stream specifically for workflow tracing

**Implementation:**
```python
# Add to logging_config.py
def setup_debug_logging():
    """Setup detailed debug logging for LLM workflow troubleshooting."""
    debug_handler = logging.FileHandler('prt_data/debug_llm_chaining.log')
    debug_handler.setLevel(logging.DEBUG)
    debug_formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] [%(funcName)s] %(message)s'
    )
    debug_handler.setFormatter(debug_formatter)

    # Add to all relevant loggers
    for logger_name in ['prt_src.llm_ollama', 'prt_src.api', 'prt_src.llm_memory']:
        logger = logging.getLogger(logger_name)
        logger.addHandler(debug_handler)
        logger.setLevel(logging.DEBUG)
```

**Log Structure:**
```
[TIMESTAMP] [COMPONENT] [LEVEL] [FUNCTION] [OPERATION] message data
[2024-11-03 13:45:22] [prt_src.llm_ollama] [INFO] [chat] [USER_INPUT] "create directory of contacts with images"
[2024-11-03 13:45:22] [prt_src.llm_ollama] [DEBUG] [_save_contacts_with_images] [TOOL_START] Starting tool execution
[2024-11-03 13:45:23] [prt_src.api] [INFO] [get_contacts_with_images] [QUERY_RESULT] Found 1,247 contacts, 180MB total
```

### 2. LLM Conversation Level Instrumentation

**File:** `prt_src/llm_ollama.py`

**Target Methods:**
- `chat()` - Main conversation handler
- `_save_contacts_with_images()` - First tool in chain
- `_generate_directory()` - Second tool in chain
- `_list_memory()` - Memory browsing tool

**Critical Instrumentation Points:**

#### A. chat() Method Enhancement
```python
def chat(self, messages: List[Dict[str, str]], model: str = None) -> str:
    logger.info(f"[CHAT_START] User message: {messages[-1]['content'][:100]}...")
    logger.debug(f"[CHAT_CONTEXT] Total messages: {len(messages)}, context size: {len(str(messages))}")

    # Log system prompt size
    system_prompt = self._get_system_prompt()
    logger.debug(f"[SYSTEM_PROMPT] Size: {len(system_prompt)} chars")

    try:
        # Existing chat logic...

        # Log tool calls if they occur
        if "tool_calls" in response:
            logger.info(f"[TOOL_CALLS] Found {len(response['tool_calls'])} tool calls")
            for i, tool_call in enumerate(response['tool_calls']):
                logger.info(f"[TOOL_CALL_{i}] {tool_call['function']['name']}({tool_call['function']['arguments'][:200]}...)")

        # Log final response
        final_response = response.get('message', {}).get('content', '')
        logger.info(f"[CHAT_RESPONSE] Length: {len(final_response)}, preview: {final_response[:100]}...")

        if len(final_response) == 0:
            logger.error(f"[ZERO_LENGTH_RESPONSE] Empty response detected! Tool calls: {len(response.get('tool_calls', []))}")
            logger.error(f"[ZERO_LENGTH_RESPONSE] Full response object: {response}")

        return final_response

    except Exception as e:
        logger.error(f"[CHAT_ERROR] Exception in chat: {e}", exc_info=True)
        raise
```

#### B. Tool Execution Instrumentation
```python
def _save_contacts_with_images(self, description: str = "contacts with images") -> Dict[str, Any]:
    logger.info(f"[TOOL_START] save_contacts_with_images(description='{description}')")
    logger.debug(f"[TOOL_CONTEXT] API available: {self.api is not None}")

    start_time = time.time()

    try:
        # Query execution
        logger.debug(f"[QUERY_START] Calling api.get_contacts_with_images()")
        contacts = self.api.get_contacts_with_images()
        query_time = time.time() - start_time

        logger.info(f"[QUERY_RESULT] Found {len(contacts)} contacts in {query_time:.3f}s")

        if len(contacts) == 0:
            logger.warning(f"[QUERY_EMPTY] No contacts with images found")
            return {"success": False, "error": "No contacts with images found", "count": 0}

        # Data analysis
        total_image_size = sum(len(c.get('profile_image', b'')) for c in contacts)
        avg_image_size = total_image_size / len(contacts) if contacts else 0
        logger.debug(f"[DATA_ANALYSIS] Total image data: {total_image_size/1024/1024:.1f}MB, avg: {avg_image_size/1024:.1f}KB")

        # Memory save
        logger.debug(f"[MEMORY_SAVE_START] Saving {len(contacts)} contacts to memory")
        memory_save_start = time.time()

        memory_id = llm_memory.save_result(contacts, "contacts", description)
        memory_save_time = time.time() - memory_save_start

        logger.info(f"[MEMORY_SAVE_SUCCESS] Saved to {memory_id} in {memory_save_time:.3f}s")

        # Verify memory save
        logger.debug(f"[MEMORY_VERIFY] Attempting to load {memory_id}")
        verification = llm_memory.load_result(memory_id)
        if verification is None:
            logger.error(f"[MEMORY_VERIFY_FAIL] Cannot load {memory_id} immediately after save")
            return {"success": False, "error": "Memory save verification failed"}

        logger.debug(f"[MEMORY_VERIFY_SUCCESS] Loaded {len(verification.get('data', []))} contacts")

        # Tool response
        response = {
            "success": True,
            "memory_id": memory_id,
            "count": len(contacts),
            "description": description,
            "message": f"Saved {len(contacts)} contacts with images to memory",
            "usage": {
                "query_time_ms": query_time * 1000,
                "memory_save_time_ms": memory_save_time * 1000,
                "total_image_size_mb": total_image_size / 1024 / 1024
            }
        }

        logger.info(f"[TOOL_RESPONSE] Returning success response: {response}")
        return response

    except Exception as e:
        logger.error(f"[TOOL_ERROR] Exception in save_contacts_with_images: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
```

### 3. API Layer Instrumentation

**File:** `prt_src/api.py`

**Target Method:** `get_contacts_with_images()`

```python
def get_contacts_with_images(self) -> List[Dict[str, Any]]:
    logger.info(f"[API_QUERY_START] get_contacts_with_images() called")

    try:
        # SQL logging
        logger.debug(f"[SQL_QUERY] Executing optimized contacts with images query")
        logger.debug(f"[SQL_DETAIL] WHERE profile_image IS NOT NULL ORDER BY name")

        # Check index usage (if possible)
        logger.debug(f"[INDEX_CHECK] Assuming idx_contacts_profile_image_not_null exists")

        start_time = time.time()

        contacts = (
            self.db.session.query(Contact)
            .filter(Contact.profile_image.is_not(None))
            .order_by(Contact.name)
            .all()
        )

        query_time = time.time() - start_time

        # Convert to dict format and analyze
        result = []
        total_size = 0
        corrupted_count = 0

        for contact in contacts:
            contact_dict = {
                "id": contact.id,
                "name": contact.name,
                "email": contact.email,
                "phone": contact.phone,
                "profile_image": contact.profile_image,
                "profile_image_filename": contact.profile_image_filename,
                "profile_image_mime_type": contact.profile_image_mime_type,
            }

            # Image validation
            if contact.profile_image:
                image_size = len(contact.profile_image)
                total_size += image_size

                # Check for suspicious data
                if image_size < 100:  # Suspiciously small
                    logger.warning(f"[IMAGE_SUSPICIOUS] Contact {contact.id} has tiny image: {image_size} bytes")
                    corrupted_count += 1
                elif image_size > 5 * 1024 * 1024:  # Suspiciously large (>5MB)
                    logger.warning(f"[IMAGE_LARGE] Contact {contact.id} has huge image: {image_size/1024/1024:.1f}MB")

                # Basic format validation
                if contact.profile_image_mime_type and not contact.profile_image_mime_type.startswith('image/'):
                    logger.warning(f"[IMAGE_FORMAT] Contact {contact.id} has non-image MIME type: {contact.profile_image_mime_type}")
                    corrupted_count += 1

            result.append(contact_dict)

        logger.info(f"[API_QUERY_SUCCESS] Retrieved {len(result)} contacts in {query_time:.3f}s")
        logger.info(f"[API_DATA_ANALYSIS] Total image data: {total_size/1024/1024:.1f}MB, corrupted: {corrupted_count}")

        if corrupted_count > 0:
            logger.warning(f"[API_DATA_QUALITY] Found {corrupted_count} potentially corrupted images")

        return result

    except Exception as e:
        logger.error(f"[API_QUERY_ERROR] Exception in get_contacts_with_images: {e}", exc_info=True)
        raise
```

### 4. Memory System Instrumentation

**File:** `prt_src/llm_memory.py`

**Target Methods:** `save_result()`, `load_result()`

```python
def save_result(self, data: Any, result_type: str = "query", description: str = None) -> str:
    logger.info(f"[MEMORY_SAVE_START] Type: {result_type}, description: '{description}'")

    # Data analysis
    data_size = 0
    data_count = 0

    if isinstance(data, list):
        data_count = len(data)
        # Estimate size for contacts with images
        if data and isinstance(data[0], dict) and 'profile_image' in data[0]:
            total_image_size = sum(len(item.get('profile_image', b'')) for item in data)
            logger.debug(f"[MEMORY_DATA_ANALYSIS] {data_count} contacts, {total_image_size/1024/1024:.1f}MB images")
            data_size = total_image_size

        # Check for binary data issues
        binary_items = 0
        for item in data[:10]:  # Sample first 10
            if isinstance(item, dict) and 'profile_image' in item:
                if not isinstance(item['profile_image'], bytes):
                    logger.warning(f"[MEMORY_DATA_TYPE] profile_image is not bytes: {type(item['profile_image'])}")
                else:
                    binary_items += 1

        logger.debug(f"[MEMORY_BINARY_CHECK] {binary_items}/{min(10, len(data))} items have bytes profile_image")

    # Generate ID
    timestamp = datetime.now().strftime("%H%M%S")
    short_uuid = str(uuid.uuid4())[:8]
    result_id = f"{result_type}_{timestamp}_{short_uuid}"

    logger.debug(f"[MEMORY_ID_GENERATED] {result_id}")

    try:
        # Prepare metadata
        metadata = {
            "id": result_id,
            "type": result_type,
            "description": description or f"{result_type} result",
            "created_at": datetime.now().isoformat(),
            "data_count": data_count,
            "data": data
        }

        # JSON serialization attempt
        logger.debug(f"[MEMORY_JSON_START] Attempting JSON serialization")
        json_start = time.time()

        result_file = self.base_dir / f"{result_id}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)

        json_time = time.time() - json_start
        file_size = result_file.stat().st_size

        logger.info(f"[MEMORY_SAVE_SUCCESS] {result_id} saved in {json_time:.3f}s, file size: {file_size/1024/1024:.1f}MB")

        return result_id

    except Exception as e:
        logger.error(f"[MEMORY_SAVE_ERROR] Failed to save {result_id}: {e}", exc_info=True)

        # Additional debugging for JSON errors
        if "not JSON serializable" in str(e):
            logger.error(f"[MEMORY_JSON_ERROR] Analyzing non-serializable data...")
            for i, item in enumerate(data[:5]):  # Sample first 5
                try:
                    json.dumps(item, default=str)
                except Exception as item_error:
                    logger.error(f"[MEMORY_JSON_ITEM_ERROR] Item {i}: {item_error}")

        raise

def load_result(self, result_id: str) -> Optional[Dict[str, Any]]:
    logger.debug(f"[MEMORY_LOAD_START] Loading {result_id}")

    result_file = self.base_dir / f"{result_id}.json"

    if not result_file.exists():
        logger.error(f"[MEMORY_LOAD_MISSING] File not found: {result_file}")
        return None

    file_size = result_file.stat().st_size
    logger.debug(f"[MEMORY_LOAD_FILE] File size: {file_size/1024/1024:.1f}MB")

    try:
        load_start = time.time()

        with open(result_file, 'r', encoding='utf-8') as f:
            result = json.load(f)

        load_time = time.time() - load_start
        data_count = len(result.get('data', []))

        logger.info(f"[MEMORY_LOAD_SUCCESS] {result_id} loaded in {load_time:.3f}s, {data_count} items")

        return result

    except Exception as e:
        logger.error(f"[MEMORY_LOAD_ERROR] Failed to load {result_id}: {e}", exc_info=True)
        return None
```

### 5. Configuration Changes

**File:** `prt_src/logging_config.py`

```python
# Add debug level configuration
def configure_debug_logging():
    """Enable comprehensive debug logging for troubleshooting."""

    # Set all PRT loggers to DEBUG level
    prt_loggers = [
        'prt_src.llm_ollama',
        'prt_src.api',
        'prt_src.llm_memory',
        'prt_src.db'
    ]

    for logger_name in prt_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)

    # Create debug-specific log file
    debug_file = Path('prt_data/debug_llm_chaining.log')
    debug_file.parent.mkdir(exist_ok=True)

    debug_handler = logging.FileHandler(debug_file)
    debug_handler.setLevel(logging.DEBUG)

    debug_formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] [%(funcName)s:%(lineno)d] %(message)s'
    )
    debug_handler.setFormatter(debug_formatter)

    # Add to all loggers
    for logger_name in prt_loggers:
        logger = logging.getLogger(logger_name)
        logger.addHandler(debug_handler)
```

### 6. Usage Instructions

**Enable Debug Logging:**
```python
# Add to any script running the workflow
from prt_src.logging_config import configure_debug_logging
configure_debug_logging()
```

**Monitor Logs in Real-Time:**
```bash
# Terminal 1: General logs
tail -f prt_data/prt.log

# Terminal 2: Debug workflow logs
tail -f prt_data/debug_llm_chaining.log | grep -E "\[(TOOL_|MEMORY_|API_|CHAT_)\]"

# Terminal 3: Error-specific logs
tail -f prt_data/debug_llm_chaining.log | grep -E "\[ERROR\]|\[ZERO_LENGTH\]"
```

## Expected Debugging Output

With this instrumentation, a successful workflow should produce logs like:
```
[2024-11-03 13:45:22] [prt_src.llm_ollama] [INFO] [CHAT_START] User message: create directory of contacts with images
[2024-11-03 13:45:22] [prt_src.llm_ollama] [INFO] [TOOL_START] save_contacts_with_images(description='contacts with images')
[2024-11-03 13:45:22] [prt_src.api] [INFO] [API_QUERY_START] get_contacts_with_images() called
[2024-11-03 13:45:23] [prt_src.api] [INFO] [API_QUERY_SUCCESS] Retrieved 1,247 contacts in 0.045s
[2024-11-03 13:45:24] [prt_src.llm_memory] [INFO] [MEMORY_SAVE_SUCCESS] contacts_134523_a1b2c3d4 saved in 1.234s
[2024-11-03 13:45:24] [prt_src.llm_ollama] [INFO] [TOOL_RESPONSE] Returning success response
[2024-11-03 13:45:25] [prt_src.llm_ollama] [INFO] [TOOL_START] generate_directory(memory_id='contacts_134523_a1b2c3d4')
[2024-11-03 13:45:26] [prt_src.llm_ollama] [INFO] [CHAT_RESPONSE] Length: 156, preview: I've created a directory...
```

A failure will pinpoint exactly where the process breaks down.

## Next Steps

1. **Implement this instrumentation systematically**
2. **Test with real-world data**
3. **Analyze logs to identify failure point**
4. **Focus remediation on specific identified issue**

This comprehensive logging will reveal whether the issue is in data scale, binary data handling, memory operations, or LLM processing.