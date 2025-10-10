# Chat Integration Documentation

**Complete guide to implementing the Chat screen as a conversational database interface**

This folder contains everything you need to understand, implement, test, and deploy the Chat screen for PRT. The documentation is organized sequentially - read in order for the full picture, or jump to specific sections as needed.

---

## 📚 Documentation Index

### Core Planning Documents (Read These First)

1. **[01_Architecture.md](./01_Architecture.md)** - System architecture and design decisions
   - High-level overview of components
   - Data flow diagrams
   - Key design principles
   - Context management strategy
   - Permission system

2. **[02_Configuration.md](./02_Configuration.md)** - LLM configuration and safeguards
   - Complete configuration schema
   - Permission controls (create/update/delete)
   - System prompt customization
   - Developer tools and debugging
   - Example configurations

3. **[03_Implementation_Plan.md](./03_Implementation_Plan.md)** - Phase-by-phase implementation guide
   - 7 phases from infrastructure to production
   - Estimated effort: 125-169 hours
   - Exit criteria for each phase
   - Risk mitigation strategy
   - Detailed task breakdowns

4. **[04_Testing_Strategy.md](./04_Testing_Strategy.md)** - Comprehensive testing approach
   - 4-layer testing pyramid
   - Fast feedback loop (< 6 seconds for 95% confidence)
   - Promptfoo integration for LLM validation
   - Test organization and CI setup

### Integration Guides

5. **[05_Ollama_Integration.md](./05_Ollama_Integration.md)** - Ollama setup and configuration
   - Installation and setup
   - Model management
   - Performance optimization
   - Troubleshooting

6. **[06_Contract_Testing.md](./06_Contract_Testing.md)** - LLM contract testing with promptfoo
   - Promptfoo setup and configuration
   - Test case design
   - Regression detection
   - Baseline establishment

---

## 🎯 Quick Start

### For Someone New to This Project

**Read in this order:**
1. Start with [01_Architecture.md](./01_Architecture.md) to understand the big picture
2. Review [03_Implementation_Plan.md](./03_Implementation_Plan.md) to see the roadmap
3. Scan [04_Testing_Strategy.md](./04_Testing_Strategy.md) to understand quality approach
4. Reference [02_Configuration.md](./02_Configuration.md) when implementing features

### For Someone Continuing Implementation

**Your starting checklist:**
1. Check which phase you're in (see [03_Implementation_Plan.md](./03_Implementation_Plan.md))
2. Review exit criteria for previous phase (did we complete it?)
3. Read tasks for current phase
4. Check configuration requirements in [02_Configuration.md](./02_Configuration.md)
5. Set up tests first (see [04_Testing_Strategy.md](./04_Testing_Strategy.md))

### For Someone Debugging Issues

