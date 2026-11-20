"""Command-line interface for counting lines in a Git working tree."""

import argparse
import subprocess
import sys
from pathlib import Path

from glc.core.line_stats import LineStats, count_lines, list_tracked_files


def print_report(stats: LineStats, show_types: bool) -> None:
    for file_path, message in stats.skipped_files.items():
        print(f"Skipping {file_path!r}: {message}", file=sys.stderr)

    print(f"Total tracked files: {stats.total_files}")
    print(f"Total lines: {stats.total_lines}")
    if stats.skipped_files:
        print(f"Tracked files skipped: {len(stats.skipped_files)}")

    if not show_types or not stats.files_by_type:
        return

    print()
    print(f"{'Extension':<16} {'Files':>8} {'File %':>8} {'Lines':>10} {'Line %':>8}")
    for extension, file_count in stats.files_by_type.most_common():
        line_count = stats.lines_by_type[extension]
        file_share = file_count / stats.total_files
        line_share = line_count / stats.total_lines if stats.total_lines else 0.0
        print(
            f"{extension:<16} {file_count:>8,} {file_share:>8.1%} "
            f"{line_count:>10,} {line_share:>8.1%}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Count tracked files and lines in a Git working tree."
    )
    parser.add_argument(
        "repo", nargs="?", type=Path, default=Path("."),
        help="folder to scan (defaults to the current folder)",
    )
    parser.add_argument(
        "-t", "--types", action="store_true",
        help="show file and line percentages by extension",
    )
    args = parser.parse_args()

    if not args.repo.is_dir():
        parser.error(f"folder does not exist or is not a directory: {args.repo}")

    try:
        files = list_tracked_files(args.repo)
    except subprocess.CalledProcessError as error:
        message = error.stderr.decode("utf-8", errors="replace").strip()
        print(f"Cannot list tracked files in {args.repo}: {message}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"Cannot run Git in {args.repo}: {error}", file=sys.stderr)
        return 1

    print_report(count_lines(args.repo, files), args.types)
    return 0


if __name__ == "__main__":
    sys.exit(main())
