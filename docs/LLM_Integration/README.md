# LLM Integration - Simplified Approach

**Start Date:** October 10, 2025
**Philosophy:** Start with absolute minimum, grow based on evidence

## Current Status: Phase 0 - Restoration

We're restoring the **working system prompt** from commit a074dd2 that successfully used tool calling for basic contact queries.

### What We Have (Already Working)

✅ **OllamaLLM class** (`prt_src/llm_ollama.py`) with:
- Tool calling infrastructure
- Conversation history management
- Error handling
- Working system prompt (the old one!)

✅ **15 tools defined** including:
- `search_contacts(query)` - Returns full contact details
- `list_all_contacts()`
- `get_contact_details(contact_id)`
- And 12 others...

✅ **PRTAPI** that returns comprehensive contact data

### What We're Going to Do

**Phase 1: Prove 1 tool works (This Week)**
- Simplify from 15 tools to 1 tool: `search_contacts(query)`
- Test manually with 10 different queries
- Document what works and what doesn't
- **Time: 6-8 hours**

**Phase 2: Add reliability (Next Week)**
- Only if Phase 1 works well
- Add testing with promptfoo
- Add structured validation if needed
- Measure accuracy
- **Time: 16-20 hours**

**Phase 3: Expand (Only if metrics show gaps)**
- Add tools ONLY for observed needs
- Not speculative
- **Time: TBD based on Phase 2 results**

## Key Principles

1. **Start with 1 tool, not 15** - Simplify first
2. **Tools ARE intents** - Don't build separate intent system
3. **Test before building** - Manual testing, then automated
4. **Measure before modifying** - Let evidence drive decisions
5. **The "10x rule"** - Each sophistication level costs 10x more effort

## Architecture (Minimal)

Three components, no more:

1. **Direct Model Access** - OllamaLLM (already have)
2. **Clear System Prompt** - Simple prompt with examples (already have)
3. **Basic Orchestration** - Call model → Execute tool → Return response (already have)

That's it. Everything else is optional optimization.

## External References

Three documents guided this approach:
- `EXTERNAL_DOCS/Model_Tips/How_to_architect_llm_systems.txt`
- `EXTERNAL_DOCS/Model_Tips/building_reliable_llm_db_systems.md`
- `EXTERNAL_DOCS/Model_Tips/tech_docs_for_oss20b.md`

All three emphasize: **Start simple, grow deliberately, measure constantly.**

## Next Steps

1. ✅ Archive old Chat_Integration docs (DONE)
2. ✅ Verify system prompt is the working one (DONE - it is!)
3. ⏭️ Simplify to 1 tool
4. ⏭️ Manual testing
5. ⏭️ Document results

---

**Last Updated:** October 10, 2025
