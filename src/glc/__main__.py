"""Command-line interface for counting lines in a Git working tree."""

import argparse
import subprocess
import sys
from contextlib import nullcontext
from pathlib import Path

from glc.core.line_stats import LineStats, count_lines, list_tracked_files
from glc.core.repository import cloned_repository, is_repo_url


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
        description="Count tracked files and lines in a local folder or Git repository URL."
    )
    parser.add_argument(
        "repo", nargs="?", default=".",
        help="local folder (default: current folder) or Git URL to clone temporarily",
    )
    parser.add_argument(
        "-t", "--types", action="store_true",
        help="show file and line percentages by extension",
    )
    checkout_options = parser.add_mutually_exclusive_group()
    checkout_options.add_argument(
        "--keep", metavar="DIR", type=Path,
        help="keep a URL's clone in this new or empty directory",
    )
    checkout_options.add_argument(
        "--pull", action="store_true",
        help="run git pull --ff-only before counting a local working tree",
    )
    args = parser.parse_args()

    remote = is_repo_url(args.repo)
    if remote:
        if args.pull:
            parser.error("--pull requires a local checkout. Use glc --pull DIR on a saved clone.")
        checkout = cloned_repository(args.repo, args.keep)
    else:
        if args.keep is not None:
            parser.error("--keep requires a Git URL to clone")
        repo = Path(args.repo)
        if not repo.is_dir():
            parser.error(f"folder does not exist or is not a directory: {repo}")
        checkout = nullcontext(repo)

    try:
        with checkout as repo:
            if args.pull:
                subprocess.run(
                    ["git", "pull", "--ff-only"], cwd=repo, capture_output=True, check=True,
                )
            files = list_tracked_files(repo)
            stats = count_lines(repo, files, confine_symlinks=remote or args.pull)
    except subprocess.CalledProcessError as error:
        message = error.stderr.decode("utf-8", errors="replace").strip()
        print(f"git {error.cmd[1]} failed: {message}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"Cannot access repository: {error}", file=sys.stderr)
        return 1

    print_report(stats, args.types)
    return 0


if __name__ == "__main__":
    sys.exit(main())
