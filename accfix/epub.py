"""Module for handling EPUB files"""
from pathlib import Path
import shutil
import tempfile

import fsspec


class Epub:

    def __init__(self, path, clone=True):
        # type: (str, Path) -> Epub
        """Opens a EPUB file for reading and writing.

        Wraps the epub file in a fsspec zip filesystem for easy access.

        :param path: Path to the EPUB file.
        :param clone: Create a temporary copy of the EPUB file and open that one.
        """
        self._path = Path(path)
        self._clone = None
        if clone:
            temp_dir = tempfile.mkdtemp()
            self._clone = Path(temp_dir) / self._path.name
            shutil.copy2(self._path, self._clone)

