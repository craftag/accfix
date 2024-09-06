"""Module for handling EPUB files"""

from functools import cache
from typing import List, Optional
from loguru import logger as log
from pathlib import Path
import shutil
import tempfile
from accfix.zfile import ZipFileR
from lxml import etree
from lxml.etree import ElementTree


class Epub:
    def __init__(self, path, clone=True):
        # type: (str|Path, bool) -> None
        """EPUB file object for reading and writing members.

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

    @cache
    def opf_path(self) -> Path:
        """Determine OPF-File path within epub archive"""
        with self._zf.open("META-INF/container.xml", "r") as f:
            xml_data = f.read()
        tree = etree.fromstring(xml_data)
        namespace = {"ns": "urn:oasis:names:tc:opendocument:xmlns:container"}
        rootfile_element = tree.find(".//ns:rootfiles/ns:rootfile", namespaces=namespace)
        result = rootfile_element.attrib["full-path"]
        return Path(result)

    def opf_tree(self) -> ElementTree:
        """Return parsed ElementTree of OPF-File"""
        return etree.fromstring(self.read(self.opf_path()))

    def nav_path(self) -> Optional[Path]:
        """Determine nav-File path within epub archive"""
        opf_content = self.read(self.opf_path())
        tree = etree.fromstring(opf_content)

        # Define namespaces
        namespaces = {
            "opf": "http://www.idpf.org/2007/opf",
        }

        # Find the item with properties="nav"
        nav_item = tree.xpath("//opf:manifest/opf:item[@properties='nav']", namespaces=namespaces)

        if not nav_item:
            log.warning("No nav item found in the EPUB manifest")
            return None

        if len(nav_item) > 1:
            log.warning("Multiple nav items found in the EPUB manifest. Using the first one.")

        # Get the href of the nav item
        nav_href = nav_item[0].get("href")

        # Combine the OPF directory with the href to get the full relative path
        opf_dir = self.opf_path().parent
        full_path = opf_dir / nav_href

        # Normalize the path to remove any '..' components
        return Path(full_path.as_posix())

    def nav_tree(self) -> ElementTree:
        """Return parsed ElementTree of OPF-File"""
        return etree.parse(self.read(self.nav_path()))

    def read(self, path):
        # type: (str|Path) -> bytes
        """Read the content of a file from the EPUB.

        :param path: The relative path of the file within the EPUB.
        :return: The content of the file.
        """
        path = Path(path)
        log.debug(f"Reading: {self.name}/{path.as_posix()}")
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

    def pages(self):
        # type: () -> List[Path]
        """Return a list of paths to epub pages.

        Reads all <spine> elements and resolves them to the actual file paths.
        """
        opf_content = self.read(self.opf_path())
        tree = etree.fromstring(opf_content)

        # Define namespaces
        namespaces = {
            "opf": "http://www.idpf.org/2007/opf",
            "dc": "http://purl.org/dc/elements/1.1/",
        }

        # Get the spine elements
        spine_elements = tree.xpath("//opf:spine/opf:itemref", namespaces=namespaces)

        # Get the manifest elements
        manifest_elements = tree.xpath("//opf:manifest/opf:item", namespaces=namespaces)

        # Create a dictionary to map ids to hrefs
        id_to_href = {item.get("id"): item.get("href") for item in manifest_elements}

        # Get the paths for each spine item
        page_paths = []
        opf_dir = self.opf_path().parent
        for itemref in spine_elements:
            idref = itemref.get("idref")
            if idref in id_to_href:
                href = id_to_href[idref]
                # Combine the OPF directory with the href to get the full relative path
                full_path = opf_dir / href
                # Normalize the path to remove any '..' components
                full_path = Path(full_path.as_posix())
                page_paths.append(full_path)

        return page_paths


if __name__ == "__main__":
    epb = Epub("../scratch/test1_fix.epub")
    print(f"OPF path: {epb.opf_path()}")
    print(f"Nav path: {epb.nav_path()}")

    print("\nTesting pages() method:")
    for page in epb.pages():
        print(f"Page: {page}")
