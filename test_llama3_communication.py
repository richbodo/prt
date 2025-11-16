#!/usr/bin/env python3
"""
Quick test to reproduce the llama3-8b-local communication error
"""

import os
import sys
import traceback

# Add prt_src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "prt_src"))

from prt_src.api import PRTAPI
from prt_src.llm_factory import create_llm


def test_llama3_communication():
    """Test communication with llama3-8b-local model"""
    print("🔍 Testing llama3-8b-local communication...")

    try:
        # Initialize API and config
        prt_api = PRTAPI()
        print("📋 API initialized")

        # Create LLM instance
        print("🤖 Creating LLM instance...")
        llm = create_llm(api=prt_api, model="llama3-8b-local")
        print(f"✅ LLM created: {type(llm).__name__} with model {llm.model}")

        # Test health check
        print("💓 Testing health check...")
        is_healthy = llm.health_check()
        print(f"Health check result: {is_healthy}")

        if not is_healthy:
            print("❌ Health check failed!")
            return False

        # Test preload
        print("📥 Testing model preload...")
        preload_result = llm.preload_model()
        print(f"Preload result: {preload_result}")

        # Test simple chat
        print("💬 Testing simple chat...")
        response = llm.chat("Hello, just say 'hi' back")
        print(f"Chat response: {response}")

        print("✅ All tests passed!")
        return True

    except Exception as e:
        print(f"❌ Error during test: {e}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        return False


def test_mistral_comparison():
    """Test communication with mistral for comparison"""
    print("\n🔍 Testing mistral-7b-instruct for comparison...")

    try:
        # Initialize API
        prt_api = PRTAPI()

        # Create LLM instance
        print("🤖 Creating Mistral LLM instance...")
        llm = create_llm(api=prt_api, model="mistral-7b-instruct")
        print(f"✅ LLM created: {type(llm).__name__} with model {llm.model}")

        # Test health check
        print("💓 Testing health check...")
        is_healthy = llm.health_check()
        print(f"Health check result: {is_healthy}")

        # Test simple chat
        print("💬 Testing simple chat...")
        response = llm.chat("Hello, just say 'hi' back")
        print(f"Chat response: {response}")

        print("✅ Mistral tests passed!")
        return True

    except Exception as e:
        print(f"❌ Error during Mistral test: {e}")
        print(f"Error type: {type(e).__name__}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting LLM communication tests...\n")

    # Test llama3-8b-local
    llama3_success = test_llama3_communication()

    # Test mistral for comparison
    mistral_success = test_mistral_comparison()

    print("\n📊 Results:")
    print(f"   llama3-8b-local: {'✅ PASS' if llama3_success else '❌ FAIL'}")
    print(f"   mistral-7b-instruct: {'✅ PASS' if mistral_success else '❌ FAIL'}")

    if not llama3_success:
        print("\n🐛 llama3-8b-local has communication issues that need to be fixed!")
        sys.exit(1)
    else:
        print("\n✅ All models working correctly!")
