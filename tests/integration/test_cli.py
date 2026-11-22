import os
import shutil
import subprocess
import sysconfig
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class GlcCommandTests(unittest.TestCase):
    def setUp(self):
        self.command = shutil.which("glc", path=sysconfig.get_path("scripts"))
        self.assertIsNotNone(self.command, "Install GLC with poetry install before testing")
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.scratch = self.root / "temp"
        self.scratch.mkdir()
        self.env = os.environ.copy()
        for variable in ("TMPDIR", "TEMP", "TMP"):
            self.env[variable] = str(self.scratch)

    def glc(self, *args, cwd=None, check=True):
        return subprocess.run(
            [self.command, *map(str, args)], cwd=cwd or self.root, env=self.env,
            capture_output=True, text=True, check=check,
        )

    def git(self, repo, *args, input_text=None):
        return subprocess.run(
            ["git", *args], cwd=repo, input=input_text, capture_output=True, text=True, check=True,
        ).stdout.strip()

    def commit(self, repo, message):
        self.git(
            repo, "-c", "user.name=GLC Test", "-c", "user.email=glc@example.org",
            "commit", "--no-gpg-sign", "-qm", message,
        )

    def commit_text(self, repo, content):
        (repo / "tracked.txt").write_text(content, encoding="utf-8")
        self.git(repo, "add", "--", "tracked.txt")
        self.commit(repo, "Update tracked file")

    def make_origin(self):
        repo = self.root / "origin with spaces"
        repo.mkdir()
        self.git(repo, "init", "--quiet")
        self.commit_text(repo, "first\n")
        return repo

    def test_installed_command_counts_current_working_tree(self):
        repo = self.root
        self.git(repo, "init", "--quiet")
        tracked = repo / "tracked.txt"
        tracked.write_text("first\n", encoding="utf-8")
        self.git(repo, "add", "--", tracked.name)
        tracked.write_text("first\nsecond\n", encoding="utf-8")
        (repo / "untracked.txt").write_text("ignored\n", encoding="utf-8")

        result = self.glc(cwd=repo)

        self.assertEqual(
            result.stdout.splitlines(), ["Total tracked files: 1", "Total lines: 2"]
        )
        self.assertEqual(result.stderr, "")

    def test_url_counts_committed_lines_and_removes_temporary_clone(self):
        repo = self.make_origin()
        (repo / "tracked.txt").write_text("uncommitted\nedits\n", encoding="utf-8")

        result = self.glc(repo.as_uri(), "--types")

        self.assertEqual(
            result.stdout.splitlines()[:2], ["Total tracked files: 1", "Total lines: 1"]
        )
        self.assertRegex(result.stdout, r"\.txt\s+1\s+100\.0%\s+1\s+100\.0%")
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_failed_clone_cleans_up_and_reports_the_error(self):
        result = self.glc((self.root / "missing.git").as_uri(), check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("git clone failed", result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(list(self.scratch.iterdir()), [])

    def test_url_scan_does_not_read_through_an_external_symlink(self):
        origin = self.make_origin()
        outside = self.root / "outside.txt"
        outside.write_text("outside\n" * 10, encoding="utf-8")
        # Stage a Git symlink even on filesystems that check links out as plain text.
        target = self.git(origin, "hash-object", "-w", "--stdin", input_text=outside.as_posix())
        self.git(origin, "update-index", "--add", "--cacheinfo", f"120000,{target},link.txt")
        self.commit(origin, "Add symbolic link")
        saved = self.root / "saved"

        result = self.glc(origin.as_uri(), "--keep", saved)

        if (saved / "link.txt").is_symlink():
            self.assertIn("Tracked files skipped: 1", result.stdout)
            self.assertIn("Total lines: 1", result.stdout.splitlines())
        else:
            self.assertIn("Total lines: 2", result.stdout.splitlines())

    def test_keep_saves_shallow_clone_and_pull_updates_it(self):
        origin = self.make_origin()
        self.commit_text(origin, "second revision\n")
        saved = self.root / "saved clone"

        first = self.glc(origin.as_uri(), "--keep", saved)
        self.assertEqual(self.git(saved, "rev-list", "--count", "HEAD"), "1")
        self.assertIn("Total lines: 1", first.stdout)
        self.commit_text(origin, "first\nsecond\n")
        self.assertEqual(self.glc(saved).stdout, first.stdout)

        updated = self.glc("--pull", saved)

        self.assertEqual(
            updated.stdout.splitlines(), ["Total tracked files: 1", "Total lines: 2"]
        )
        self.assertEqual(
            self.git(saved, "rev-parse", "HEAD"), self.git(origin, "rev-parse", "HEAD")
        )

    def test_keep_leaves_an_occupied_destination_intact(self):
        origin = self.make_origin()
        saved = self.root / "occupied"
        saved.mkdir()
        existing = saved / "existing.txt"
        existing.write_text("keep this", encoding="utf-8")

        result = self.glc(origin.as_uri(), "--keep", saved, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(list(saved.iterdir()), [existing])
        self.assertEqual(existing.read_text(encoding="utf-8"), "keep this")

    def test_failed_pull_preserves_local_commit_and_skips_count(self):
        origin = self.make_origin()
        saved = self.root / "saved"
        self.glc("--keep", saved, origin.as_uri())
        self.commit_text(saved, "local change\n")
        self.commit_text(origin, "upstream change\n")
        local_head = self.git(saved, "rev-parse", "HEAD")

        result = self.glc("--pull", cwd=saved, check=False)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("git pull failed", result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(self.git(saved, "rev-parse", "HEAD"), local_head)
        self.assertEqual((saved / "tracked.txt").read_text(encoding="utf-8"), "local change\n")

    def test_checkout_flags_require_the_appropriate_source(self):
        for args, message in (
            (("--keep", "saved", self.root), "--keep requires a Git URL"),
            (("--pull", "git@example.org:owner/repo.git"), "--pull requires a local checkout"),
        ):
            with self.subTest(args=args):
                result = self.glc(*args, check=False)
                self.assertEqual(result.returncode, 2)
                self.assertIn(message, result.stderr)
