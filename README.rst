Git Line Counter (GLC)
======================

A small Python tool that reports the number of tracked files and the total
number of lines in a local Git repository. It counts lines from the working
tree, including local edits and blank lines. It reports any tracked files it
cannot read.

Requirements
------------

Python 3.7 or later and Git. Keep ``count_lines.py`` and ``line_stats.py`` in
the same directory.

Usage
-----

Run ``glc.py`` with Python. It scans the current directory by default.
Pass a local repository path to scan a different directory.

Build
-----

Use `PyInstaller <https://pyinstaller.org/en/stable/>`_ to bundle GLC into a
single executable. From the directory containing both Python files:

1. Install PyInstaller with ``python -m pip install pyinstaller``.
2. Build with ``python -m PyInstaller --onefile --name glc glc.py``.

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
