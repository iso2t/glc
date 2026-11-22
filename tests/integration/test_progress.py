import io
import subprocess
import sys
import unittest
from threading import Event
from unittest.mock import patch

from glc import __main__ as cli
from glc.core.line_stats import LineStats


class RecordingTerminal(io.StringIO):
    def __init__(self, status):
        super().__init__()
        self.status = status
        self.frames = []
        self.animated = Event()

    def isatty(self):
        return True

    def write(self, text):
        written = super().write(text)
        if self.status in text:
            self.frames.append(text)
            if len(self.frames) == 2:
                self.animated.set()
        return written


class ProgressTests(unittest.TestCase):
    def run_cli(self, terminal):
        with patch.multiple(sys, stdout=terminal, stderr=terminal, argv=["glc"]):
            return cli.main()

    def assert_replaced(self, terminal, expected_output):
        frames, erase, output = terminal.getvalue().rsplit("\r", 2)
        self.assertNotEqual(terminal.frames[0], terminal.frames[1])
        self.assertNotIn("\n", frames)
        self.assertEqual(erase, " " * len(frames.rsplit("\r", 1)[-1].rstrip()))
        self.assertEqual(output, expected_output)

    def test_slow_scan_counts_completed_files_and_clears_before_the_report(self):
        terminal = RecordingTerminal("Counting lines (1/2 files)")

        def slow_count(repo, files, *, confine_symlinks):
            for path in files:
                if path == "second.txt":
                    self.assertTrue(terminal.animated.wait(5), "No animation during file read")
            return LineStats(total_files=2, total_lines=3)

        with patch.object(cli, "list_tracked_files", return_value=["first.txt", "second.txt"]):
            with patch.object(cli, "count_lines", slow_count):
                self.assertEqual(self.run_cli(terminal), 0)

        self.assert_replaced(terminal, "Total tracked files: 2\nTotal lines: 3\n")

    def test_slow_git_failure_clears_before_the_error(self):
        terminal = RecordingTerminal("Listing tracked files")

        def failed_listing(repo):
            self.assertTrue(terminal.animated.wait(5), "No animation while waiting for Git")
            raise subprocess.CalledProcessError(1, ["git", "ls-files"], stderr=b"test failure")

        with patch.object(cli, "list_tracked_files", failed_listing):
            self.assertEqual(self.run_cli(terminal), 1)

        self.assert_replaced(terminal, "git ls-files failed: test failure\n")

    def test_quick_terminal_scan_only_prints_the_report(self):
        terminal = RecordingTerminal("Counting lines")
        with patch.object(cli, "list_tracked_files", return_value=[]):
            self.assertEqual(self.run_cli(terminal), 0)
        self.assertEqual(terminal.getvalue(), "Total tracked files: 0\nTotal lines: 0\n")
