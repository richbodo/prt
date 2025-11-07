# LLM Tool Audit

This report inventories the 24 tools documented in `docs/LLM_Integration/README.md`, notes their runtime dependencies, and links existing automated coverage. It also highlights safety behaviour, manual smoke procedures for lightly tested areas, and the temporary feature flags introduced in this audit.

## Tool matrix

| Tool | Scope | Dependencies | Current automated coverage |
| --- | --- | --- | --- |
| `search_contacts` | Read | Mapped to `PRTAPI.search_contacts` for contact lookups.【F:prt_src/llm_ollama.py†L304-L318】【F:prt_src/api.py†L298-L322】 | API regression test plus CLI export workflow cover typical usage.【F:tests/test_api.py†L26-L35】【F:tests/test_cli.py†L120-L156】 |
| `list_all_contacts` | Read | Directly calls `PRTAPI.list_all_contacts` to enumerate contacts.【F:prt_src/llm_ollama.py†L320-L335】【F:prt_src/api.py†L713-L719】 | API test verifies payload structure for the full contact list.【F:tests/test_api.py†L120-L135】 |
| `list_all_tags` | Read | Uses `PRTAPI.list_all_tags` for aggregate tag data.【F:prt_src/llm_ollama.py†L325-L330】【F:prt_src/api.py†L593-L599】 | API test exercises tag listing and schema.【F:tests/test_api.py†L136-L148】 |
| `list_all_notes` | Read | Routes through `PRTAPI.list_all_notes` for note summaries.【F:prt_src/llm_ollama.py†L331-L336】【F:prt_src/api.py†L631-L644】 | API test covers list output and fields.【F:tests/test_api.py†L150-L158】 |
| `get_database_stats` | Read | Calls `PRTAPI.get_database_stats` for aggregate counts.【F:prt_src/llm_ollama.py†L337-L341】【F:prt_src/api.py†L66-L71】 | API smoke test and LLM integration fixture confirm behaviour.【F:tests/test_api.py†L26-L35】【F:tests/integration/test_llm_write_tools.py†L329-L336】 |
| `get_contact_details` | Read | Delegates to `PRTAPI.get_contact_details` for per-contact data.【F:prt_src/llm_ollama.py†L353-L365】【F:prt_src/api.py†L694-L711】 | Core operations unit test validates rich contact payloads.【F:tests/test_core_operations.py†L192-L207】 |
| `search_tags` | Read | Uses `PRTAPI.search_tags` for tag queries.【F:prt_src/llm_ollama.py†L368-L377】【F:prt_src/api.py†L323-L332】 | CLI export test covers end-to-end tag search usage.【F:tests/test_cli.py†L159-L202】 |
| `search_notes` | Read | Uses `PRTAPI.search_notes` for note queries.【F:prt_src/llm_ollama.py†L380-L392】【F:prt_src/api.py†L333-L352】 | CLI export test exercises note search workflow.【F:tests/test_cli.py†L205-L220】 |
| `get_contacts_by_tag` | Read | Relies on `PRTAPI.get_contacts_by_tag` to expand tag matches.【F:prt_src/llm_ollama.py†L395-L407】【F:prt_src/api.py†L485-L509】 | CLI export scenario fetches tagged contacts for validation.【F:tests/test_cli.py†L167-L202】 |
| `get_contacts_by_note` | Read | Calls `PRTAPI.get_contacts_by_note` for note associations.【F:prt_src/llm_ollama.py†L409-L422】【F:prt_src/api.py†L511-L535】 | CLI export test loads contacts linked to selected notes.【F:tests/test_cli.py†L205-L220】 |
| `add_tag_to_contact` | Write | Wraps `PRTAPI.add_tag_to_contact`; backup wrapper now reports failures accurately.【F:prt_src/llm_ollama.py†L428-L446】【F:prt_src/llm_ollama.py†L1350-L1414】【F:prt_src/api.py†L542-L548】 | Integration test asserts backups and result contract.【F:tests/integration/test_llm_write_tools.py†L14-L59】 |
| `remove_tag_from_contact` | Write | Uses `PRTAPI.remove_tag_from_contact` with automatic backups.【F:prt_src/llm_ollama.py†L447-L458】【F:prt_src/llm_ollama.py†L1350-L1414】【F:prt_src/api.py†L550-L565】 | Integration coverage now checks failure propagation and backups.【F:tests/integration/test_llm_write_tools.py†L60-L118】【F:tests/integration/test_llm_write_tools.py†L294-L316】 |
| `create_tag` | Write | Calls `PRTAPI.create_tag` and benefits from backup safety.【F:prt_src/llm_ollama.py†L460-L470】【F:prt_src/llm_ollama.py†L1350-L1414】【F:prt_src/api.py†L600-L613】 | Integration suite verifies backup metadata for tag creation.【F:tests/integration/test_llm_write_tools.py†L119-L148】 |
| `delete_tag` | Write | Invokes `PRTAPI.delete_tag` with automatic backups.【F:prt_src/llm_ollama.py†L471-L482】【F:prt_src/llm_ollama.py†L1350-L1414】【F:prt_src/api.py†L615-L629】 | Integration test checks destructive tag removal workflow.【F:tests/integration/test_llm_write_tools.py†L149-L193】 |
| `add_note_to_contact` | Write | Uses `PRTAPI.add_note_to_contact` for relationship notes.【F:prt_src/llm_ollama.py†L487-L500】【F:prt_src/llm_ollama.py†L1350-L1414】【F:prt_src/api.py†L567-L573】 | Integration test confirms backup creation for note addition.【F:tests/integration/test_llm_write_tools.py†L194-L218】 |
| `remove_note_from_contact` | Write | Calls `PRTAPI.remove_note_from_contact` with backup guard.【F:prt_src/llm_ollama.py†L501-L516】【F:prt_src/llm_ollama.py†L1350-L1414】【F:prt_src/api.py†L575-L590】 | Integration test ensures removal triggers safety backup.【F:tests/integration/test_llm_write_tools.py†L164-L191】 |
| `create_note` | Write | Writes through `PRTAPI.create_note` under backup supervision.【F:prt_src/llm_ollama.py†L517-L528】【F:prt_src/llm_ollama.py†L1350-L1414】【F:prt_src/api.py†L646-L664】 | Integration test validates creation semantics and backup metadata.【F:tests/integration/test_llm_write_tools.py†L193-L218】 |
| `update_note` | Write | Uses `PRTAPI.update_note` to modify content safely.【F:prt_src/llm_ollama.py†L531-L542】【F:prt_src/llm_ollama.py†L1350-L1414】【F:prt_src/api.py†L666-L676】 | Integration test exercises update flow and backup logging.【F:tests/integration/test_llm_write_tools.py†L219-L246】 |
| `delete_note` | Write | Calls `PRTAPI.delete_note` with automatic safety backup.【F:prt_src/llm_ollama.py†L543-L553】【F:prt_src/llm_ollama.py†L1350-L1414】【F:prt_src/api.py†L678-L692】 | Integration test covers destructive deletion path.【F:tests/integration/test_llm_write_tools.py†L247-L273】 |
| `create_backup_with_comment` | Write | Direct call to `PRTAPI.create_backup_with_comment` for manual snapshots.【F:prt_src/llm_ollama.py†L558-L571】【F:prt_src/api.py†L81-L99】 | Integration test verifies manual backup creation via tool call.【F:tests/integration/test_llm_write_tools.py†L317-L347】 |
| `execute_sql` | Read/Write (guarded) | Routed through `_execute_sql_safe`, which validates and delegates to `PRTAPI.execute_sql` with backup-on-write semantics.【F:prt_src/llm_ollama.py†L577-L598】【F:prt_src/llm_ollama.py†L800-L872】【F:prt_src/api.py†L163-L211】 | Phase 4 integration tests cover confirmation, read, and write flows plus error handling.【F:tests/integration/test_llm_phase4_tools.py†L25-L104】 |
| `generate_directory` | Write (filesystem) | Executes `_generate_directory`, which orchestrates data pulls and D3 generation.【F:prt_src/llm_ollama.py†L633-L654】【F:prt_src/llm_ollama.py†L972-L1347】 | Phase 4 integration tests validate success, filtering, and no-result handling.【F:tests/integration/test_llm_phase4_tools.py†L105-L184】 |
| `add_contact_relationship` | Write | Uses `PRTAPI.add_contact_relationship` with new backup propagation logic.【F:prt_src/llm_ollama.py†L675-L697】【F:prt_src/llm_ollama.py†L1350-L1414】【F:prt_src/api.py†L932-L1001】 | Phase 4 integration test ensures backup metadata and error handling.【F:tests/integration/test_llm_phase4_tools.py†L186-L236】 |
| `remove_contact_relationship` | Write | Calls `PRTAPI.remove_contact_relationship` with safety wrapper.【F:prt_src/llm_ollama.py†L698-L709】【F:prt_src/llm_ollama.py†L1350-L1414】【F:prt_src/api.py†L1003-L1066】 | Phase 4 integration test checks removal backups and messaging.【F:tests/integration/test_llm_phase4_tools.py†L236-L276】 |

