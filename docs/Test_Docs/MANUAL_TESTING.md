# Manual Testing Scenarios

**Last Updated**: 2025-10-14
**Philosophy**: Manual testing is the fallback when headless testing is impossible

---

## When Manual Testing Is Required

Manual testing should only be used when:
1. **Headless testing is technically impossible** (visual rendering, performance profiling)
2. **Cost-benefit doesn't justify automation** (one-time migration, rare edge case)
3. **Test requires human judgment** (accessibility, user experience)

**Before adding a manual test**: Try to write a headless test first. See `docs/TESTING_STRATEGY.md`.

---

## Manual Test Scenarios

### 1. Visual Regression

**Why Manual**: Headless tests can't validate colors, alignment, fonts, or responsive behavior.

**Scenarios**:
- [ ] Color scheme consistency across all screens
- [ ] Text alignment and padding in widgets
- [ ] Border rendering (no gaps or overlaps)
- [ ] Responsive layout at different terminal sizes
- [ ] Theme variable application (light/dark modes if implemented)

**Test Process**:
```bash
# Launch TUI
./prt_env/bin/python -m prt_src

# Navigate to each screen
# - Press 'n' to open menu
# - Navigate to: Home, Help, Chat, Search, Settings
# - For each screen:
#   1. Verify borders are clean (no gaps)
#   2. Verify text is readable and properly aligned
#   3. Verify colors match design (use theme variables)
#   4. Resize terminal (Cmd+Plus/Minus on Mac) and verify layout adapts
```

**Expected Results**:
- No visual artifacts (border gaps, overlapping widgets)
- Consistent color scheme across all screens
- Text readable at minimum terminal size (80x24)
- Layout doesn't break at maximum terminal size

---

### 2. Performance Testing

**Why Manual**: Automated tests in CI don't have stable performance metrics.

**Scenarios**:
- [ ] Large dataset handling (5000+ contacts)
- [ ] Search response time (< 100ms for local search)
- [ ] LLM response time (acceptable for user)
- [ ] Memory usage (no leaks during extended use)
- [ ] TUI render time (< 16ms per frame for smooth 60fps)

**Test Process**:
```bash
# Create large dataset
./prt_env/bin/python -c "
from prt_src.db import create_database
from tests.fixtures import SAMPLE_CONTACTS
from prt_src.models import Contact
from pathlib import Path

db = create_database(Path('prt_data/perf_test.db'))
db.initialize()

# Create 5000 contacts
for i in range(5000):
    contact = Contact(
        name=f'Test Contact {i}',
        email=f'test{i}@example.com'
    )
    db.session.add(contact)

db.session.commit()
print(f'Created {db.count_contacts()} contacts')
"

# Launch TUI with large dataset
./prt_env/bin/python -m prt_src

# Test performance
# 1. Navigate to Search screen
# 2. Type a search query and measure response time
# 3. Scroll through results and verify smoothness
# 4. Open Chat screen
# 5. Ask "How many contacts do I have?" and measure LLM response time
# 6. Monitor memory usage (Activity Monitor on Mac, Task Manager on Windows)
```

**Expected Results**:
- Search results appear in < 100ms
- Scrolling is smooth (no visible stuttering)
- LLM responses arrive within expected time (10-30s for local model)
- Memory usage stays stable (no growth over time)
- Memory usage < 200MB for 5000 contacts

---

### 3. Accessibility Testing

**Why Manual**: Requires screen readers and keyboard-only navigation validation.

**Scenarios**:
- [ ] Keyboard-only navigation (no mouse required)
- [ ] Screen reader compatibility (VoiceOver on Mac, NVDA on Windows)
- [ ] Color contrast (WCAG AA minimum for text)
- [ ] Focus indicators (visible focus on current widget)

**Test Process**:
```bash
# Launch TUI
./prt_env/bin/python -m prt_src

# Keyboard-only navigation
# 1. Don't use mouse at all
# 2. Use Tab/Shift+Tab to move focus
# 3. Use Enter to activate buttons
# 4. Use arrow keys for navigation
# 5. Verify all features are accessible

# Screen reader testing (Mac)
# 1. Enable VoiceOver (Cmd+F5)
# 2. Navigate TUI with keyboard
# 3. Verify screen reader announces:
#    - Current screen name
#    - Current widget/button
#    - Available actions
#    - Error messages
```

