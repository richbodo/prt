# System Prompt Improvement Notes

This document captures opportunities to shorten and clarify the Ollama chat system prompt while keeping—or improving—its guidance for PRT's LLM assistant.

## Pain Points in the Current Prompt

1. **Redundant sections about the same policy** – Backup enforcement, SQL confirmation, and directory gating are repeated in multiple headings ("Critical Security Rules", "Usage Instructions", and "Important Reminders"), forcing the model to parse the same rule three times.【F:prt_src/llm_ollama.py†L917-L1060】【F:prt_src/llm_ollama.py†L1106-L1183】
2. **Overly long tool list** – Tools are described twice: once through `tools_description` and again in usage examples. The plain list lacks grouping context (e.g., search vs. maintenance) that could be expressed tersely via a table or bullets while relying on tool metadata for detail.【F:prt_src/llm_ollama.py†L902-L946】
3. **Narrative paragraphs that could be bulletized** – Sections like "ABOUT PRT" and "YOUR ROLE" devote multiple sentences to a single idea that could be conveyed with fewer, action-oriented bullets. The same idea (privacy, local data, TUI constraints) resurfaces later in "Response Style" and "Limitations".【F:prt_src/llm_ollama.py†L855-L933】【F:prt_src/llm_ollama.py†L1110-L1174】
4. **Static schema dump in the prompt** – Injecting `schema_info` balloons the prompt even though the schema rarely changes at runtime; the schema could be referenced from a smaller summary or an external tool help command. The current inline schema is long and duplicates documentation available through `get_database_schema`.【F:prt_src/llm_ollama.py†L910-L946】
5. **Example-heavy sections** – "Common Use Cases" and "SQL Optimization" embed numerous examples that overlap with user intent; replacing them with short patterns or references to docs would preserve capability with far fewer tokens.【F:prt_src/llm_ollama.py†L1048-L1158】

## Suggested Restructuring

1. **Condense repeated policies into a single "Safety Rules" block**
   - Merge backup, SQL confirmation, and directory rules into one numbered list covering "Always confirm SQL", "Write ops auto-backup", and "Never auto-generate directories". Refer back to it ("see Safety Rule #1") instead of repeating full prose.
   - Move the reminder bullets from "Important Reminders" under this section to eliminate duplication.

2. **Provide an at-a-glance command matrix instead of narrative use cases**
   - Replace the long "Common Use Cases" list with a compact table: *Intent* → *Preferred tool* → *Notes*. This keeps guidance but fits within ~8 rows.
   - Drop the repeated phrasing ("backup auto-created") because Safety Rule #2 already covers automatic backups.

3. **Summarize the schema**
   - Swap the full schema dump with a one-paragraph summary plus a note that `get_database_schema` returns authoritative details. Example: "Tables: contacts (core profile fields), tags/notes (linked via contact_metadata), contact_relationships/relationship_types (pairwise links)."
   - For fields the LLM must know (e.g., columns used in frequent filters), provide a short bullet list rather than full column tables.

4. **Surface tool context via categorization**
   - Use the existing tool metadata to generate a concise categorized bullet list (e.g., "Search: search_contacts, list_all_contacts"; "Mutate: add_tag_to_contact, remove_tag_from_contact"). The dynamic description can remain accessible through the built-in tool schema that models already read, reducing duplicate prose.

5. **Convert prose introductions into directives**
   - Rephrase "ABOUT PRT"/"YOUR ROLE" as imperative bullets ("Respect that all data is local"; "Keep responses short because the TUI scroll area is tight"; "Offer visualizations only when asked"). This shortens text while emphasizing actionable behavior.

6. **Trim example-heavy SQL guidance**
   - Retain only the five optimization heuristics as short bullet rules, removing the full SQL snippets. Mention that the `execute_sql` tool description already covers confirmation requirements.

7. **Link to external docs for depth**
   - Instead of embedding full backup and visualization walkthroughs, include a short pointer: "For full workflows see docs/LLM_Integration/tool_audit.md". This maintains discoverability without inflating the prompt.

## Implementation Approach

1. Update `_create_system_prompt` in `prt_src/llm_ollama.py` (and `llm_llamacpp.py`) to generate the streamlined structure above. Keep placeholders (`{tool_count}`, `{tools_description}`) but ensure they output categorized bullets.
2. Add regression coverage in `tests/integration/test_debug_info_command.py` to assert that the prompt stays under an agreed character budget (e.g., <8k chars) and still mentions critical rules (SQL confirmation, automatic backups, directory gating).
3. Document the new structure in `docs/LLM_Integration/README.md` so future contributors know where to add instructions without re-expanding the prompt.

These changes should cut the prompt length by more than half while reinforcing the behaviors that matter for safety and UX.
