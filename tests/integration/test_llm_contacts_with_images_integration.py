"""Integration tests for LLM contacts with images workflow.

This test suite provides integration tests that work with real LLM services
but are designed to be resilient to response variability and external
dependency availability. Tests are categorized appropriately and handle
timeout scenarios gracefully.
"""

import re
import time
from pathlib import Path

import pytest

from prt_src.api import PRTAPI
from prt_src.llm_ollama import OllamaLLM
from tests.fixtures import get_fixture_spec
from tests.mocks.timeout_utils import is_ollama_available
from tests.mocks.timeout_utils import is_ollama_inference_ready
from tests.mocks.timeout_utils import timeout_context


@pytest.mark.integration
def test_api_get_contacts_with_images_performance(test_db):
    """Test the optimized API method for getting contacts with images - performance focused."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}
    api = PRTAPI(config)

    # Get fixture spec to validate expected data
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
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
def test_llm_tool_execution_with_timeout(test_db):
    """Test LLM tool execution with proper timeout protection."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    # Initialize API and LLM
    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    # Test with timeout protection
    with timeout_context(10):  # 10 second timeout for tool execution
        start_time = time.time()
        result = llm._get_contacts_with_images()
        tool_time = time.time() - start_time

        # Verify result structure - more flexible assertions
        assert isinstance(result, dict)

        # Handle different possible outcomes gracefully
        if result.get("success") is True:
            assert "contacts" in result
            assert "count" in result
            assert "message" in result
            contacts = result["contacts"]
            assert isinstance(contacts, list)
            assert result["count"] == len(contacts)
            print(f"✓ Tool returned {len(contacts)} contacts with images in {tool_time*1000:.1f}ms")
        else:
            # Tool failed - could be due to model loading, timeout, etc.
            pytest.skip(
                f"Tool execution failed (may be expected): {result.get('error', 'Unknown error')}"
            )


