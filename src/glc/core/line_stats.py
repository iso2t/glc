"""Collect line counts for files tracked by Git."""

from __future__ import annotations

import os
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class LineStats:
    total_files: int = 0
    total_lines: int = 0
    files_by_type: Counter[str] = field(default_factory=Counter)
    lines_by_type: Counter[str] = field(default_factory=Counter)
    skipped_files: dict[str, str] = field(default_factory=dict)


def list_tracked_files(repo: Path) -> list[str]:
    """Return unique tracked paths relative to the given folder."""
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo,
        capture_output=True,
        check=True,
    )
    return list(dict.fromkeys(
        os.fsdecode(name) for name in result.stdout.split(b"\0") if name
    ))


def count_lines(repo: Path, files: Iterable[str], *, confine_symlinks: bool = False) -> LineStats:
    """Count working-tree lines, optionally confining symlinks to the scanned folder."""
    stats = LineStats()
    root = repo.resolve() if confine_symlinks else None
    for file_path in files:
        path = repo / file_path
        extension = path.suffix.lower() or "(no extension)"
        stats.total_files += 1
        stats.files_by_type[extension] += 1

        try:
            if root is not None:
                try:
                    path = path.resolve(strict=True)
                    path.relative_to(root)
                except (ValueError, RuntimeError):
                    stats.skipped_files[file_path] = "path does not resolve inside the checkout"
                    continue
            with path.open("r", encoding="utf-8", errors="replace") as file:
                line_count = sum(1 for _ in file)
        except OSError as error:
            stats.skipped_files[file_path] = error.strerror or str(error)
            continue

        stats.total_lines += line_count
        stats.lines_by_type[extension] += line_count

    return stats
