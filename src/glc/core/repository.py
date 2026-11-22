"""Open a Git URL as a temporary or retained working tree."""

import os
import re
import shutil
import stat
import subprocess
import sys
from contextlib import ExitStack, contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory, mkdtemp
from typing import Iterator, Optional


def is_repo_url(source: str) -> bool:
    if source.startswith(("https://", "http://", "ssh://", "git://", "file://")):
        return True
    # Git also accepts scp-style SSH addresses such as git@host:owner/repo.git.
    return re.fullmatch(r"[\w.-]+@(?:[\w.-]+|\[[\w:.%]+\]):(?!:).+", source) is not None


def _remove_readonly(remove, path, error_info):
    error = error_info[1]
    if not isinstance(error, PermissionError) or remove not in (os.unlink, os.rmdir):
        raise error
    attributes = os.lstat(path).st_file_attributes
    if (
        attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        or not (attributes & stat.FILE_ATTRIBUTE_READONLY)
    ):
        raise error
    os.chmod(path, stat.S_IWRITE)
    remove(path)


@contextmanager
def cloned_repository(url: str, destination: Optional[Path]) -> Iterator[Path]:
    with ExitStack() as cleanup:
        if destination is None:
            if os.name == "nt" and sys.version_info < (3, 8):
                # Python 3.7's TemporaryDirectory cannot remove Git's read-only objects.
                destination = Path(mkdtemp(prefix="glc-"))
                cleanup.callback(shutil.rmtree, destination, onerror=_remove_readonly)
            else:
                destination = Path(cleanup.enter_context(TemporaryDirectory(prefix="glc-")))
        subprocess.run(
            ["git", "clone", "--depth", "1", "--", url, str(destination)],
            capture_output=True, check=True,
        )
        yield destination
