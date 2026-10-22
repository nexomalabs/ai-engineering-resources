# Applied AI Engineering, Volume IV, Chapter 4
# Section 4.3, Trigger-Based Automation
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import asyncio
import os
from pathlib import Path
from typing import Callable, Awaitable
import logging

logger = logging.getLogger(__name__)

class FileWatcher:
    """Watch a directory for new files and trigger a handler."""

    def __init__(
        self,
        watch_dir: str,
        handler: Callable[[Path], Awaitable[None]],
        poll_interval: float = 2.0,
        file_extensions: tuple[str, ...] = (".pdf", ".docx", ".txt"),
    ):
        self.watch_dir = Path(watch_dir)
        self.handler = handler
        self.poll_interval = poll_interval
        self.file_extensions = file_extensions
        self._seen_files: set[str] = set()
        self._running = False

    async def start(self) -> None:
        """Begin watching the directory."""
        self._running = True
        # Seed seen files (don't process existing files on startup)
        for f in self.watch_dir.iterdir():
            if f.suffix in self.file_extensions:
                self._seen_files.add(str(f))
        logger.info("FileWatcher started: watching %s", self.watch_dir)
        while self._running:
            await self._check_for_new_files()
            await asyncio.sleep(self.poll_interval)

    async def _check_for_new_files(self) -> None:
        try:
            for filepath in self.watch_dir.iterdir():
                if (filepath.suffix in self.file_extensions
                        and str(filepath) not in self._seen_files):
                    self._seen_files.add(str(filepath))
                    logger.info("New file detected: %s", filepath.name)
                    asyncio.create_task(self._safe_handle(filepath))
        except OSError as exc:
            logger.error("Error scanning watch directory: %s", exc)

    async def _safe_handle(self, filepath: Path) -> None:
        try:
            await self.handler(filepath)
        except Exception as exc:
            logger.error("Handler failed for %s: %s", filepath.name, exc)

    def stop(self) -> None:
        self._running = False
