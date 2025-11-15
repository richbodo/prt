"""
Mock Directory Generator for Test Isolation

This module provides a mock implementation of DirectoryGenerator that eliminates
file system dependencies during testing while maintaining the same interface.
"""

import json
from pathlib import Path

from prt_src.logging_config import get_logger

logger = get_logger(__name__)


class MockDirectoryGenerator:
    """Mock directory generator that simulates directory creation without file I/O."""

    def __init__(self, export_path: Path, output_path: Path, layout: str = "graph"):
        """Initialize mock directory generator.

        Args:
            export_path: Path to the export data (will be mocked)
            output_path: Path where directory would be created (will be mocked)
            layout: Layout type for the directory
        """
        self.export_path = export_path
        self.output_path = output_path
        self.layout = layout
        self.generated = False
        logger.debug(f"[MOCK_DIR] Initialized mock directory generator: {output_path}")

    def generate(self) -> bool:
        """Mock directory generation that always succeeds without file I/O.

        Returns:
            True to simulate successful generation
        """
        logger.debug(f"[MOCK_DIR] Mock generating directory at {self.output_path}")

        # Simulate reading export data
        if (
            self.export_path
            and (self.export_path / "contacts_with_images_search_results.json").exists()
        ):
            try:
                with open(self.export_path / "contacts_with_images_search_results.json") as f:
                    export_data = json.load(f)
                contact_count = len(export_data.get("results", []))
                logger.debug(f"[MOCK_DIR] Mock processed {contact_count} contacts from export")
            except Exception as e:
                logger.warning(f"[MOCK_DIR] Could not read export data: {e}")

        # Simulate successful directory creation without actual file operations
        self.generated = True
        logger.info(f"[MOCK_DIR] Mock directory generation completed for {self.output_path}")
        return True

    def get_output_path(self) -> Path:
        """Get the output path where directory would be created."""
        return self.output_path

    def was_generated(self) -> bool:
        """Check if the directory was generated."""
        return self.generated


def create_mock_directory_generator(
    export_path: Path, output_path: Path, layout: str = "graph"
) -> MockDirectoryGenerator:
    """Factory function to create mock directory generator instances.

    Args:
        export_path: Path to the export data
        output_path: Path where directory would be created
        layout: Layout type for the directory

    Returns:
        MockDirectoryGenerator instance
    """
    return MockDirectoryGenerator(export_path, output_path, layout)


class MockDirectoryGeneratorPatcher:
    """Context manager to patch DirectoryGenerator with mock implementation."""

    def __init__(self, mock_success: bool = True):
        """Initialize patcher.

        Args:
            mock_success: Whether mock generation should succeed
        """
        self.mock_success = mock_success
        self.original_generator = None
        self.generated_directories = []

    def __enter__(self):
        """Enter context with DirectoryGenerator patched."""
        # Import here to avoid circular imports during module loading
        from unittest.mock import patch

        def mock_generator_factory(*args, **kwargs):
            """Factory that creates mock generators."""
            mock_gen = MockDirectoryGenerator(*args, **kwargs)
            self.generated_directories.append(mock_gen)

            # Override generate method to control success/failure
            original_generate = mock_gen.generate

            def controlled_generate():
                if self.mock_success:
                    return original_generate()
                else:
                    logger.error(
                        f"[MOCK_DIR] Simulated generation failure for {mock_gen.output_path}"
                    )
                    return False

            mock_gen.generate = controlled_generate

            return mock_gen

        # Patch the DirectoryGenerator class in the make_directory module
        # This patches it where it's imported dynamically in the LLM code
        self.patcher = patch("make_directory.DirectoryGenerator", mock_generator_factory)
        self.patcher.start()

        logger.debug(
            f"[MOCK_DIR_PATCHER] DirectoryGenerator patched with mock (success={self.mock_success})"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore original DirectoryGenerator."""
        if hasattr(self, "patcher"):
            self.patcher.stop()
            logger.debug("[MOCK_DIR_PATCHER] DirectoryGenerator restored")

    def get_generated_directories(self) -> list:
        """Get list of directories that were generated during this context."""
        return self.generated_directories
