Git Line Counter
================

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

Run ``count_lines.py`` with Python. It scans the current directory by default.
Pass a local repository path to scan a different directory.

Flags
-----

``-t``, ``--types``
    Show the share of tracked files and counted lines for each file extension.
    Extensions are grouped case-insensitively.

``-h``, ``--help``
    Show command-line help and exit.
