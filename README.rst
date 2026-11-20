Git Line Counter (GLC)
======================

A small Python tool that reports the number of tracked files and the total
number of lines in a local Git repository. It counts lines from the working
tree, including local edits and blank lines. It reports any tracked files it
cannot read.

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

You can also run ``python src/glc.py`` directly from the checkout.

Tests
-----

The integration test runs the installed command in a temporary Git repository.

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

``-h``, ``--help``
    Show command-line help and exit.
