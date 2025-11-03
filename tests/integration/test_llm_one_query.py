"""Contract tests: Real LLM testing to validate tool calling functionality.

RECLASSIFIED: These tests were previously marked as integration tests but they:
1. Take 6-11+ seconds (violates < 5s integration test contract)
2. Require real LLM services (not deterministic)
3. Test actual end-to-end LLM behavior (contract validation)

They are now properly categorized as contract tests with timeout protection.
"""

import pytest
import requests

from prt_src.api import PRTAPI
from prt_src.llm_ollama import OllamaLLM
from tests.fixtures import get_fixture_spec


def is_ollama_available() -> bool:
    """Check if Ollama is running and available."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except (requests.RequestException, ConnectionError):
        return False


@pytest.mark.contract
@pytest.mark.requires_llm
@pytest.mark.timeout(300)
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
def test_count_contacts_integration(test_db):
    """Integration: 'How many contacts?' should return correct count.

    This is THE test - if this passes, tool calling works through our app.
    Uses fixture database and spec for expected values.
    """
    db, fixtures = test_db

    # Get fixture spec to know what to expect
    spec = get_fixture_spec()
    expected_count = spec["contacts"]["count"]

    print(f"\n[TEST] Fixture spec says: {expected_count} contacts")

    # Create PRTAPI with test database configuration
    test_config = {
        "db_path": str(db.path),
        "db_encrypted": False,
        "db_type": "sqlite",
    }
    api = PRTAPI(config=test_config)
    llm = OllamaLLM(api=api)

    # Verify database actually has the expected data
    all_contacts = api.list_all_contacts()
    actual_count = len(all_contacts)
    assert actual_count == expected_count, (
        f"Test setup problem: Database has {actual_count} contacts, "
        f"but spec says {expected_count}"
    )

    print(f"[TEST] Database verified: {actual_count} contacts")

    # Ask LLM the question
    print("[TEST] Asking LLM: 'How many contacts do I have?'")
    response = llm.chat("How many contacts do I have?")

    print(f"[TEST] LLM Response: {response}")

    # Verify response mentions the correct count
    # Accept both numeric and word forms (e.g., "7" or "seven")
    number_words = {
        1: "one",
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
        7: "seven",
        8: "eight",
        9: "nine",
        10: "ten",
    }
    expected_str = str(expected_count)
    expected_word = number_words.get(expected_count, expected_str)

    response_lower = response.lower()
    assert (
        expected_str in response or expected_word in response_lower
    ), f"Expected count {expected_count} (as '{expected_str}' or '{expected_word}') not found in response: {response}"

    print(f"[TEST] ✅ SUCCESS - Response contains correct count: {expected_count}")


@pytest.mark.contract
@pytest.mark.requires_llm
@pytest.mark.timeout(300)
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
def test_debug_tool_execution(test_db):
    """Debug test: Shows exactly what the LLM does with tools.

    Run with: pytest tests/integration/test_llm_one_query.py::test_debug_tool_execution -v -s
    Uses fixture database and spec.
    """
    db, fixtures = test_db

    # Get fixture spec
    spec = get_fixture_spec()
    expected_count = spec["contacts"]["count"]

    # Create PRTAPI with test database configuration
    test_config = {
        "db_path": str(db.path),
        "db_encrypted": False,
        "db_type": "sqlite",
    }
    api = PRTAPI(config=test_config)
    llm = OllamaLLM(api=api)

    print("\n" + "=" * 80)
    print("DEBUG: Tool Calling Test")
    print("=" * 80)

    print(f"\n[DEBUG] Using fixture database with {expected_count} contacts")
    print(f"[DEBUG] Registered tools: {[t.name for t in llm.tools]}")
    print(f"[DEBUG] System prompt preview:\n{llm._create_system_prompt()[:500]}...")

    print("\n[DEBUG] Sending query: 'How many contacts?'")
    response = llm.chat("How many contacts?")

    print(f"\n[DEBUG] Response: {response}")
    print(f"[DEBUG] Conversation history length: {len(llm.conversation_history)}")

    # Check conversation history for tool calls
    for i, msg in enumerate(llm.conversation_history):
        print(f"\n[DEBUG] Message {i}: role={msg['role']}")
        if "tool_calls" in msg:
            print(f"[DEBUG]   tool_calls: {msg['tool_calls']}")
        if msg["role"] == "tool":
            print(f"[DEBUG]   tool result: {msg.get('content', '')[:200]}...")

    print("\n" + "=" * 80)
