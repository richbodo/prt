# Bug: test_llm_phase4_tools.py::TestLLMPhase4Tools::test_generate_directory failing due to incorrect field names

## Bug Description
The test `tests/integration/test_llm_phase4_tools.py::TestLLMPhase4Tools::test_generate_directory` is failing because it expects a field named `contacts_count` (plural) in the return value from the `generate_directory` tool, but the implementation returns `contact_count` (singular). This causes an AssertionError when the test checks for the existence of the `contacts_count` field.

The test failure shows:
```
AssertionError: assert 'contacts_count' in {'success': True, 'output_path': '/Users/richardbodo/src/prt/directories/test_directory', 'url': 'file:///Users/richardbodo/src/prt/directories/test_directory/index.html', 'contact_count': 1}
```

The same issue occurs in a second test method `test_generate_directory_with_search_query` that also expects `contacts_count`.

## Problem Statement
The test code was written with inconsistent field naming that doesn't match the documented schema and implementation. The tests expect `contacts_count` (plural) but the implementation correctly returns `contact_count` (singular) according to the JSON export schema documentation.

## Solution Statement
Fix the test code to expect the correct field name `contact_count` (singular) instead of `contacts_count` (plural) to align with the documented schema and implementation. This is a minimal change that corrects the test to match the actual API contract.

## Steps to Reproduce
1. Run the failing test: `./prt_env/bin/pytest tests/integration/test_llm_phase4_tools.py::TestLLMPhase4Tools::test_generate_directory -v`
2. Observe the AssertionError showing that `contacts_count` is not in the returned dictionary
3. Note that `contact_count` (singular) is present in the returned dictionary

## Root Cause Analysis
The root cause is a naming inconsistency between the test expectations and the implementation/documentation:

1. **Documentation**: `docs/Database/JSON_EXPORT_SCHEMA.md` shows the correct field name is `contact_count` (singular) on line 93
2. **Implementation**: `prt_src/llm_ollama.py` line 810 correctly returns `contact_count` (singular)
3. **Test Code**: `tests/integration/test_llm_phase4_tools.py` lines 134 and 163 incorrectly expect `contacts_count` (plural)

The implementation follows the documented schema, so the test code needs to be corrected to match the documented API contract.

## Relevant Files
Use these files to fix the bug:

- `tests/integration/test_llm_phase4_tools.py` - Contains the failing test assertions that expect `contacts_count` instead of `contact_count`. Lines 134 and 163 need to be updated.
- `docs/Database/JSON_EXPORT_SCHEMA.md` - Documents the correct field naming convention as `contact_count` (singular). This confirms the implementation is correct.
- `prt_src/llm_ollama.py` - Contains the correct implementation that returns `contact_count`. This file validates our understanding of the expected behavior.

## Step by Step Tasks

### Fix Test Field Names
- Update line 134 in `tests/integration/test_llm_phase4_tools.py` from `assert "contacts_count" in result` to `assert "contact_count" in result`
- Update line 135 in `tests/integration/test_llm_phase4_tools.py` from `assert result["contacts_count"] > 0` to `assert result["contact_count"] > 0`
- Update line 163 in `tests/integration/test_llm_phase4_tools.py` from `assert result["contacts_count"] >= 1` to `assert result["contact_count"] >= 1`

### Validate Fix with Tests
- Run the specific failing test to ensure it now passes
- Run all related tests to ensure no regressions
- Verify the test correctly validates the directory generation functionality

## Validation Commands
Execute every command to validate the bug is fixed with zero regressions.

- `source ./init.sh` - Ensure environment is properly set up
- `./prt_env/bin/pytest tests/integration/test_llm_phase4_tools.py::TestLLMPhase4Tools::test_generate_directory -v` - Run the specific failing test to verify it now passes
- `./prt_env/bin/pytest tests/integration/test_llm_phase4_tools.py::TestLLMPhase4Tools::test_generate_directory_with_search_query -v` - Run the second affected test to verify it now passes
- `./prt_env/bin/pytest tests/integration/test_llm_phase4_tools.py -v` - Run all tests in the class to ensure no other regressions
- `./prt_env/bin/pytest tests/integration/ -v` - Run all integration tests to validate broader system compatibility

## Notes
- This is a simple field naming fix that aligns the test with the documented API schema
- The implementation was already correct according to the JSON export schema documentation
- The directory generation functionality is working properly; only the test assertions were incorrect
- This fix ensures consistency between tests, implementation, and documentation