**Expected Results**:
- All features accessible via keyboard only
- Tab order is logical (top-to-bottom, left-to-right)
- Focus indicators are clearly visible
- Screen reader announces all relevant information
- No keyboard traps (can always navigate away)

---

### 4. Platform-Specific Testing

**Why Manual**: Different terminals have different rendering capabilities.

**Scenarios**:
- [ ] iTerm2 (Mac) - primary development environment
- [ ] Terminal.app (Mac) - macOS default
- [ ] Windows Terminal (Windows)
- [ ] GNOME Terminal (Linux)
- [ ] tmux/screen compatibility

**Test Process**:
For each terminal:
```bash
# Launch TUI
./prt_env/bin/python -m prt_src

# Verify rendering
# 1. Check borders render correctly
# 2. Check colors display correctly
# 3. Check special characters (✓, ✗, →, etc.) render
# 4. Test screen resizing
# 5. Test copy/paste (if applicable)
```

**Expected Results**:
- TUI renders correctly in all tested terminals
- Colors match across terminals (accounting for terminal color schemes)
- Unicode characters render or have ASCII fallback
- Resizing works smoothly without artifacts

---

### 5. Error Recovery Testing

**Why Manual**: Complex error scenarios are hard to automate.

**Scenarios**:
- [ ] Database corruption recovery
- [ ] Network failure during LLM call
- [ ] Disk full during export
- [ ] Interrupted import process
- [ ] Permission denied errors
- [ ] Invalid configuration file

**Test Process**:
```bash
# Test database corruption recovery
# 1. Copy production database to backup
cp prt_data/prt.db prt_data/prt.db.backup

# 2. Corrupt database (delete some bytes)
dd if=/dev/zero of=prt_data/prt.db bs=1024 count=1 seek=100 conv=notrunc

# 3. Launch TUI
./prt_env/bin/python -m prt_src

# 4. Verify error handling:
#    - Clear error message displayed
#    - Recovery instructions provided
#    - Can restore from backup
```

**Expected Results**:
- Clear error messages (no stack traces to user)
- Recovery instructions provided
- User can continue or exit gracefully
- No data loss (backups available)

---

### 6. Complex User Workflows

**Why Manual**: Multi-step flows with decision points are complex to automate.

**Scenarios**:
- [ ] Import → Review → Accept/Reject → Merge duplicates → Export
- [ ] Search → Select → Bulk tag → Verify → Export directory
- [ ] Setup wizard → Configure encryption → Import data → Verify
- [ ] Chat → Search → Refine → Select → Export → Verify results

**Test Process**:
```bash
# Example: Import workflow
./prt_env/bin/python -m prt_src.cli --classic

# 1. Import Google Takeout export
# 2. Review imported contacts
# 3. Accept/reject suggested merges
# 4. Tag imported contacts
# 5. Export directory
# 6. Verify exported HTML directory
```

**Expected Results**:
- Workflow completes successfully
- User can navigate back/cancel at any step
- Progress is preserved (no data loss if interrupted)
- Final result matches expectations

---

### 7. LLM Conversation Quality

**Why Manual**: Requires human judgment of response quality.

**Scenarios**:
- [ ] Chat understands natural language queries
- [ ] Chat provides helpful responses (not just correct)
- [ ] Chat handles ambiguous queries gracefully
- [ ] Chat conversation maintains context
- [ ] Chat handles errors with clear explanations

**Test Process**:
```bash
# Launch chat
./prt_env/bin/python -m prt_src.cli chat --debug

# Test conversational queries
# 1. "How many contacts do I have?" (simple count)
# 2. "Who are my contacts in tech?" (filtered search)
# 3. "Show me contacts without email" (negative filter)
# 4. "Can you find Alice's phone number?" (specific info)
# 5. "What was that first contact's email?" (context reference)
```

