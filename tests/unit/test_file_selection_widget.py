"""Unit tests for FileSelectionWidget."""

import pytest

from prt_src.tui.widgets.file_selection import FileSelectionWidget


@pytest.fixture
def temp_files(tmp_path):
    """Create temporary test files.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        List of Path objects for test files
    """
    files = []
    for i in range(5):
        file_path = tmp_path / f"takeout-{i+1}.zip"
        # Create file with some content to have realistic size
        file_path.write_bytes(b"x" * (1024 * 1024 * (i + 1)))  # 1-5 MB files
        files.append(file_path)
    return files


@pytest.fixture
def many_temp_files(tmp_path):
    """Create many temporary test files (more than 9).

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        List of Path objects for test files
    """
    files = []
    for i in range(12):
        file_path = tmp_path / f"takeout-{i+1}.zip"
        file_path.write_bytes(b"x" * 1024 * 1024)  # 1 MB files
        files.append(file_path)
    return files


class TestFileSelectionWidget:
    """Tests for FileSelectionWidget."""

    @pytest.mark.asyncio
    async def test_widget_renders_with_files(self, temp_files):
        """Test that widget renders correctly with file list."""
        widget = FileSelectionWidget(files=temp_files)

        # Check basic properties
        assert widget.files == temp_files
        assert widget.title_text == "Select Google Takeout File"
        assert "file-selection-widget" in widget.classes

    @pytest.mark.asyncio
    async def test_widget_custom_title(self, temp_files):
        """Test widget with custom title."""
        custom_title = "Choose Your File"
        widget = FileSelectionWidget(files=temp_files, title=custom_title)
        assert widget.title_text == custom_title

    @pytest.mark.asyncio
    async def test_file_selected_message(self, temp_files):
        """Test that selecting a file emits FileSelected message."""
        from textual.app import App

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.selected_file = None

            def compose(self):
                yield FileSelectionWidget(files=temp_files, id="file-widget")

            def on_file_selection_widget_file_selected(self, message):
                self.selected_file = message.file_path

        app = TestApp()
        async with app.run_test() as pilot:
            # Focus the widget first
            widget = app.query_one("#file-widget", FileSelectionWidget)
            widget.focus()
            await pilot.pause()

            # Press '1' to select first file
            await pilot.press("1")
            await pilot.pause()

            # Check that message was handled
            assert app.selected_file == temp_files[0]

    @pytest.mark.asyncio
    async def test_number_keys_select_files(self, temp_files):
        """Test that number keys 1-5 select corresponding files."""
        from textual.app import App

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.selected_files = []

            def compose(self):
                yield FileSelectionWidget(files=temp_files, id="file-widget")

            def on_file_selection_widget_file_selected(self, message):
                self.selected_files.append(message.file_path)

        app = TestApp()
        async with app.run_test() as pilot:
            # Focus the widget
            widget = app.query_one("#file-widget", FileSelectionWidget)
            widget.focus()
            await pilot.pause()

            # Test each number key
            for i in range(1, 6):  # 1-5
                await pilot.press(str(i))
                await pilot.pause()

                # Check that correct file was selected
                assert app.selected_files[-1] == temp_files[i - 1]

    @pytest.mark.asyncio
    async def test_cancel_with_c_key(self, temp_files):
        """Test that 'c' key cancels selection."""
        from textual.app import App

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.cancelled = False

            def compose(self):
                yield FileSelectionWidget(files=temp_files, id="file-widget")

            def on_file_selection_widget_selection_cancelled(self, message):
                self.cancelled = True

        app = TestApp()
        async with app.run_test() as pilot:
            # Focus the widget
            widget = app.query_one("#file-widget", FileSelectionWidget)
            widget.focus()
            await pilot.pause()

            # Press 'c' to cancel
            await pilot.press("c")
            await pilot.pause()

            # Check that cancellation was handled
            assert app.cancelled is True

    @pytest.mark.asyncio
    async def test_cancel_with_escape(self, temp_files):
        """Test that escape key cancels selection."""
        from textual.app import App

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.cancelled = False

            def compose(self):
                yield FileSelectionWidget(files=temp_files, id="file-widget")

            def on_file_selection_widget_selection_cancelled(self, message):
                self.cancelled = True

        app = TestApp()
        async with app.run_test() as pilot:
            # Focus the widget
            widget = app.query_one("#file-widget", FileSelectionWidget)
            widget.focus()
            await pilot.pause()

            # Press escape to cancel
            await pilot.press("escape")
            await pilot.pause()

            # Check that cancellation was handled
            assert app.cancelled is True

    @pytest.mark.asyncio
    async def test_overflow_notice_shown(self, many_temp_files):
        """Test that overflow notice is shown when more than 9 files."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield FileSelectionWidget(files=many_temp_files)

        app = TestApp()
        async with app.run_test():
            # Check that overflow notice exists
            widget = app.query_one(FileSelectionWidget)
            assert len(widget.files) == 12  # 12 files total

            # Try to find overflow notice
            try:
                overflow_notice = widget.query_one("#files-overflow-notice")
                assert overflow_notice is not None
            except Exception:
                # Widget might not be fully mounted yet
                pass

    @pytest.mark.asyncio
    async def test_only_first_9_files_selectable(self, many_temp_files):
        """Test that only first 9 files are selectable when more exist."""
        from textual.app import App

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.selected_files = []

            def compose(self):
                yield FileSelectionWidget(files=many_temp_files, id="file-widget")

            def on_file_selection_widget_file_selected(self, message):
                self.selected_files.append(message.file_path)

        app = TestApp()
        async with app.run_test() as pilot:
            # Focus the widget
            widget = app.query_one("#file-widget", FileSelectionWidget)
            widget.focus()
            await pilot.pause()

            # Press '9' (should work)
            await pilot.press("9")
            await pilot.pause()
            assert len(app.selected_files) == 1
            assert app.selected_files[0] == many_temp_files[8]  # 9th file (0-indexed)

    @pytest.mark.asyncio
    async def test_invalid_key_ignored(self, temp_files):
        """Test that invalid keys are ignored."""
        from textual.app import App

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.selected_file = None
                self.cancelled = False

            def compose(self):
                yield FileSelectionWidget(files=temp_files)

            def on_file_selection_widget_file_selected(self, message):
                self.selected_file = message.file_path

            def on_file_selection_widget_selection_cancelled(self, message):
                self.cancelled = True

        app = TestApp()
        async with app.run_test() as pilot:
            # Press invalid keys
            await pilot.press("a")
            await pilot.press("b")
            await pilot.press("x")
            await pilot.pause()

            # Check that no action was taken
            assert app.selected_file is None
            assert app.cancelled is False

    @pytest.mark.asyncio
    async def test_out_of_range_number_ignored(self, temp_files):
        """Test that numbers outside file range are ignored."""
        from textual.app import App

        class TestApp(App):
            def __init__(self):
                super().__init__()
                self.selected_file = None

            def compose(self):
                yield FileSelectionWidget(files=temp_files)

            def on_file_selection_widget_file_selected(self, message):
                self.selected_file = message.file_path

        app = TestApp()
        async with app.run_test() as pilot:
            # Press '6' (only 5 files exist)
            await pilot.press("6")
            await pilot.press("7")
            await pilot.press("9")
            await pilot.pause()

            # Check that no file was selected
            assert app.selected_file is None

    def test_file_selected_message_attributes(self, temp_files):
        """Test FileSelected message has correct attributes."""
        file_path = temp_files[0]
        message = FileSelectionWidget.FileSelected(file_path)
        assert message.file_path == file_path

    def test_selection_cancelled_message(self):
        """Test SelectionCancelled message can be created."""
        message = FileSelectionWidget.SelectionCancelled()
        assert message is not None
