"""Module for handling EPUB files"""

from loguru import logger as log
from pathlib import Path
import shutil
import tempfile
from accfix.zfile import ZipFileR


class Epub:
    def __init__(self, path, clone=True):
        # type: (str|Path, bool) -> Epub
        """Opens a EPUB file for reading and writing.

        Wraps the epub file in a fsspec zip filesystem for easy access.

        :param path: Path to the EPUB file.
        :param clone: Create a temporary copy of the EPUB file and open that one.
        """
        self._path = Path(path)
        self.name = self._path.name
        log.debug("Opening EPUB file: {name}".format(name=self._path.name))
        self._clone = None
        if clone:
            temp_dir = tempfile.mkdtemp()
            self._clone = Path(temp_dir) / self._path.name
            shutil.copy2(self._path, self._clone)
            log.debug(f"Cloning EPUB file to: {self._clone.parent}")
        self._zf = ZipFileR(self._clone if self._clone else self._path, mode="a")

    def __repr__(self):
        return f'Epub("{self._path.name}")'

    def read(self, path):
        # type: (str|Path) -> bytes
        """Read the content of a file from the EPUB.

        :param path: The relative path of the file within the EPUB.
        :return: The content of the file.
        """
        path = Path(path)
        log.debug(f"Reading: {self.name}/{path}")
        with self._zf.open(path.as_posix()) as file:
            return file.read()

    def write(self, path, data):
        # type: (str|Path, bytes) -> None
        """Write data to a file in the EPUB.

        :param path: The relative path of the file within the EPUB.
        :param data: The data to write to the file.
        """
        path = Path(path)
        log.debug(f"Writing: {self.name}/{path}")
        try:
            self._zf.remove(path.as_posix())
        except KeyError:
            pass
        with self._zf.open(path.as_posix(), "w") as file:
            file.write(data)


if __name__ == "__main__":
    epb = Epub("../scratch/test1_fix.epub")
    mtc = epb.read("mimetype")
    print(mtc)
    epb.write("mimetype", mtc)
    c = epb.read("OEBPS/cover.xhtml")
    print(type(c))
    c = epb.read("OEBPS/images/cover.jpg")
    print(type(c))
    c = epb.read(Path("OEBPS/images/cover.jpg"))
    print(type(c))