> **Note:** The runtime currently exposes four additional helpers (`get_database_schema`, `get_contacts_with_images`, `save_contacts_with_images`, `list_memory`). Two of them are feature-flagged off by default—see the “Disabled tools” section below.

## Logging, backups, and error handling verification

* All write tools run through `_safe_write_wrapper`, which now inspects the underlying API response and surfaces failures instead of always returning `success=True`, while still reporting the pre-operation backup ID for auditing.【F:prt_src/llm_ollama.py†L1350-L1414】
* The API endpoints invoked by write tools rely on `PRTAPI.auto_backup_before_operation` when applicable (e.g., SQL writes) or perform direct SQLAlchemy commits with logging and rollback on error.【F:prt_src/api.py†L163-L211】【F:prt_src/api.py†L542-L692】【F:prt_src/api.py†L932-L1066】
* `OllamaLLM` logs when configuration disables tools so operators can trace capability changes in the standard log stream.【F:prt_src/llm_ollama.py†L82-L90】

## Manual smoke scripts for lightly covered tools

Run these commands from the repository root to exercise read-only queries that only have indirect coverage:

1. Fetch contacts associated with a tag and confirm empty/error handling:
   ```bash
   python -m prt_src.llm_commands get_contacts_by_tag "friend"
   python -m prt_src.llm_commands get_contacts_by_tag "nonexistent-tag"
   ```
   【F:prt_src/llm_commands.py†L37-L45】
2. Inspect note associations to ensure note titles with no matches behave gracefully:
   ```bash
   python -m prt_src.llm_commands get_contacts_by_note "Weekly Meeting"
   python -m prt_src.llm_commands get_contacts_by_note "missing-note-title"
   ```
   【F:prt_src/llm_commands.py†L42-L45】
3. Review contact detail responses and integer parsing edge cases:
   ```bash
   python -m prt_src.llm_commands get_contact_details 1
   python -m prt_src.llm_commands get_contact_details 999
   ```
   【F:prt_src/llm_commands.py†L47-L50】

Each command returns JSON output, making it easy to diff results between typical queries and edge cases.

## Disabled tools and follow-up

Two helper tools remain disabled by default via the new `llm_tools.disabled` flag because they extend beyond the Phase 4 scope and require additional reliability work before being exposed in the dynamic tool prompt:

* `save_contacts_with_images`
* `list_memory`

They are excluded through the default configuration list and logged at runtime.【F:prt_src/config.py†L10-L18】【F:prt_src/config.py†L362-L377】【F:prt_src/llm_ollama.py†L82-L90】 Dedicated follow-up items outlining the validation and documentation work needed to re-enable them live in [`docs/LLM_Integration/follow_up_issues.md`](follow_up_issues.md).

