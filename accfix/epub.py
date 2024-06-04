"""Module for handling EPUB files"""

from pathlib import Path
import shutil
import tempfile

import fsspec


class Epub:
    def __init__(self, path, clone=True):
        # type: (str|Path, bool) -> Epub
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
        self._fs = fsspec.filesystem("zip", fo=str(self._clone if self._clone else self._path))

    def __repr__(self):
        return f'Epub("{self._path.name}")'

    def read(self, epub_relative_path):
        """Read the content of a file from the EPUB.

        :param epub_relative_path: The relative path of the file within the EPUB.
        :return: The content of the file.
        """
        with self._fs.open(epub_relative_path, "r") as file:
            return file.read()


if __name__ == '__main__':
    epb = Epub("../scratch/test1.epub")
    print(epb)
