import shutil
import subprocess
import sysconfig
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class GlcCommandTests(unittest.TestCase):
    def test_installed_command_counts_current_working_tree(self):
        command = shutil.which("glc", path=sysconfig.get_path("scripts"))
        self.assertIsNotNone(command, "Install GLC with poetry install before testing")
        with TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
            tracked = repo / "tracked.txt"
            tracked.write_text("first\n", encoding="utf-8")
            subprocess.run(["git", "add", "--", tracked.name], cwd=repo, check=True)
            tracked.write_text("first\nsecond\n", encoding="utf-8")
            (repo / "untracked.txt").write_text("ignored\n", encoding="utf-8")

            result = subprocess.run(
                [command], cwd=repo, capture_output=True, text=True, check=True
            )

        self.assertEqual(
            result.stdout.splitlines(), ["Total tracked files: 1", "Total lines: 2"]
        )
