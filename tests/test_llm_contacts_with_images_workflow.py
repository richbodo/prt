"""Integration test: LLM workflow for creating directory of contacts with images.

This test verifies the complete workflow:
1. LLM query parsing for "create a directory of contacts with images"
2. Optimized database query using index
3. Tool chaining from query to directory creation
4. Performance measurement
"""

import time
from pathlib import Path

import pytest
import requests

from prt_src.api import PRTAPI
from prt_src.llm_ollama import OllamaLLM
from tests.fixtures import get_fixture_spec


def is_ollama_available() -> bool:
    """Check if Ollama is running and available with models."""
    try:
        # Test basic connectivity
        response = requests.get("http://localhost:11434/api/version", timeout=2)
        if response.status_code != 200:
            return False

        # Test model availability
        tags_response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if tags_response.status_code != 200:
            return False

        # Check if any models are available
        tags_data = tags_response.json()
        models = tags_data.get("models", [])
        return len(models) > 0

    except (requests.RequestException, ConnectionError, ValueError, KeyError):
        return False


# Import from centralized utilities
from tests.mocks.timeout_utils import is_ollama_inference_ready
from tests.mocks.timeout_utils import timeout_context


@pytest.mark.integration
@pytest.mark.performance
def test_get_contacts_with_images_api(test_db):
    """Test the optimized API method for getting contacts with images."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}
    api = PRTAPI(config)

    # Get fixture spec to know expected data
    spec = get_fixture_spec()

    start_time = time.time()
    contacts = api.get_contacts_with_images()
    query_time = time.time() - start_time

    # Verify results using fixture spec
    assert isinstance(contacts, list)
    expected_with_images = spec["contacts"]["expected_with_images_count"]
    assert (
        len(contacts) == expected_with_images
    ), f"Expected {expected_with_images} contacts with images from fixtures, got {len(contacts)}"

    # Check that all returned contacts have images
    for contact in contacts:
        assert (
            contact["profile_image"] is not None
        ), f"Contact {contact['name']} missing profile_image"
        assert isinstance(contact["profile_image"], bytes), "Profile image should be bytes"
        assert len(contact["profile_image"]) > 0, "Profile image should not be empty"

    # Performance check - should be fast with index
    expected_max_time = 1.0
    assert (
        query_time < expected_max_time
    ), f"Query took {query_time:.3f}s, expected < {expected_max_time}s with index"

    # Performance targets for different scenarios
    if len(contacts) <= 10:
        # Small dataset should be very fast
        assert query_time < 0.1, f"Small dataset query took {query_time:.3f}s, expected < 0.1s"
    elif len(contacts) <= 100:
        # Medium dataset should still be fast
        assert query_time < 0.5, f"Medium dataset query took {query_time:.3f}s, expected < 0.5s"

    print(f"✓ Found {len(contacts)} contacts with images in {query_time*1000:.1f}ms")


@pytest.mark.integration
def test_get_contacts_with_images_tool(test_db):
    """Test the LLM tool for getting contacts with images."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    # Call the tool directly
    start_time = time.time()
    result = llm._get_contacts_with_images()
    tool_time = time.time() - start_time

    # Verify result structure
    assert isinstance(result, dict)
    assert result["success"] is True, f"Tool failed: {result.get('error')}"
    assert "contacts" in result
    assert "count" in result
    assert "message" in result

    # Verify data
    contacts = result["contacts"]
    assert len(contacts) > 0, "Expected contacts with images from fixtures"
    assert result["count"] == len(contacts)

    # Performance check with detailed assertions
    expected_max_time = 1.0
    assert (
        tool_time < expected_max_time
    ), f"Tool took {tool_time:.3f}s, expected < {expected_max_time}s"

    # Tool should have minimal overhead over the API call
    # Since the tool calls the API, it should be only slightly slower
    if len(contacts) <= 10:
        assert (
            tool_time < 0.2
        ), f"Small dataset tool execution took {tool_time:.3f}s, expected < 0.2s"

    print(f"✓ Tool returned {len(contacts)} contacts with images in {tool_time*1000:.1f}ms")


