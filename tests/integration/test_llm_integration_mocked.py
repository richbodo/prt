"""Fast integration tests using MockLLMService for deterministic testing.

These tests validate component interactions without real LLM dependencies,
ensuring fast feedback loops (< 5s) while maintaining integration test coverage.
"""

import time

import pytest

from prt_src.api import PRTAPI
from tests.fixtures import get_fixture_spec
from tests.mocks import MockOllamaLLM


@pytest.mark.integration
class TestLLMIntegrationMocked:
    """Fast integration tests using MockLLMService."""

    def setup_method(self):
        """Set up test environment with mocked LLM."""
        # This will be set by individual test methods
        self.mock_llm = None
        self.test_api = None

    def test_contact_count_query_fast(self, test_db):
        """Test contact counting with deterministic mock response."""
        start_time = time.time()

        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        self.test_api = PRTAPI(config)
        self.mock_llm = MockOllamaLLM(api=self.test_api)

        # Get the actual contact count from the test database
        contacts = self.test_api.list_all_contacts()
        expected_count = len(contacts)

        response = self.mock_llm.chat("How many contacts do I have?")

        # Verify response content (mock should use real API data)
        assert str(expected_count) in response or "contact" in response.lower()
        assert len(self.mock_llm.conversation_history) == 2

        # Verify timing - should be fast
        elapsed = time.time() - start_time
        assert elapsed < 1.0, f"Test took {elapsed:.2f}s, should be < 1s"

    def test_tool_calling_workflow_fast(self, test_db):
        """Test tool calling workflow without real LLM processing."""
        start_time = time.time()

        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        self.test_api = PRTAPI(config)
        self.mock_llm = MockOllamaLLM(api=self.test_api)

        # Mock will simulate get_database_stats tool call
        response = self.mock_llm.chat("How many contacts do I have?")

        # Verify tool was "called" in simulation
        assert self.mock_llm.last_tool_called == "get_database_stats"
        assert "contact" in response.lower()

        # Verify tool call history
        tool_history = self.mock_llm.get_tool_call_history()
        assert len(tool_history) == 1
        assert tool_history[0]["tool"] == "get_database_stats"

        # Verify timing
        elapsed = time.time() - start_time
        assert elapsed < 1.0, f"Test took {elapsed:.2f}s, should be < 1s"

    def test_search_contacts_simulation(self, test_db):
        """Test contact search simulation with MockLLMService."""
        start_time = time.time()

        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        self.test_api = PRTAPI(config)
        self.mock_llm = MockOllamaLLM(api=self.test_api)

        # Test search for contacts (use a search term that should find something)
        contacts = self.test_api.list_all_contacts()
        if contacts:
            first_name = contacts[0]["name"].split()[0]
            response = self.mock_llm.chat(f"Search for contacts named {first_name}")
        else:
            response = self.mock_llm.chat("Search for contacts named John")

        # Verify response indicates search was performed
        assert "contact" in response.lower() or "found" in response.lower()
        assert self.mock_llm.last_tool_called == "search_contacts"

        # Verify tool call arguments
        tool_history = self.mock_llm.get_tool_call_history()
        assert len(tool_history) == 1
        assert "query" in tool_history[0]["args"]

        # Verify timing
        elapsed = time.time() - start_time
        assert elapsed < 1.0, f"Test took {elapsed:.2f}s, should be < 1s"

    def test_export_contacts_simulation(self, test_db):
        """Test contact export simulation with MockLLMService."""
        start_time = time.time()

        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        self.test_api = PRTAPI(config)
        self.mock_llm = MockOllamaLLM(api=self.test_api)

        response = self.mock_llm.chat("Export my contacts to JSON")

        # Verify response indicates export
        assert "export" in response.lower()
        assert self.mock_llm.last_tool_called == "export_contacts"

        # Verify timing
        elapsed = time.time() - start_time
        assert elapsed < 1.0, f"Test took {elapsed:.2f}s, should be < 1s"

    def test_conversation_history_management(self, test_db):
        """Test conversation history is properly maintained."""
        start_time = time.time()

        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        self.test_api = PRTAPI(config)
        self.mock_llm = MockOllamaLLM(api=self.test_api)

        # Multiple interactions
        self.mock_llm.chat("Hello")
        self.mock_llm.chat("How many contacts?")
        self.mock_llm.chat("Search for Alice")

        # Verify history structure
        history = self.mock_llm.get_conversation_history()
        assert len(history) == 6  # 3 user + 3 assistant messages

        # Check message structure
        for i in range(0, 6, 2):  # User messages
            assert history[i]["role"] == "user"
            assert "content" in history[i]

        for i in range(1, 6, 2):  # Assistant messages
            assert history[i]["role"] == "assistant"
            assert "content" in history[i]

        # Verify timing
        elapsed = time.time() - start_time
        assert elapsed < 1.0, f"Test took {elapsed:.2f}s, should be < 1s"

    def test_response_pattern_matching(self, test_db):
        """Test response pattern matching works correctly."""
        start_time = time.time()

        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        self.test_api = PRTAPI(config)
        self.mock_llm = MockOllamaLLM(api=self.test_api)

        # Test various patterns
        test_cases = [
            ("What can you do?", "help"),
            ("List my contacts", "contact"),
            ("Create a directory", "directory"),
            ("Add a tag called work", "tag"),
        ]

        for query, expected_keyword in test_cases:
            response = self.mock_llm.chat(query)
            assert (
                expected_keyword.lower() in response.lower()
            ), f"Response '{response}' should contain '{expected_keyword}'"

        # Verify timing
        elapsed = time.time() - start_time
        assert elapsed < 1.0, f"Test took {elapsed:.2f}s, should be < 1s"

    def test_health_check_and_preload_always_succeed(self, test_db):
        """Test that mock health check and preload always return True."""
        start_time = time.time()

        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        self.test_api = PRTAPI(config)
        self.mock_llm = MockOllamaLLM(api=self.test_api)

        # Test async methods
        import asyncio

        async def test_async():
            health = await self.mock_llm.health_check()
            preload = await self.mock_llm.preload_model()
            return health, preload

        health, preload = asyncio.run(test_async())

        assert health is True
        assert preload is True
        assert self.mock_llm.is_available() is True

        # Verify timing
        elapsed = time.time() - start_time
        assert elapsed < 1.0, f"Test took {elapsed:.2f}s, should be < 1s"

    def test_custom_response_overrides(self, test_db):
        """Test that custom response overrides work correctly."""
        start_time = time.time()

        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        self.test_api = PRTAPI(config)
        self.mock_llm = MockOllamaLLM(api=self.test_api)

        # Set custom response
        custom_response = "This is a custom test response for testing purposes."
        self.mock_llm.set_response("test.*custom", custom_response)

        response = self.mock_llm.chat("test custom functionality")
        assert response == custom_response

        # Test that pattern didn't affect other queries
        response2 = self.mock_llm.chat("How many contacts?")
        assert response2 != custom_response
        assert "contact" in response2.lower()

        # Verify timing
        elapsed = time.time() - start_time
        assert elapsed < 1.0, f"Test took {elapsed:.2f}s, should be < 1s"

    def test_api_integration_with_fixtures(self, test_db):
        """Test that MockLLMService properly integrates with test database."""
        start_time = time.time()

        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        self.test_api = PRTAPI(config)
        self.mock_llm = MockOllamaLLM(api=self.test_api)

        # Get fixture spec to verify expectations
        spec = get_fixture_spec()
        expected_contacts = spec["contacts"]["count"]

        # Mock should have access to real API data for context
        response = self.mock_llm.chat("How many contacts in the database?")

        # Verify mock used real API data for context
        assert str(expected_contacts) in response or response.count("contact") > 0

        # Verify the mock LLM has tools configured
        assert len(self.mock_llm.tools) > 0
        tool_names = [tool["name"] for tool in self.mock_llm.tools]
        assert "get_database_stats" in tool_names
        assert "search_contacts" in tool_names

        # Verify timing
        elapsed = time.time() - start_time
        assert elapsed < 1.0, f"Test took {elapsed:.2f}s, should be < 1s"

    def test_clear_conversation_functionality(self, test_db):
        """Test conversation clearing functionality."""
        start_time = time.time()

        db, fixtures = test_db
        config = {"db_path": str(db.path), "db_encrypted": False}
        self.test_api = PRTAPI(config)
        self.mock_llm = MockOllamaLLM(api=self.test_api)

        # Add some conversation history
        self.mock_llm.chat("Hello")
        self.mock_llm.chat("How many contacts?")

        assert len(self.mock_llm.conversation_history) == 4
        assert len(self.mock_llm.tool_call_history) > 0

        # Clear conversation
        self.mock_llm.clear_conversation()

        assert len(self.mock_llm.conversation_history) == 0
        assert len(self.mock_llm.tool_call_history) == 0
        assert self.mock_llm.last_tool_called is None

        # Verify timing
        elapsed = time.time() - start_time
        assert elapsed < 1.0, f"Test took {elapsed:.2f}s, should be < 1s"
