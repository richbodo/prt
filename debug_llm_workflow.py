#!/usr/bin/env python3
"""
Debug script for LLM workflow troubleshooting.

This script enables comprehensive debug logging and then runs
the LLM workflow to identify zero-length response issues.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from prt_src.api import PRTAPI
from prt_src.llm_ollama import OllamaLLM
from prt_src.logging_config import configure_debug_logging


def test_workflow_with_debug():
    """Test the contacts with images workflow with comprehensive debug logging."""

    # Enable debug logging
    print("🔍 Enabling comprehensive debug logging...")
    configure_debug_logging()

    print("📁 Logs will be written to:")
    print("  - prt_data/prt.log (general log)")
    print("  - prt_data/debug_llm_chaining.log (workflow-specific log)")
    print()

    # Initialize API and LLM
    print("🔧 Initializing API and LLM...")
    api = PRTAPI()
    llm = OllamaLLM(api=api)

    # Test the workflow
    print("🚀 Testing: 'create a directory of contacts with images'")
    print("=" * 60)

    try:
        response = llm.chat("create a directory of contacts with images")

        print("📊 RESULT:")
        print(f"Response length: {len(response)}")
        if len(response) == 0:
            print("❌ ZERO-LENGTH RESPONSE DETECTED!")
        else:
            print("✅ Response received:")
            print(response[:500] + "..." if len(response) > 500 else response)

    except Exception as e:
        print(f"❌ Exception during workflow: {e}")
        import traceback

        traceback.print_exc()

    print("\n" + "=" * 60)
    print("🔍 Check the debug logs for detailed analysis:")
    print("  tail -f prt_data/debug_llm_chaining.log | grep -E '\\[(TOOL_|MEMORY_|API_|CHAT_)\\]'")


if __name__ == "__main__":
    test_workflow_with_debug()
