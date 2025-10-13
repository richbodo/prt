"""Integration test: ONE query to prove tool calling works.

This tests the actual app code (OllamaLLM.chat) rather than raw Ollama API.
If this passes, tool calling works. If it fails, we have a real problem.
"""

import pytest

from prt_src.api import PRTAPI
from prt_src.llm_ollama import OllamaLLM


@pytest.mark.integration
def test_count_contacts_integration():
    """Integration: 'How many contacts?' should return correct count.

    This is THE test - if this passes, tool calling works through our app.
    """
    # Create real instances (uses test database from fixtures)
    api = PRTAPI()
    llm = OllamaLLM(api=api)

    # Get actual contact count from database
    all_contacts = api.list_all_contacts()
    expected_count = len(all_contacts)

    print(f"\n[TEST] Database has {expected_count} contacts")

    # Ask LLM the question
    print("[TEST] Asking LLM: 'How many contacts do I have?'")
    response = llm.chat("How many contacts do I have?")

    print(f"[TEST] LLM Response: {response}")

    # Verify response mentions the correct count
    # We're lenient - just check if the number appears ANYWHERE in response
    assert (
        str(expected_count) in response
    ), f"Expected count {expected_count} not found in response: {response}"

    print(f"[TEST] ✅ SUCCESS - Response contains correct count: {expected_count}")


@pytest.mark.integration
def test_debug_tool_execution():
    """Debug test: Shows exactly what the LLM does with tools.

    Run with: pytest tests/integration/test_llm_one_query.py::test_debug_tool_execution -v -s
    """
    api = PRTAPI()
    llm = OllamaLLM(api=api)

    print("\n" + "=" * 80)
    print("DEBUG: Tool Calling Test")
    print("=" * 80)

    print(f"\n[DEBUG] Registered tools: {[t.name for t in llm.tools]}")
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
