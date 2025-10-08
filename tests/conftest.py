import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from prt_src.db import create_database  # noqa: E402
from tests.fixtures import setup_test_database  # noqa: E402

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
            # Add mode attribute if the passed app kwarg has it
            if "app" in screen_kwargs and hasattr(screen_kwargs["app"], "mode"):
                self.mode = screen_kwargs["app"].mode
            else:
                self.mode = AppMode.NAVIGATION

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