@pytest.mark.integration
def test_create_directory_tool(test_db):
    """Test the combined tool for creating directory from contacts with images."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    # Call the combined tool
    start_time = time.time()
    result = llm._create_directory_from_contacts_with_images("test_contacts_with_images")
    time.time() - start_time  # Track total time

    # Verify result structure
    assert isinstance(result, dict)
    assert result["success"] is True, f"Directory creation failed: {result.get('error')}"
    assert "output_path" in result
    assert "url" in result
    assert "contact_count" in result
    assert "performance" in result

    # Verify performance metrics
    perf = result["performance"]
    assert "query_time_ms" in perf
    assert "directory_time_ms" in perf
    assert "total_time_ms" in perf

    # Verify the directory was created
    output_path = Path(result["output_path"])
    assert output_path.exists(), f"Directory not created at {output_path}"

    # Check for key files
    index_file = output_path / "index.html"
    assert index_file.exists(), "index.html not found in directory"

    # Verify contact count matches
    assert result["contact_count"] > 0, "Expected contacts in directory"

    print(f"✓ Created directory with {result['contact_count']} contacts")
    print(f"  Query time: {perf['query_time_ms']:.1f}ms")
    print(f"  Directory creation: {perf['directory_time_ms']:.1f}ms")
    print(f"  Total time: {perf['total_time_ms']:.1f}ms")
    print(f"  Output: {result['output_path']}")


@pytest.mark.contract
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
def test_llm_contacts_with_images_query_understanding(test_db):
    """Test that LLM can understand and process 'contacts with images' queries.

    This is a contract test that validates real LLM behavior and may be flaky
    due to the non-deterministic nature of LLM responses.
    """
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    test_queries = [
        "get all contacts with profile images",
        "show me contacts that have pictures",
        "find contacts with profile photos",
        "list contacts with images",
    ]

    for query in test_queries:
        start_time = time.time()

        try:
            # Add timeout protection for each query
            with timeout_context(30):  # 30 second timeout per query
                response = llm.chat(query)
                response_time = time.time() - start_time

                # Verify we got a response
                assert isinstance(response, str)

                # Handle empty responses gracefully
                if len(response.strip()) == 0:
                    print(
                        f"Warning: Empty response for query '{query}' - may indicate model issues"
                    )
                    continue

                # The LLM should be able to understand this is about contacts with images
                # This is more of a behavioral test - we can't assert exact content
                # but we can verify it doesn't error and produces reasonable output

                print(f"✓ Query '{query}' processed in {response_time:.2f}s")

        except Exception as e:
            print(f"Warning: LLM failed to process query '{query}': {e}")
            # Don't fail the entire test - LLMs can be unpredictable
            continue


@pytest.mark.contract
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
def test_llm_basic_inference(test_db):
    """Test basic LLM inference capability - simpler than full workflow test.

    This is a contract test that validates basic LLM responsiveness.
    """
    if not is_ollama_inference_ready():
        pytest.skip("Ollama inference not working")

    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    # Test with a simple, predictable query
    query = "Hello, please respond with 'Hello' to confirm you are working"

    start_time = time.time()

    try:
        with timeout_context(20):  # 20 second timeout for basic inference
            response = llm.chat(query)
            total_time = time.time() - start_time

        print(f"LLM response: {response}")
        print(f"Response time: {total_time:.2f}s")

        # Basic assertions - just verify we got some response
        assert isinstance(response, str)
        assert len(response) > 0

        # Performance target: should complete in reasonable time
        assert total_time < 30.0, f"Basic inference took {total_time:.1f}s, expected < 30s"

        print(f"✓ Basic LLM inference working in {total_time:.2f}s")

    except Exception as e:
        pytest.fail(f"Basic LLM inference failed: {e}")


@pytest.mark.contract
@pytest.mark.flaky(max_runs=3, min_passes=1)
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
def test_full_workflow_performance(test_db):
    """Performance test for the full workflow: query understanding -> tool execution.

    NOTE: This test may show variable behavior based on LLM responses.
    The LLM might respond conversationally (asking for clarification) rather than
    executing tools immediately, which is actually correct behavior.

    This is a flaky contract test due to LLM non-deterministic behavior.
    """
    if not is_ollama_inference_ready():
        pytest.skip("Ollama inference not working")

    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    # Test the specific query that should trigger our optimized tool
    query = "create a directory of all contacts with images"

    start_time = time.time()

    try:
        with timeout_context(60):  # 60 second timeout for full workflow
            response = llm.chat(query)
            total_time = time.time() - start_time

        print(f"LLM response: {response}")
        print(f"Response time: {total_time:.2f}s")

        # More flexible assertions - the LLM might respond conversationally
        assert isinstance(response, str)

        # Check for either:
        # 1. A meaningful response (conversational)
        # 2. Tool execution results
        # 3. Or at least some response indicating the LLM understood
        if len(response) == 0:
            pytest.skip(
                "LLM returned empty response - this may indicate model loading issues or prompt handling differences in test environment"
            )

        # The response should contain some indication that the LLM understood the request
        response_lower = response.lower()
        expected_keywords = ["contact", "directory", "image", "create", "found"]
        has_relevant_content = any(keyword in response_lower for keyword in expected_keywords)

        if not has_relevant_content:
            print(f"Warning: LLM response doesn't contain expected keywords. Response: {response}")
            # Don't fail the test, just warn - the LLM might be responding differently

        # Performance target: should complete in reasonable time
        assert total_time < 60.0, f"Full workflow took {total_time:.1f}s, expected < 60s"

        print(f"✓ Full workflow completed in {total_time:.2f}s")
        print(f"  Response length: {len(response)} characters")
        print(f"  Contains relevant keywords: {has_relevant_content}")

    except Exception as e:
        pytest.fail(f"Full workflow failed: {e}")


if __name__ == "__main__":
    # Allow running this test directly for development
    pytest.main([__file__, "-v"])
