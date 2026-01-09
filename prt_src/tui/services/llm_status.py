"""LLM Status Checking Service for PRT TUI.

This service provides real-time status checking for LLM availability,
with caching and background updates to minimize performance impact.
"""

import asyncio
import contextlib
import time
from collections.abc import Callable
from enum import Enum

from prt_src.llm_ollama import OllamaLLM
from prt_src.logging_config import get_logger

logger = get_logger(__name__)


class LLMStatus(Enum):
    """LLM availability status."""

    ONLINE = "online"
    OFFLINE = "offline"
    CHECKING = "checking"
    ERROR = "error"


class LLMStatusChecker:
    """Service for checking and monitoring LLM availability."""

    def __init__(self, ollama_llm: OllamaLLM | None = None, check_interval: float = 30.0):
        """Initialize the LLM status checker.

        Args:
            ollama_llm: OllamaLLM instance to check. If None, will be lazy-loaded.
            check_interval: How often to check status in background (seconds)
        """
        self.ollama_llm = ollama_llm
        self.check_interval = check_interval
        self._status = LLMStatus.CHECKING
        self._last_check_time = 0.0
        self._cache_duration = 5.0  # Cache status for 5 seconds
        self._status_callbacks = []
        self._background_task = None

    def add_status_callback(self, callback: Callable[[LLMStatus], None]) -> None:
        """Add a callback to be notified of status changes.

        Args:
            callback: Function to call when status changes
        """
        self._status_callbacks.append(callback)

    def remove_status_callback(self, callback: Callable[[LLMStatus], None]) -> None:
        """Remove a status change callback.

        Args:
            callback: Function to remove from callbacks
        """
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)

    def _notify_status_change(self, new_status: LLMStatus) -> None:
        """Notify all callbacks of status change.

        Args:
            new_status: The new LLM status
        """
        if new_status != self._status:
            logger.debug(f"LLM status changed: {self._status.value} -> {new_status.value}")
            self._status = new_status

            for callback in self._status_callbacks:
                try:
                    callback(new_status)
                except Exception as e:
                    logger.error(f"Error in status callback: {e}")

    async def get_status(self, force_check: bool = False) -> LLMStatus:
        """Get current LLM status, using cache if available.

        Args:
            force_check: If True, bypass cache and check immediately

        Returns:
            Current LLM status
        """
        current_time = time.time()

        # Use cached status if recent enough and not forcing
        if not force_check and (current_time - self._last_check_time) < self._cache_duration:
            return self._status

        # Perform actual status check
        return await self._check_status()

    async def _check_status(self) -> LLMStatus:
        """Perform actual status check against Ollama.

        Returns:
            Current LLM status
        """
        try:
            # Lazy-load Ollama LLM if needed
            if self.ollama_llm is None:
                from prt_src.api import PRTAPI

                api = PRTAPI()
                self.ollama_llm = OllamaLLM(api)

            # Set status to checking
            if self._status != LLMStatus.CHECKING:
                self._notify_status_change(LLMStatus.CHECKING)

            # Perform health check
            is_healthy = await self.ollama_llm.health_check(timeout=2.0)
            new_status = LLMStatus.ONLINE if is_healthy else LLMStatus.OFFLINE

            # Update cache
            self._last_check_time = time.time()
            self._notify_status_change(new_status)

            return new_status

        except Exception as e:
            logger.error(f"Error checking LLM status: {e}")
            self._notify_status_change(LLMStatus.ERROR)
            return LLMStatus.ERROR

    def get_status_display(self, status: LLMStatus | None = None) -> tuple[str, str]:
        """Get display text and CSS class for status.

        Args:
            status: Status to get display for. If None, uses current status.

        Returns:
            Tuple of (display_text, css_class)
        """
        if status is None:
            status = self._status

        status_map = {
            LLMStatus.ONLINE: ("✅ LLM: Online", "llm-status-online"),
            LLMStatus.OFFLINE: ("❌ LLM: Offline", "llm-status-offline"),
            LLMStatus.CHECKING: ("⚠️ LLM: Checking...", "llm-status-checking"),
            LLMStatus.ERROR: ("⚠️ LLM: Error", "llm-status-error"),
        }

        return status_map.get(status, ("❓ LLM: Unknown", "llm-status-unknown"))

    async def start_background_monitoring(self) -> None:
        """Start background task to periodically check LLM status."""
        if self._background_task is not None:
            return  # Already running

        self._background_task = asyncio.create_task(self._background_monitor())
        logger.info("Started LLM status background monitoring")

    async def stop_background_monitoring(self) -> None:
        """Stop background status monitoring."""
        if self._background_task is not None:
            self._background_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._background_task
            self._background_task = None
            logger.info("Stopped LLM status background monitoring")

    async def _background_monitor(self) -> None:
        """Background task to periodically check status."""
        try:
            while True:
                await asyncio.sleep(self.check_interval)
                await self._check_status()
        except asyncio.CancelledError:
            logger.debug("Background monitoring cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in background monitoring: {e}")
