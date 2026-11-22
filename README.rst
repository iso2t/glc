Git Line Counter (GLC)
======================

A small Python tool that counts tracked files and lines in a local Git working
tree or a repository cloned from a URL. It includes blank lines and local edits
and reports any tracked files it cannot read.

Requirements
------------

The wheel and the source launcher run on Python 3.7 or later with Git on
your ``PATH``. The development commands below use Poetry 2 with Python 3.10
or later.

Usage
-----

From the project root, install GLC and run it to scan the current directory.

::

    poetry install
    poetry run glc

To see the extension breakdown for another working tree, pass ``--types``
and its path.

::

    poetry run glc --types /path/to/repo

Pass a Git URL for a one-off count. GLC makes a shallow clone of the default
branch in a temporary directory and removes it after the scan.

::

    poetry run glc --types https://github.com/pallets/click.git

To keep the checkout, give ``--keep`` a new or empty directory. Later, pass
that path to count it again. Add ``--pull`` to fast-forward the current branch
from its configured upstream before counting.

::

    poetry run glc https://github.com/pallets/click.git --keep ./click
    poetry run glc ./click
    poetry run glc ./click --pull

If the pull fails, GLC reports the Git error and stops before counting. For
URL and ``--pull`` scans, symbolic links that resolve outside the scanned
folder are reported as skipped.

You can also run ``python src/glc.py`` directly from the checkout.

Tests
-----

The integration tests run the installed command against temporary Git
repositories. They use local ``file://`` URLs to exercise cloning and pulling.

::

    poetry run python -m unittest discover -s tests/integration

Build
-----

Run ``poetry build`` to create a wheel and source distribution in ``dist/``.
For a standalone executable, install the optional PyInstaller dependency
and build from the project root.

::

    poetry install --with bundle
    poetry run pyinstaller --onefile --name glc src/glc.py

The executable is ``dist/glc.exe`` on Windows or ``dist/glc`` on macOS and
Linux. Build on the operating system where you plan to run it. The executable
bundles Python and still needs Git on your ``PATH``.

Flags
-----

``-t``, ``--types``
    Show the share of tracked files and counted lines for each file extension.
    Extensions are grouped case-insensitively.

``--keep DIR``
    Keep a URL's shallow clone in ``DIR`` after counting.

``--pull``
    Run ``git pull --ff-only`` before counting a local working tree.

``-h``, ``--help``
    Show command-line help and exit.
