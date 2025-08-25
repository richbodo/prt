#!/usr/bin/env python3
"""
Example script demonstrating Ollama integration with PRT.

This script shows how to use the Ollama LLM with tool calling
to interact with your PRT contacts and relationships.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prt.config import load_config
from prt.api import PRTAPI
from prt.llm_ollama import OllamaLLM, chat_with_ollama


def main():
    """Demonstrate Ollama integration with PRT."""
    print("🤖 PRT Ollama Integration Example")
    print("=" * 50)
    
    try:
        # Load configuration
        config = load_config()
        print("✅ Configuration loaded")
        
        # Create API instance
        api = PRTAPI(config)
        print("✅ API initialized")
        
        # Create Ollama LLM instance
        llm = OllamaLLM(api)
        print("✅ Ollama LLM initialized")
        
        # Show available tools
        print(f"\n📋 Available tools ({len(llm.tools)}):")
        for tool in llm.tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Example conversations
        print("\n💬 Example conversations:")
        
        # Example 1: Get database stats
        print("\n1. Getting database statistics...")
        response = chat_with_ollama(api, "What are the current database statistics?")
        print(f"Response: {response}")
        
        # Example 2: Search for contacts
        print("\n2. Searching for contacts...")
        response = chat_with_ollama(api, "Search for all contacts")
        print(f"Response: {response}")
        
        # Example 3: List tags
        print("\n3. Listing tags...")
        response = chat_with_ollama(api, "Show me all available tags")
        print(f"Response: {response}")
        
        print("\n✅ Example completed successfully!")
        print("\nTo start an interactive chat session, run:")
        print("  python -m prt_src.cli")
        print("  # Then select option 6: Start LLM Chat")
        print("\nOr start chat mode directly:")
        print("  python -m prt_src.cli chat")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nMake sure:")
        print("1. Ollama is installed and running (ollama serve)")
        print("2. GPT-OSS-20B model is pulled (ollama pull gpt-oss:20b)")
        print("3. PRT is properly configured")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