**Quick references:**
1. [05_Ollama_Integration.md](./05_Ollama_Integration.md#troubleshooting) - Common Ollama issues
2. [02_Configuration.md](./02_Configuration.md#llm_developer-developer-tools) - Enable debug logging
3. [04_Testing_Strategy.md](./04_Testing_Strategy.md#layer-3-llm-contract-tests-promptfoo-) - Run contract tests
4. [01_Architecture.md](./01_Architecture.md#security--safety) - Safety controls

---

## 🏗️ What We're Building

### Vision

Transform the Chat screen into a **natural language database interface** where users can:
- Search: "show me tech contacts in San Francisco"
- Refine: "just the ones I haven't talked to in 6 months"
- Select: "select the first 5"
- Act: "export them for the directory maker"

All through natural conversation, with the same power and safety as structured operations.

### Key Principles

1. **LLM as Translator, Not Renderer**
   - LLM parses natural language → JSON commands
   - Code executes queries and formats results
   - No hallucinated data (LLM never makes up contacts/IDs)

2. **Token-Efficient Context Management**
   - Minimal context by default (~500 tokens)
   - Expand to detailed only when needed (~2000 tokens)
   - Adaptive switching based on query type

3. **Configurable Safety Controls**
   - Permission flags for create/update/delete
   - Confirmation dialogs for risky operations
   - Read-only mode for safe exploration
   - Audit logging for all LLM operations

4. **Fast Testing Feedback Loop**
   - 95% confidence from fast tests (< 6 seconds)
   - 5% confidence from slow tests (contract/E2E)
   - Mock LLM for rapid iteration
   - Real LLM validation with promptfoo

5. **Reusable Components**
   - Share formatters between Chat and Search screens
   - Common selection service (app-level)
   - Same workflow engine for both interfaces

---

## 📊 Implementation Status

**Current Phase**: Phase 0 (not yet started)

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 0 | 🔴 Not Started | Test infrastructure & configuration |
| Phase 1 | ⚪ Pending | Deterministic components (TDD) |
| Phase 2 | ⚪ Pending | LLM bridge with mocks |
| Phase 3 | ⚪ Pending | LLM contract testing (HIGH RISK) |
| Phase 4 | ⚪ Pending | Workflow implementation |
| Phase 5 | ⚪ Pending | Real LLM integration |
| Phase 6 | ⚪ Pending | Advanced features |
| Phase 7 | ⚪ Pending | Regression suite & docs |

**Update this section as you complete phases!**

---

## 🔑 Key Decisions from Planning Sessions

### Architectural Decisions

1. **LLM Role**: Translator only, not renderer
   - **Why**: Prevents hallucinations, token-efficient, testable
   - **Impact**: LLM returns JSON, code formats everything

2. **Context Strategy**: Adaptive (minimal/detailed based on query)
   - **Why**: Token efficiency without sacrificing capability
   - **Impact**: 500-1000 tokens per query vs 2000-4000 always

3. **Configuration**: JSON-based, developer-first
   - **Why**: Easy experimentation, version controllable
   - **Impact**: All settings in `prt_config.json`, not hardcoded

4. **Testing**: 4-layer pyramid (unit → integration → contract → E2E)
   - **Why**: Fast feedback (< 6s for 95% of tests)
   - **Impact**: Can iterate quickly, slow tests run rarely

5. **Permission System**: Configurable with confirmations
   - **Why**: Safety without rigidity
   - **Impact**: Developers can enable everything, users get safe defaults

### Risk Mitigation Decisions

1. **Test LLM Early** (Phase 3 before heavy dev)
   - **Why**: Validate parsing accuracy before building on it
   - **Impact**: May need to adjust approach if LLM fails

2. **Build Deterministic First** (Phase 1)
   - **Why**: Fast tests, no LLM dependency
   - **Impact**: Solid foundation, 90%+ test coverage

3. **Mock LLM for Integration** (Phase 2)
   - **Why**: Fast iteration without waiting for LLM
   - **Impact**: Can test workflows in seconds

4. **Promptfoo for Contracts** (Phase 3)
   - **Why**: Industry-standard tool for LLM testing
   - **Impact**: Regression detection, baseline tracking

---

## 💡 Common Questions

### "Where do I start?"

Phase 0 (Test Infrastructure & Configuration). See [03_Implementation_Plan.md](./03_Implementation_Plan.md#phase-0-test-infrastructure--configuration-setup-).

### "Can I skip the testing setup?"

No. The testing infrastructure is what makes this project feasible. Without it, you'll be waiting 30 seconds for every test run and won't catch regressions.

### "Why not use function calling instead of JSON commands?"

We may migrate to function calling later (Phase 6+), but JSON commands are simpler to implement and test initially. Function calling support in Ollama may not be mature enough yet.

### "How long will this take?"

125-169 hours total, spread over 8-12 weeks at 10-20 hours/week. See [03_Implementation_Plan.md](./03_Implementation_Plan.md#summary-total-effort-estimate).

### "What if the LLM can't parse accurately enough?"

That's why we test it early (Phase 3). If accuracy is < 95%, we'll iterate on the system prompt or reconsider the approach before building more.

### "Can users modify the system prompt?"

Yes, in dev mode (current). See [02_Configuration.md](./02_Configuration.md#3-llm_prompts-system-prompt-configuration). In the future, we'll have a "safe mode" with locked-down prompts.

---

## 🎓 Learning Resources

### Understanding the Architecture

- Read [01_Architecture.md](./01_Architecture.md) - Start here
- Review example conversations in Architecture doc
- Study the data flow diagrams

### Understanding the Testing Approach

- Read [04_Testing_Strategy.md](./04_Testing_Strategy.md)
- Review the test pyramid concept
- Understand why we use mocks for integration tests

### Understanding Promptfoo

- Read [06_Contract_Testing.md](./06_Contract_Testing.md)
- Visit [promptfoo.dev/docs](https://www.promptfoo.dev/docs/)
- Study example test cases in Contract Testing doc

### Understanding Ollama

- Read [05_Ollama_Integration.md](./05_Ollama_Integration.md)
- Visit [ollama.ai/docs](https://ollama.ai/docs)
- Review troubleshooting section

---

## 📋 Checklist for Picking Up Where You Left Off

1. **Review Status**
   - [ ] Check "Implementation Status" section above
   - [ ] Review commits since last session
   - [ ] Run existing tests to ensure baseline

2. **Understand Current Phase**
   - [ ] Read current phase in [03_Implementation_Plan.md](./03_Implementation_Plan.md)
   - [ ] Review exit criteria
   - [ ] Check what's already completed

3. **Set Up Environment**
   - [ ] Activate venv: `source ./init.sh`
   - [ ] Check Ollama is running: `curl http://localhost:11434/v1/models`
   - [ ] Run tests: `pytest -m unit && pytest -m integration`

4. **Review Recent Decisions**
   - [ ] Read "Key Decisions" section above
   - [ ] Check if any architectural changes occurred
   - [ ] Review any new risks or blockers

5. **Continue Work**
   - [ ] Start with current phase tasks
   - [ ] Write tests first (TDD)
   - [ ] Update "Implementation Status" as you complete tasks

---

## 🚀 Success Metrics

### Phase Completion Metrics

Track these as you complete each phase:

**Phase 0-3** (Foundation):
- ✅ All unit tests pass in < 1s
- ✅ All integration tests pass in < 5s
- ✅ LLM contract tests show 95%+ accuracy
- ✅ Configuration system loads and validates

**Phase 4-5** (Core Functionality):
- ✅ Critical workflows work end-to-end
- ✅ Response times < 30s for 90% of queries
- ✅ No critical bugs in manual testing
- ✅ Permission system prevents unintended modifications

**Phase 6-7** (Production Ready):
- ✅ All features implemented and tested
- ✅ Comprehensive regression suite (60+ tests)
- ✅ Performance benchmarks documented
- ✅ User and developer documentation complete

---

## 🤝 Contributing

When adding to this documentation:

1. **Keep it sequential** - Documents build on each other
2. **Update the index** - Add new docs to the index above
3. **Update status** - Keep "Implementation Status" current
4. **Cross-reference** - Link to related docs
5. **Add examples** - Code examples make it clearer

---

## 📝 Document History

| Date | Change | Author |
|------|--------|--------|
| 2025-01-10 | Created refactored documentation structure | Claude/rsb |
| 2025-01-10 | Consolidated planning from PR #126 | Claude/rsb |
| 2025-01-10 | Incorporated conversation context and decisions | Claude/rsb |

---

## 🔗 Related Documentation

**In this folder:**
- All numbered docs (01-06) for complete chat implementation

**Elsewhere in the project:**
- `../TUI/TUI_Specification.md` - Overall TUI spec
- `../TUI/TUI_Style_Guide.md` - Design principles
- `../TUI/TUI_Key_Bindings.md` - Key binding reference
- `../examples/prt_config_llm_settings.json` - Example configuration

**External resources:**
- [Promptfoo Documentation](https://www.promptfoo.dev/docs/)
- [Ollama Documentation](https://ollama.ai/docs)
- [Textual Documentation](https://textual.textualize.io/)

---

**Ready to start? Begin with [01_Architecture.md](./01_Architecture.md)!**
