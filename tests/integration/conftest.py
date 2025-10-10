"""Fixtures for integration tests.

Provides MockLLMService and other integration test fixtures.
"""

import json

import pytest

# ============================================================================
# Mock LLM Service
# ============================================================================


class MockLLMService:
    """Mock LLM that returns pre-defined responses for testing.

    This allows fast integration testing without actual LLM calls.
    """

    def __init__(self):
        """Initialize mock LLM with empty response library."""
        self.responses = {}
        self.call_count = 0
        self.last_prompt = None

    def add_response(self, pattern: str, response: dict):
        """Register a canned response for a prompt pattern.

        Args:
            pattern: String to match in the prompt
            response: Dictionary to return as JSON response
        """
        self.responses[pattern] = response

    def add_response_json(self, pattern: str, response_json: str):
        """Register a canned JSON response for a prompt pattern.

        Args:
            pattern: String to match in the prompt
            response_json: JSON string to return
        """
        self.responses[pattern] = response_json

    def chat(self, prompt: str) -> str:
        """Return canned response matching prompt pattern.

        Args:
            prompt: Prompt string

        Returns:
            JSON string response

        Raises:
            ValueError: If no matching response found
        """
        self.call_count += 1
        self.last_prompt = prompt

        # Find matching response
        for pattern, response in self.responses.items():
            if pattern.lower() in prompt.lower():
                # Return dict as JSON or return string directly
                if isinstance(response, dict):
                    return json.dumps(response)
                return response

        raise ValueError(f"No mock response registered for pattern in: {prompt[:100]}")

    def reset(self):
        """Reset call tracking."""
        self.call_count = 0
        self.last_prompt = None


# ============================================================================
# Pre-configured Mock LLM Fixtures
# ============================================================================


@pytest.fixture
def mock_llm():
    """Fixture: Basic mock LLM with common responses."""
    llm = MockLLMService()

    # Standard search intent
    llm.add_response(
        "tech contacts",
        {
            "intent": "search",
            "parameters": {"entity_type": "contacts", "filters": {"tags": ["tech"]}},
            "explanation": "Searching for tech contacts",
        },
    )

    llm.add_response(
        "show me contacts",
        {
            "intent": "search",
            "parameters": {"entity_type": "contacts", "filters": {}},
            "explanation": "Searching for all contacts",
        },
    )

    # Search with location
    llm.add_response(
        "san francisco",
        {
            "intent": "search",
            "parameters": {
                "entity_type": "contacts",
                "filters": {"location": ["San Francisco", "SF"]},
            },
            "explanation": "Searching contacts in San Francisco",
        },
    )

    # Standard selection intent
    llm.add_response(
        "select 1, 2",
        {
            "intent": "select",
            "parameters": {"selection_type": "ids", "ids": [1, 2]},
            "explanation": "Selected 2 contacts",
        },
    )

    llm.add_response(
        "select all",
        {
            "intent": "select",
            "parameters": {"selection_type": "all"},
            "explanation": "Selected all items",
        },
    )

    # Standard export intent
    llm.add_response(
        "export",
        {
            "intent": "export",
            "parameters": {"format": "json"},
            "explanation": "Exporting to JSON",
        },
    )

    llm.add_response(
        "directory",
        {
            "intent": "export",
            "parameters": {"format": "directory"},
            "explanation": "Exporting for directory maker",
        },
    )

    return llm


@pytest.fixture
def mock_llm_with_errors():
    """Fixture: Mock LLM that returns invalid responses for testing error handling."""
    llm = MockLLMService()

    # Malformed JSON
    llm.add_response_json("malformed", '{"intent": "search", "parameters":')  # Incomplete JSON

    # Missing required fields
    llm.add_response("missing_fields", {"intent": "search"})  # No parameters

    # Unknown intent
    llm.add_response(
        "unknown_intent",
        {
            "intent": "unknown_action",
            "parameters": {},
            "explanation": "This is an invalid intent",
        },
    )

    return llm


# ============================================================================
# Mock Response Library (for common patterns)
# ============================================================================


# Standard responses for search intents
MOCK_SEARCH_RESPONSES = {
    "tech contacts": {
        "intent": "search",
        "parameters": {"entity_type": "contacts", "filters": {"tags": ["tech"]}},
        "explanation": "Searching for tech contacts",
    },
    "python developers": {
        "intent": "search",
        "parameters": {
            "entity_type": "contacts",
            "filters": {"tags": ["python", "developer"]},
        },
        "explanation": "Searching for Python developers",
    },
    "contacts in sf": {
        "intent": "search",
        "parameters": {
            "entity_type": "contacts",
            "filters": {"location": ["SF", "San Francisco"]},
        },
        "explanation": "Searching contacts in San Francisco",
    },
}

# Standard responses for selection intents
MOCK_SELECTION_RESPONSES = {
    "select 1, 2, 3": {
        "intent": "select",
        "parameters": {"selection_type": "ids", "ids": [1, 2, 3]},
        "explanation": "Selected 3 contacts",
    },
    "select first 5": {
        "intent": "select",
        "parameters": {"selection_type": "range", "range": [1, 5]},
        "explanation": "Selected first 5 items",
    },
    "select all": {
        "intent": "select",
        "parameters": {"selection_type": "all"},
        "explanation": "Selected all items",
    },
    "clear selection": {
        "intent": "select",
        "parameters": {"selection_type": "none"},
        "explanation": "Cleared selection",
    },
}

# Standard responses for export intents
MOCK_EXPORT_RESPONSES = {
    "export to json": {
        "intent": "export",
        "parameters": {"format": "json"},
        "explanation": "Exporting to JSON",
    },
    "export for directory": {
        "intent": "export",
        "parameters": {"format": "directory"},
        "explanation": "Exporting for directory maker",
    },
}

# Standard responses for refinement intents
MOCK_REFINEMENT_RESPONSES = {
    "just the ones in oakland": {
        "intent": "refine",
        "parameters": {"action": "add_filter", "filters": {"location": ["Oakland"]}},
        "explanation": "Adding location filter for Oakland",
    },
    "remove location filter": {
        "intent": "refine",
        "parameters": {"action": "remove_filter", "filter_type": "location"},
        "explanation": "Removing location filter",
    },
}


def create_mock_llm_with_library(
    include_search=True,
    include_selection=True,
    include_export=True,
    include_refinement=True,
) -> MockLLMService:
    """Create a MockLLMService with standard response library.

    Args:
        include_search: Include search responses
        include_selection: Include selection responses
        include_export: Include export responses
        include_refinement: Include refinement responses

    Returns:
        Configured MockLLMService
    """
    llm = MockLLMService()

    if include_search:
        for pattern, response in MOCK_SEARCH_RESPONSES.items():
            llm.add_response(pattern, response)

    if include_selection:
        for pattern, response in MOCK_SELECTION_RESPONSES.items():
            llm.add_response(pattern, response)

    if include_export:
        for pattern, response in MOCK_EXPORT_RESPONSES.items():
            llm.add_response(pattern, response)

    if include_refinement:
        for pattern, response in MOCK_REFINEMENT_RESPONSES.items():
            llm.add_response(pattern, response)

    return llm


@pytest.fixture
def mock_llm_full_library():
    """Fixture: MockLLMService with complete response library."""
    return create_mock_llm_with_library(
        include_search=True,
        include_selection=True,
        include_export=True,
        include_refinement=True,
    )
