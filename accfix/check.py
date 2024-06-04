from pathlib import Path
import zipfile
from typing import Optional
from lingua import LanguageDetectorBuilder
from lxml import etree
from subprocess import run
import json


detector = LanguageDetectorBuilder.from_all_languages().with_low_accuracy_mode().build()


def is_epub(fp: str | Path) -> bool:
    """Check if a file is an epub."""
    fp = Path(fp)
    with zipfile.ZipFile(fp, "r") as zf:
        infolist = zf.infolist()
        if not infolist or infolist[0].filename != "mimetype":
            return False

        info = infolist[0]
        if info.file_size == 20 and zf.read(info) == b"application/epub+zip":
            return True
    return False


def opf_path(fp: str | Path) -> Path:
    """Determine OPF-File path within epub archive"""
    fp = Path(fp)
    with zipfile.ZipFile(fp, "r") as z:
        with z.open("META-INF/container.xml", "r") as f:
            xml_data = f.read()
        tree = etree.fromstring(xml_data)
        namespace = {"ns": "urn:oasis:names:tc:opendocument:xmlns:container"}
        rootfile_element = tree.find(".//ns:rootfiles/ns:rootfile", namespaces=namespace)
        result = rootfile_element.attrib["full-path"]
    return Path(result)


def read_opf(fp: str | Path):
    """Read OPF-File from epub archive"""
    fp = Path(fp)
    opf_fp = opf_path(fp)  # use the existing function to determine the opf file's location
    with zipfile.ZipFile(fp, "r") as z:
        with z.open(opf_fp.as_posix(), "r") as f:
            xml_data = f.read()
    tree = etree.fromstring(xml_data)  # parse the opf file using lxml for editing
    return tree


def xml_text(xml: etree._Element) -> str | None:
    """Extract plaintext content from XML tree"""
    content = [t.strip() for t in xml.xpath("//text()") if t.strip()]
    return "\n".join(content)


def detect_lang(text: str) -> Optional[str]:
    """Detect language of text and return ISO 639-1 code"""
    detected_language = detector.detect_language_of(text)
    if not detected_language:
        return
    return detected_language.iso_code_639_1.name.lower()


def check(fp: str | Path) -> dict:
    # Prepare output path
    fp = Path(fp)
    report_dir = fp.parent / f"{fp.stem}_report"
    report_dir.mkdir(exist_ok=True)
    report_file = report_dir / "report.json"

    # Run ACE Check
    cmd = ["ace", "-f", "-o", report_dir, fp]
    run(cmd, shell=True)

    # Return Result data
    return json.load(report_file.open(encoding="utf-8"))


if __name__ == "__main__":
    file = Path("../scratch/test1.epub")
    check(file)
    # print(is_epub(file))
    # opf_fp = opf_path(Path("../scratch/test1_fix.epub"))
    # print(opf_fp)
    # opf_tree = read_opf(file)
    # print(opf_tree)
    # print(detect_lang("Guten Tag. Wie geht es ihnen"))
    # print(xml_text(opf_tree))
    # print(check(Path("../scratch/test1_fix.epub")))
