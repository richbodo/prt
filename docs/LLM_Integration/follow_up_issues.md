# Follow-up issues for disabled LLM tools

## `save_contacts_with_images`
- **Status:** Disabled by default via `llm_tools.disabled` until workflow stability is proven.【F:prt_src/config.py†L10-L18】【F:prt_src/config.py†L362-L377】  The Ollama runtime logs the removal when it loads.【F:prt_src/llm_ollama.py†L82-L90】
- **Reproduction steps:**
  1. Temporarily enable the tool by providing a config override, e.g. `LLMConfigManager({"llm_tools": {"disabled": []}})`, then instantiate `OllamaLLM`.
  2. Run the memory-chain integration tests to exercise the full save/list workflow:
     ```bash
     pytest tests/test_llm_memory_chaining.py::test_save_contacts_with_images_tool -q
     pytest tests/test_llm_memory_chaining.py::test_generate_directory_with_memory_id -q
     ```
     【F:tests/test_llm_memory_chaining.py†L39-L138】
- **Desired fixes:** Add an automated chat-level test that covers the two-step directory generation path, document the feature in `docs/LLM_Integration/README.md`, and ensure the system prompt instructions are reinstated once stability is confirmed.

## `list_memory`
- **Status:** Disabled alongside the memory-saving tool because it depends on the same storage workflow.【F:prt_src/config.py†L10-L18】【F:prt_src/config.py†L362-L377】【F:prt_src/llm_ollama.py†L82-L90】
- **Reproduction steps:**
  1. Enable the tool with the same config override described above.
  2. Execute the listing integration test to confirm expected payloads:
     ```bash
     pytest tests/test_llm_memory_chaining.py::test_list_memory_tool -q
     ```
     【F:tests/test_llm_memory_chaining.py†L71-L99】
- **Desired fixes:** Provide direct LLM prompting coverage that lists saved results, audit expiry/cleanup behaviour, and update user-facing docs once reliability is demonstrated.

Re-enable each tool by removing it from the disabled list only after the above validation and documentation tasks are complete.

