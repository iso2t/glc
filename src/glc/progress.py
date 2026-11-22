"""Transient terminal progress for the GLC command."""

from __future__ import annotations

import os
from itertools import count
from threading import Event, Lock, Thread
from typing import Iterator, Optional, Sequence, TextIO


class ProgressBar:
    def __init__(self, stream: TextIO, message: str) -> None:
        self._stream = stream
        self._status: tuple[str, int, Optional[int]] = (message, 0, None)
        self._lock = Lock()
        self._stop = Event()
        self._thread: Optional[Thread] = None

    def __enter__(self) -> ProgressBar:
        if self._stream.isatty():
            self._thread = Thread(target=self._animate, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self._thread is not None:
            self._stop.set()
            self._thread.join()

    def update(self, message: str, completed: int = 0, total: Optional[int] = None) -> None:
        with self._lock:
            self._status = (message, completed, total)

    def track_files(self, files: Sequence[str]) -> Iterator[str]:
        if self._thread is None:
            yield from files
            return

        total = len(files)
        self.update("Counting lines", 0, total)
        for completed, path in enumerate(files, 1):
            yield path
            self.update("Counting lines", completed, total)

    def _frame(self, tick: int) -> str:
        with self._lock:
            message, completed, total = self._status
        width = 14
        if total is None:
            travel = width - 3
            offset = travel - abs(tick % (2 * travel) - travel)
            bar = " " * offset + "==="
        else:
            filled = width * completed // total if total else width
            spinner = "|/-\\"[tick % 4]
            bar = ("=" * filled + spinner)[:width]
            unit = "file" if total == 1 else "files"
            message += f" ({completed:,}/{total:,} {unit})"
        return f"[{bar:<{width}}] {message}"

    def _animate(self) -> None:
        if self._stop.wait(0.4):
            return

        previous_width = 0
        for tick in count():
            try:
                columns = os.get_terminal_size(self._stream.fileno()).columns
            except OSError:
                columns = 80
            # Writing in the last column can wrap the status onto a second row.
            available = (columns or 80) - 1
            line = self._frame(tick)[:available]
            self._stream.write("\r" + line.ljust(min(previous_width, available)))
            self._stream.flush()
            previous_width = len(line)
            if self._stop.wait(0.1):
                break

        self._stream.write("\r" + " " * previous_width + "\r")
        self._stream.flush()
