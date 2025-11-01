"""Google Takeout service for TUI.

Provides async interface for Google Takeout contact import functionality.
"""

import asyncio
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from prt_src.google_takeout import GoogleTakeoutParser
from prt_src.google_takeout import find_takeout_files
from prt_src.google_takeout import parse_takeout_contacts
from prt_src.logging_config import get_logger

logger = get_logger(__name__)


class GoogleTakeoutService:
    """Service for handling Google Takeout import operations in TUI."""

    def __init__(self, api):
        """Initialize the service.

        Args:
            api: PRTAPI instance for database operations
        """
        self.api = api
        self.logger = get_logger(__name__)

    async def find_takeout_files(self) -> List[Path]:
        """Find Google Takeout files in common locations.

        Searches in:
        - ~/Downloads
        - Current directory
        - prt_data/ directory

        Returns:
            List of Path objects for found takeout files
        """
        import time

        start_time = time.time()
        self.logger.info("[TAKEOUT] Starting file search")

        # Run in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        search_paths = [
            Path.home() / "Downloads",
            Path.cwd(),
            Path("prt_data"),
        ]
        self.logger.debug(f"[TAKEOUT] Search paths: {[str(p) for p in search_paths]}")

        all_files = []
        for search_path in search_paths:
            if search_path.exists():
                try:
                    self.logger.debug(f"[TAKEOUT] Searching in: {search_path}")
                    files = await loop.run_in_executor(None, find_takeout_files, search_path)
                    self.logger.info(f"[TAKEOUT] Found {len(files)} file(s) in {search_path}")
                    all_files.extend(files)
                except Exception as e:
                    self.logger.error(
                        f"[TAKEOUT] Error searching {search_path}: {e}",
                        exc_info=True,
                        extra={"search_path": str(search_path)},
                    )
            else:
                self.logger.debug(f"[TAKEOUT] Path does not exist: {search_path}")

        # Remove duplicates while preserving order
        seen = set()
        unique_files = []
        for file in all_files:
            file_abs = file.resolve()
            if file_abs not in seen:
                seen.add(file_abs)
                unique_files.append(file)

        elapsed = time.time() - start_time
        self.logger.info(
            f"[TAKEOUT] File search complete: {len(unique_files)} unique file(s) found in {elapsed:.2f}s"
        )
        return unique_files

    async def validate_file(self, file_path: Path) -> Tuple[bool, str]:
        """Validate that a file is a valid Google Takeout zip.

        Args:
            file_path: Path to the zip file to validate

        Returns:
            Tuple of (is_valid, message)
        """
        self.logger.info(f"[TAKEOUT] Validating file: {file_path.name}")
        self.logger.debug(f"[TAKEOUT] Full path: {file_path}")

        if not file_path.exists():
            self.logger.warning(f"[TAKEOUT] Validation failed: File not found at {file_path}")
            return False, f"File not found: {file_path}"

        if file_path.suffix.lower() != ".zip":
            self.logger.warning(
                f"[TAKEOUT] Validation failed: Not a zip file (suffix: {file_path.suffix})"
            )
            return False, "File must be a zip file"

        # Run validation in executor
        loop = asyncio.get_event_loop()
        try:
            parser = GoogleTakeoutParser(file_path)
            is_valid, message = await loop.run_in_executor(None, parser.validate_takeout_file)

            if is_valid:
                self.logger.info(f"[TAKEOUT] Validation passed: {message}")
            else:
                self.logger.warning(f"[TAKEOUT] Validation failed: {message}")

            return is_valid, message
        except Exception as e:
            self.logger.error(
                f"[TAKEOUT] Error validating file: {e}",
                exc_info=True,
                extra={"file_path": str(file_path)},
            )
            return False, f"Error validating file: {e}"

    async def get_preview(self, file_path: Path) -> Dict[str, Any]:
        """Get preview information about a takeout file.

        Args:
            file_path: Path to the takeout zip file

        Returns:
            Dictionary with preview info:
            - valid: bool
            - contact_count: int
            - image_count: int
            - contacts_with_images: int
            - sample_contacts: list
            - message: str
            - error: str (if not valid)
        """
        import time

        start_time = time.time()
        self.logger.info(f"[TAKEOUT] Getting preview for: {file_path.name}")

        loop = asyncio.get_event_loop()
        try:
            parser = GoogleTakeoutParser(file_path)
            preview = await loop.run_in_executor(None, parser.get_preview_info)

            elapsed = time.time() - start_time
            if preview.get("valid"):
                self.logger.info(
                    f"[TAKEOUT] Preview complete: {preview.get('contact_count', 0)} contacts, "
                    f"{preview.get('contacts_with_images', 0)} with images ({elapsed:.2f}s)"
                )
                self.logger.debug(f"[TAKEOUT] Preview details: {preview}")
            else:
                self.logger.warning(
                    f"[TAKEOUT] Preview failed: {preview.get('error', 'Unknown error')} ({elapsed:.2f}s)"
                )

            return preview
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(
                f"[TAKEOUT] Error getting preview after {elapsed:.2f}s: {e}",
                exc_info=True,
                extra={"file_path": str(file_path)},
            )
            return {
                "valid": False,
                "error": f"Error reading file: {e}",
                "contact_count": 0,
                "image_count": 0,
                "sample_contacts": [],
            }

    async def import_contacts(self, file_path: Path) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Import contacts from a Google Takeout file.

        Args:
            file_path: Path to the takeout zip file

        Returns:
            Tuple of (success, message, info_dict)
            - success: bool indicating if import succeeded
            - message: Human-readable status message
            - info_dict: Dictionary with import statistics (contact_count, etc.)
        """
        import time

        start_time = time.time()
        self.logger.info(f"[TAKEOUT] Starting import from: {file_path.name}")

        try:
            # Log file info
            file_size_mb = file_path.stat().st_size / 1024 / 1024
            self.logger.debug(f"[TAKEOUT] File size: {file_size_mb:.1f} MB")
            self.logger.debug(f"[TAKEOUT] Full path: {file_path}")

            # Parse contacts from takeout file
            parse_start = time.time()
            self.logger.debug("[TAKEOUT] Starting contact parsing...")

            loop = asyncio.get_event_loop()
            contacts, info = await loop.run_in_executor(None, parse_takeout_contacts, file_path)

            parse_elapsed = time.time() - parse_start
            self.logger.info(
                f"[TAKEOUT] Parsing complete: {len(contacts)} contacts in {parse_elapsed:.2f}s"
            )
            self.logger.debug(f"[TAKEOUT] Parse info: {info}")

            if "error" in info:
                error_msg = f"Error parsing takeout file: {info['error']}"
                self.logger.error(
                    f"[TAKEOUT] {error_msg}",
                    extra={"file_path": str(file_path), "info": info},
                )
                return False, error_msg, None

            if not contacts:
                msg = "No contacts found in the takeout file"
                self.logger.warning(f"[TAKEOUT] {msg}", extra={"info": info})
                return False, msg, info

            # Insert contacts into database
            insert_start = time.time()
            self.logger.debug(f"[TAKEOUT] Starting database insert of {len(contacts)} contacts...")

            success = await loop.run_in_executor(None, self.api.insert_contacts, contacts)

            insert_elapsed = time.time() - insert_start
            total_elapsed = time.time() - start_time

            if success:
                msg = f"Successfully imported {len(contacts)} contacts"
                self.logger.info(
                    f"[TAKEOUT] Import successful: {len(contacts)} contacts in {total_elapsed:.2f}s "
                    f"(parse: {parse_elapsed:.2f}s, insert: {insert_elapsed:.2f}s)"
                )
                # Add timing info to result
                info["parse_time"] = parse_elapsed
                info["insert_time"] = insert_elapsed
                info["total_time"] = total_elapsed
                info["source_file"] = str(file_path)
                return True, msg, info
            else:
                msg = "Failed to import contacts to database"
                self.logger.error(
                    f"[TAKEOUT] {msg} after {total_elapsed:.2f}s",
                    extra={"contact_count": len(contacts), "file_path": str(file_path)},
                )
                return False, msg, info

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = f"Error importing contacts: {e}"
            self.logger.error(
                f"[TAKEOUT] Import failed after {elapsed:.2f}s: {e}",
                exc_info=True,
                extra={"file_path": str(file_path)},
            )
            return False, error_msg, None

    def get_search_instructions(self) -> str:
        """Get instructions for where to place takeout files.

        Returns:
            Formatted instruction string
        """
        return """To import contacts:

1. Go to https://takeout.google.com
2. Select 'Contacts' only (deselect everything else)
3. Choose 'Export once' and download the zip file
4. Place the zip file in one of these locations:
   • ~/Downloads
   • Current directory where you run PRT
   • prt_data/ directory

Then return to this screen to import."""