**Expected Results**:
- Responses are factually correct
- Responses are helpful (not just "7 contacts" but "You have 7 contacts")
- Ambiguous queries prompt clarification
- Context is maintained across conversation
- Errors explained clearly ("I don't have access to phone numbers")

---

### 8. Debug Mode Testing

**Why Manual**: Debug features are for development and not fully automated.

**Scenarios**:
- [ ] Debug mode creates fixture database
- [ ] Debug mode uses fixture database (not production)
- [ ] Fixture regeneration works correctly
- [ ] Enhanced logging is visible in prt_data/prt.log
- [ ] Debug mode doesn't affect production data

**Test Process**:
```bash
# Test debug mode
./prt_env/bin/python -m prt_src --debug --regenerate-fixtures

# Verify:
# 1. prt_data/debug.db created (not prt.db)
# 2. Fixture data loaded (7 contacts with known names)
# 3. Chat queries use debug database
# 4. Logs show DEBUG level messages
# 5. Production database untouched (prt_data/prt.db unchanged)

# Test without regeneration
./prt_env/bin/python -m prt_src --debug

# Verify:
# 1. Existing debug.db reused (no regeneration)
# 2. Message displayed: "Using existing debug database"
```

**Expected Results**:
- Debug database isolated from production
- Fixture data consistent (7 contacts, 8 tags, 6 notes)
- Debug logging enabled and visible
- Production data never touched by debug mode

---

## Release Testing Checklist

Before releasing a new version, run through this checklist:

### Pre-Release
- [ ] All automated tests pass (unit + integration)
- [ ] Linting passes (ruff + black)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated

### Visual Testing
- [ ] All screens render correctly (Home, Help, Chat, Search, Settings)
- [ ] Colors and borders consistent
- [ ] Responsive layout works at various terminal sizes

### Performance Testing
- [ ] Large dataset handling (5000+ contacts)
- [ ] Search response time acceptable
- [ ] Memory usage stable

### Platform Testing
- [ ] Tested on macOS (iTerm2 + Terminal.app)
- [ ] Tested on Windows (Windows Terminal) if applicable
- [ ] Tested on Linux (GNOME Terminal) if applicable

### User Workflows
- [ ] Setup wizard works for new users
- [ ] Import workflow (Google Takeout)
- [ ] Search and export workflow
- [ ] Chat functionality with LLM

### Error Handling
- [ ] Graceful degradation when LLM unavailable
- [ ] Clear error messages for common failures
- [ ] Recovery instructions provided

---

## Reporting Manual Test Results

When performing manual tests, document results:

```markdown
# Manual Test Report: [Feature Name]
**Date**: 2025-10-14
**Tester**: [Name]
**Environment**: macOS 14.0, iTerm2 3.4.19, Python 3.11.9

## Tests Performed
- [x] Visual regression: Home screen
- [x] Visual regression: Chat screen
- [ ] Performance: Large dataset (5000 contacts) - SKIPPED

## Results
### Visual Regression - Home Screen
- ✅ PASS: Borders render correctly
- ✅ PASS: Colors consistent with theme
- ⚠️ MINOR: Focus indicator slightly dim (low priority)

### Visual Regression - Chat Screen
- ✅ PASS: Chat history scrolls smoothly
- ❌ FAIL: Progress indicator has border gap
  - Screenshot: [link]
  - Bug filed: #135

## Summary
- 4/5 tests passed
- 1 bug found (border gap in progress indicator)
- 1 minor issue (focus indicator dim)
- 1 test skipped (large dataset)
```

Save reports in `docs/test_reports/manual_YYYY-MM-DD.md`.

---

## Reducing Manual Testing Over Time

As the project matures, work to convert manual tests to automated:

1. **Visual regression**: Consider Playwright + screenshot comparison
2. **Performance**: Add CI performance benchmarks with stable environment
3. **Platform testing**: Add CI matrix for multiple OS/terminal combinations
4. **Error recovery**: Mock error scenarios in integration tests

**Goal**: Minimize manual testing burden while maintaining quality.

---

## Questions?

If this document doesn't cover your manual testing scenario:
1. Consider if headless testing is actually possible
2. Propose an addition to this document
3. Document your test process for future reference
