import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from prt_src.config import LLMConfigManager  # noqa: E402
from prt_src.db import create_database  # noqa: E402
from tests.fixtures import setup_test_database  # noqa: E402
from tests.mocks.mock_llm_memory import TestMemoryContext  # noqa: E402
from tests.mocks.mock_llm_memory import create_test_memory  # noqa: E402

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
def test_db(tmp_path):
    """Create a test database with sample data."""
    db_path = tmp_path / "test.db"
    db = create_database(db_path)
    fixtures = setup_test_database(db)
    return db, fixtures


@pytest.fixture
def test_db_empty(tmp_path):
    """Create an empty test database."""
    db_path = tmp_path / "empty_test.db"
    db = create_database(db_path)
    db.initialize()  # Just create tables, no data
    return db


@pytest.fixture
def sample_config(tmp_path):
    """Create sample configuration for tests."""
    db_path = tmp_path / "config_test.db"
    return {
        "db_path": str(db_path),
        "db_encrypted": False,
        "db_type": "sqlite",
        "db_username": "test",
        "db_password": "test",
    }


@pytest.fixture
def mock_app():
    """Create a mock app for testing."""
    from unittest.mock import MagicMock

    from prt_src.tui.types import AppMode

    app = MagicMock()
    app.mode = AppMode.NAVIGATION
    app.exit = MagicMock()
    app.push_screen = MagicMock()
    app.pop_screen = MagicMock()
    return app


@pytest.fixture
def pilot_screen():
    """Create a pilot for testing Textual screens."""
    from contextlib import asynccontextmanager

    from textual.app import App

    from prt_src.tui.types import AppMode

    class TestApp(App):
        """Minimal test app."""

        def __init__(self, screen_class, **screen_kwargs):
            super().__init__()
            self._screen_class = screen_class
            self._screen_kwargs = screen_kwargs
            # Initialize mode like the real app
            self._app_mode = AppMode.NAVIGATION

        @property
        def current_mode(self):
            """Get current mode (matches real app API)."""
            return self._app_mode

        @current_mode.setter
        def current_mode(self, mode):
            """Set current mode (matches real app API)."""
            self._app_mode = mode

        def on_mount(self):
            """Push the test screen on mount."""
            self.push_screen(self._screen_class(**self._screen_kwargs))

    @asynccontextmanager
    async def _pilot(screen_class, **screen_kwargs):
        """Run screen in test app."""
        app = TestApp(screen_class, **screen_kwargs)
        async with app.run_test() as pilot:
            yield pilot

    return _pilot


@pytest.fixture
def mock_llm_memory(request):
    """Create isolated mock memory for tests."""
    test_name = request.node.name
    return create_test_memory(test_name=test_name, use_temp_files=False)


@pytest.fixture
def mock_llm_memory_with_files(request):
    """Create isolated mock memory with file storage for tests."""
    test_name = request.node.name
    return create_test_memory(test_name=test_name, use_temp_files=True)


@pytest.fixture
def isolated_memory_context(request):
    """Context manager for completely isolated LLM memory during tests."""
    test_name = request.node.name
    with TestMemoryContext(test_name=test_name, use_temp_files=False, patch_global=True) as memory:
        yield memory


@pytest.fixture
def isolated_memory_context_with_files(request):
    """Context manager for isolated LLM memory with file storage during tests."""
    test_name = request.node.name
    with TestMemoryContext(test_name=test_name, use_temp_files=True, patch_global=True) as memory:
        yield memory


@pytest.fixture
def mock_directory_generator():
    """Mock directory generator to eliminate file system dependencies."""
    from tests.mocks.mock_directory_generator import MockDirectoryGeneratorPatcher

    with MockDirectoryGeneratorPatcher(mock_success=True) as patcher:
        yield patcher


@pytest.fixture
def mock_directory_generator_fail():
    """Mock directory generator that simulates generation failures."""
    from tests.mocks.mock_directory_generator import MockDirectoryGeneratorPatcher

    with MockDirectoryGeneratorPatcher(mock_success=False) as patcher:
        yield patcher


@pytest.fixture
def llm_config():
    """Create a test LLM config manager that doesn't depend on global config file."""
    test_config = {
        "db_path": "prt_data/test.db",
        "db_encrypted": False,
        "database_mode": "test",
        "llm": {
            "provider": "ollama",
            "model": "gpt-oss:20b",
            "base_url": "http://localhost:11434",
            "keep_alive": "30m",
            "timeout": 300,
            "temperature": 0.1,
        },
        "llm_permissions": {
            "allow_create": True,
            "allow_update": True,
            "allow_delete": False,
            "require_confirmation": {"delete": True, "bulk_operations": True},
            "max_bulk_operations": 100,
            "read_only_mode": False,
        },
        "llm_prompts": {"override_system_prompt": None, "use_file": False, "file_path": None},
        "llm_context": {
            "mode": "adaptive",
            "max_conversation_history": 3,
            "max_context_tokens": 4000,
        },
        "llm_developer": {
            "debug_mode": False,
            "log_prompts": False,
            "log_responses": False,
            "log_timing": False,
        },
        "llm_tools": {"disabled": ["save_contacts_with_images", "list_memory"]},
    }
    return LLMConfigManager(config_dict=test_config)


@pytest.fixture
def llm_config_dict():
    """Create a test configuration dictionary for tests that need to pass config directly."""
    return {
        "db_path": "prt_data/test.db",
        "db_encrypted": False,
        "database_mode": "test",
        "llm": {
            "provider": "ollama",
            "model": "gpt-oss:20b",
            "base_url": "http://localhost:11434",
            "keep_alive": "30m",
            "timeout": 300,
            "temperature": 0.1,
        },
        "llm_permissions": {
            "allow_create": True,
            "allow_update": True,
            "allow_delete": False,
            "require_confirmation": {"delete": True, "bulk_operations": True},
            "max_bulk_operations": 100,
            "read_only_mode": False,
        },
        "llm_prompts": {"override_system_prompt": None, "use_file": False, "file_path": None},
        "llm_context": {
            "mode": "adaptive",
            "max_conversation_history": 3,
            "max_context_tokens": 4000,
        },
        "llm_developer": {
            "debug_mode": False,
            "log_prompts": False,
            "log_responses": False,
            "log_timing": False,
        },
        "llm_tools": {"disabled": ["save_contacts_with_images", "list_memory"]},
    }
