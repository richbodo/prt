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
    """Check if Ollama is running and available."""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        return response.status_code == 200
    except (requests.RequestException, ConnectionError):
        return False


@pytest.mark.integration
def test_get_contacts_with_images_api(test_db):
    """Test the optimized API method for getting contacts with images."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}
    api = PRTAPI(config)

    # Get fixture spec to know expected data
    get_fixture_spec()

    start_time = time.time()
    contacts = api.get_contacts_with_images()
    query_time = time.time() - start_time

    # Verify results
    assert isinstance(contacts, list)
    assert len(contacts) > 0, "Expected at least some contacts with images from fixtures"

    # Check that all returned contacts have images
    for contact in contacts:
        assert (
            contact["profile_image"] is not None
        ), f"Contact {contact['name']} missing profile_image"
        assert isinstance(contact["profile_image"], bytes), "Profile image should be bytes"
        assert len(contact["profile_image"]) > 0, "Profile image should not be empty"

    # Performance check - should be fast with index
    assert query_time < 1.0, f"Query took {query_time:.3f}s, expected < 1.0s with index"

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

    # Performance check
    assert tool_time < 1.0, f"Tool took {tool_time:.3f}s, expected < 1.0s"

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


@pytest.mark.integration
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
def test_llm_contacts_with_images_query_understanding(test_db):
    """Test that LLM can understand and process 'contacts with images' queries."""
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
            # Test LLM understanding
            response = llm.chat(query)
            response_time = time.time() - start_time

            # Verify we got a response
            assert isinstance(response, str)
            assert len(response) > 0

            # The LLM should be able to understand this is about contacts with images
            # This is more of a behavioral test - we can't assert exact content
            # but we can verify it doesn't error and produces reasonable output

            print(f"✓ Query '{query}' processed in {response_time:.2f}s")

        except Exception as e:
            pytest.fail(f"LLM failed to process query '{query}': {e}")


@pytest.mark.integration
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
def test_full_workflow_performance(test_db):
    """Performance test for the full workflow: query understanding -> tool execution."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    # Test the specific query that should trigger our optimized tool
    query = "create a directory of all contacts with images"

    start_time = time.time()

    try:
        response = llm.chat(query)
        total_time = time.time() - start_time

        # Verify we got a meaningful response
        print(f"LLM response: {response}")
        assert isinstance(response, str)
        assert len(response) > 0

        # Performance target: should complete in reasonable time
        # This includes LLM processing + tool execution
        assert total_time < 30.0, f"Full workflow took {total_time:.1f}s, expected < 30s"

        print(f"✓ Full workflow completed in {total_time:.2f}s")
        print(f"  Response length: {len(response)} characters")

    except Exception as e:
        pytest.fail(f"Full workflow failed: {e}")


if __name__ == "__main__":
    # Allow running this test directly for development
    pytest.main([__file__, "-v"])