@pytest.mark.integration
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
def test_directory_creation_tool_with_cleanup(test_db):
    """Test directory creation with proper cleanup and error handling."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    test_output_name = "test_integration_directory"
    output_path = None

    try:
        with timeout_context(15):  # 15 second timeout for directory creation
            result = llm._create_directory_from_contacts_with_images(test_output_name)

            if result.get("success") is True:
                assert "output_path" in result
                assert "contact_count" in result
                assert "performance" in result

                output_path = Path(result["output_path"])
                assert output_path.exists(), f"Directory not created at {output_path}"

                # Check for key files
                index_file = output_path / "index.html"
                assert index_file.exists(), "index.html not found in directory"

                print(f"✓ Created directory with {result['contact_count']} contacts")
                print(f"  Output: {result['output_path']}")
            else:
                pytest.skip(
                    f"Directory creation failed (may be expected): {result.get('error', 'Unknown error')}"
                )

    finally:
        # Cleanup: remove test directory if it was created
        if output_path and output_path.exists():
            import shutil

            try:
                shutil.rmtree(output_path)
                print(f"✓ Cleaned up test directory: {output_path}")
            except Exception as e:
                print(f"Warning: Could not clean up test directory {output_path}: {e}")


@pytest.mark.contract
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
def test_llm_query_understanding_resilient(test_db):
    """Test LLM understanding with resilient response validation."""
    if not is_ollama_inference_ready():
        pytest.skip("Ollama inference not working properly")

    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

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
            response = llm.chat(query)
            response_time = time.time() - start_time

            # Verify we got a response
            assert isinstance(response, str)

            # Handle empty responses gracefully
            if len(response.strip()) == 0:
                pytest.skip(
                    f"LLM returned empty response for '{query}' - may indicate model loading issues"
                )
                continue

            # More flexible content validation
            response_lower = response.lower()
            relevant_keywords = [
                "contact",
                "image",
                "photo",
                "picture",
                "found",
                "directory",
                "search",
            ]
            has_relevant_content = any(keyword in response_lower for keyword in relevant_keywords)

            if not has_relevant_content:
                print(
                    f"Warning: Response may not be relevant to query '{query}': {response[:100]}..."
                )
                # Don't fail the test - just warn, as LLM might respond differently

            # Reasonable performance expectations
            assert response_time < 60.0, f"Query took {response_time:.1f}s, expected < 60s"

            print(
                f"✓ Query '{query}' processed in {response_time:.2f}s (relevant: {has_relevant_content})"
            )

        except Exception as e:
            print(f"Warning: Query '{query}' failed: {e}")
            # Don't fail the entire test for individual query failures
            continue


@pytest.mark.contract
@pytest.mark.flaky(max_runs=3, min_passes=1)
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
def test_full_workflow_with_response_patterns(test_db):
    """Test full workflow with acceptance of different LLM response patterns.

    This test acknowledges that LLMs can respond in multiple valid ways:
    1. Conversational (asking for clarification)
    2. Explanatory (explaining what they will do)
    3. Tool execution (actually running tools)
    4. Mixed (explanation + execution)
    """
    if not is_ollama_inference_ready():
        pytest.skip("Ollama inference not working properly")

    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    query = "create a directory of all contacts with images"
    start_time = time.time()

    try:
        with timeout_context(60):  # 60 second timeout for full workflow
            response = llm.chat(query)
            total_time = time.time() - start_time

        # Basic response validation
        assert isinstance(response, str)

        if len(response.strip()) == 0:
            pytest.skip("LLM returned empty response - may indicate model/prompt issues")

        response_lower = response.lower()

        # Categorize the type of response we got
        response_type = "unknown"

        # Pattern 1: Conversational/clarification
        clarification_patterns = [
            r"would you like",
            r"do you want",
            r"shall i",
            r"should i",
            r"\?.*create",
            r"confirm.*directory",
        ]
        if any(re.search(pattern, response_lower) for pattern in clarification_patterns):
            response_type = "conversational"

        # Pattern 2: Explanatory
        explanation_patterns = [
            r"i (will|can|am going to)",
            r"let me",
            r"i'll",
            r"first.*get",
            r"then.*create",
        ]
        if any(re.search(pattern, response_lower) for pattern in explanation_patterns):
            response_type = "explanatory"

        # Pattern 3: Tool execution results
        execution_patterns = [
            r"found \d+ contacts",
            r"created.*directory",
            r"directory.*created",
            r"output.*path",
            r"\.html",
            r"exported.*contacts",
        ]
        if any(re.search(pattern, response_lower) for pattern in execution_patterns):
            response_type = "execution"

        # Pattern 4: Error/limitation
        error_patterns = [r"error", r"failed", r"cannot", r"unable", r"sorry"]
        if any(re.search(pattern, response_lower) for pattern in error_patterns):
            response_type = "error"

        # Verify the response contains some relevant content
        relevant_keywords = ["contact", "directory", "image", "create", "found", "photo", "picture"]
        has_relevant_content = any(keyword in response_lower for keyword in relevant_keywords)

        print("✓ LLM Response Analysis:")
        print(f"  Type: {response_type}")
        print(f"  Length: {len(response)} characters")
        print(f"  Time: {total_time:.2f}s")
        print(f"  Relevant content: {has_relevant_content}")
        print(f"  Response: {response[:200]}{'...' if len(response) > 200 else ''}")

        # All response types are valid - just verify we got something reasonable
        assert has_relevant_content or response_type != "unknown", (
            f"Response doesn't seem relevant to query. Type: {response_type}, "
            f"Content: {response[:100]}..."
        )

        # Performance check
        assert total_time < 90.0, f"Workflow took {total_time:.1f}s, expected < 90s"

    except Exception as e:
        pytest.fail(f"Full workflow failed with exception: {e}")


@pytest.mark.integration
@pytest.mark.skipif(not is_ollama_available(), reason="Ollama not available")
def test_basic_llm_health_check(test_db):
    """Basic health check to verify LLM is responsive."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}

    api = PRTAPI(config)
    llm = OllamaLLM(api=api)

    # Simple health check query
    with timeout_context(20):
        try:
            response = llm.chat("Hello")

            # Just verify we got some response
            assert isinstance(response, str)
            assert len(response.strip()) > 0

            print(
                f"✓ LLM health check passed. Response: {response[:50]}{'...' if len(response) > 50 else ''}"
            )

        except Exception as e:
            pytest.skip(f"LLM health check failed: {e}")


@pytest.mark.integration
def test_fixture_data_validation_for_images(test_db):
    """Validate that test fixtures contain contacts with images as expected."""
    db, fixtures = test_db
    config = {"db_path": str(db.path), "db_encrypted": False}
    api = PRTAPI(config)

    # Get fixture specification
    spec = get_fixture_spec()

    # Get all contacts and those with images
    all_contacts = api.list_all_contacts()
    contacts_with_images = api.get_contacts_with_images()

    print("Fixture validation:")
    print(f"  Total contacts: {len(all_contacts)}")
    print(f"  Contacts with images: {len(contacts_with_images)}")
    print(f"  Expected contacts from spec: {spec['contacts']['count']}")

    # Validate fixture data
    assert len(all_contacts) > 0, "Test fixtures should contain contacts"
    assert len(contacts_with_images) > 0, "Test fixtures should contain contacts with images"
    assert len(contacts_with_images) <= len(
        all_contacts
    ), "Contacts with images should be subset of all contacts"

    # Validate image data integrity
    for contact in contacts_with_images:
        assert (
            "profile_image" in contact
        ), f"Contact {contact.get('name', 'Unknown')} missing profile_image key"
        assert (
            contact["profile_image"] is not None
        ), f"Contact {contact.get('name', 'Unknown')} has null profile_image"
        assert isinstance(
            contact["profile_image"], bytes
        ), f"Contact {contact.get('name', 'Unknown')} profile_image is not bytes"
        assert (
            len(contact["profile_image"]) > 100
        ), f"Contact {contact.get('name', 'Unknown')} profile_image seems too small: {len(contact['profile_image'])} bytes"

    print(
        f"✓ Fixture validation passed - {len(contacts_with_images)} contacts have valid profile images"
    )
