import os
import shutil
import zipfile
from lxml import etree


def copy_epub(file_path: str) -> str:
    """Create a copy of the epub file with the postfix '_fix.epub'."""
    new_file_path = file_path.replace(".epub", "_fix.epub")
    shutil.copyfile(file_path, new_file_path)
    return new_file_path


def find_opf(zip_file: zipfile.ZipFile) -> str:
    """Find the path to the opf file within the epub archive."""
    with zip_file.open("META-INF/container.xml") as container_file:
        container_tree = etree.parse(container_file)
        rootfile_element = container_tree.find(
            ".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile"
        )
        opf_path = rootfile_element.get("full-path")
    return opf_path


def fix_opf(zip_file: zipfile.ZipFile, opf_path: str) -> bytes:
    """Fix opf file by addding xml:lang="en" and inserting new static meta elements."""
    with zip_file.open(opf_path) as opf_file:
        opf_tree = etree.parse(opf_file)
        package_element = opf_tree.getroot()

        # Add xml:lang="en" to the package element
        package_element.set("{http://www.w3.org/XML/1998/namespace}lang", "en")

        # Create new meta elements
        new_meta1 = etree.Element("meta", property="schema:accessMode")
        new_meta1.text = "textual"
        new_meta2 = etree.Element("meta", property="schema:accessMode")
        new_meta2.text = "visual"

        new_meta3 = etree.Element("meta", property="schema:accessibilityFeature")
        new_meta3.text = "structuralNavigation"

        new_meta4 = etree.Element("meta", property="schema:accessibilityHazard")
        new_meta4.text = "noFlashingHazard"

        new_meta5 = etree.Element("meta", property="schema:accessibilityHazard")
        new_meta5.text = "noSoundHazard"

        new_meta6 = etree.Element("meta", property="schema:accessModeSufficient")
        new_meta6.text = "textual,visual"

        new_meta7 = etree.Element("meta", property="schema:accessibilitySummary")
        new_meta7.text = "Fixed Layout with html text placed over background images."

        # Find the metadata element
        metadata_element = package_element.find(".//{http://www.idpf.org/2007/opf}metadata")

        # Append new meta elements to metadata element
        if metadata_element is not None:
            metadata_element.append(new_meta1)
            metadata_element.append(new_meta2)
            metadata_element.append(new_meta3)
            metadata_element.append(new_meta4)
            metadata_element.append(new_meta5)
            metadata_element.append(new_meta6)
            metadata_element.append(new_meta7)

        return etree.tostring(opf_tree, xml_declaration=True, encoding="utf-8", pretty_print=True)


def update_epub(new_file_path: str, opf_path: str, new_opf_content: bytes) -> None:
    """Update the opf file inside the copied epub with the modified content."""
    temp_zip_path = new_file_path + ".tmp"

    with zipfile.ZipFile(new_file_path, "r") as zip_read:
        with zipfile.ZipFile(temp_zip_path, "w") as zip_write:
            for item in zip_read.infolist():
                if item.filename == opf_path:
                    zip_write.writestr(opf_path, new_opf_content)
                else:
                    zip_write.writestr(item, zip_read.read(item.filename))

    os.replace(temp_zip_path, new_file_path)


def fix_attributes(new_file_path: str) -> None:
    temp_zip_path = new_file_path + ".tmp"

    with zipfile.ZipFile(new_file_path, "r") as zip_read:
        with zipfile.ZipFile(temp_zip_path, "w") as zip_write:
            for item in zip_read.infolist():
                if item.filename.endswith(".xhtml"):
                    with zip_read.open(item.filename) as xhtml_file:
                        xhtml_tree = etree.parse(xhtml_file)
                        html_element = xhtml_tree.getroot()
                        html_element.set("lang", "en")
                        html_element.set("{http://www.w3.org/XML/1998/namespace}lang", "en")

                        # Add title attribute to elements with class trn_link
                        # Handle namespaces in XHTML
                        namespaces = {
                            "xhtml": "http://www.w3.org/1999/xhtml",
                            "epub": "http://www.idpf.org/2007/ops",
                        }
                        a_elements = html_element.xpath(
                            '//xhtml:a[@class="trn_link"]', namespaces=namespaces
                        )
                        for el in a_elements:
                            el.set("title", "Link area")

                        if item.filename.endswith("nav.xhtml"):
                            for nav_element in html_element.xpath(
                                '//xhtml:nav[@epub:type="toc"]', namespaces=namespaces
                            ):
                                nav_element.set("role", "doc-toc")
                                nav_element.set("aria-label", "Table of Contents")

                            for nav_element in html_element.xpath(
                                '//xhtml:nav[@epub:type="landmarks"]', namespaces=namespaces
                            ):
                                nav_element.set("role", "navigation")
                                nav_element.set("aria-label", "Landmarks")
                            for a_element in html_element.xpath(
                                '//xhtml:a[@epub:type="bodymatter"]', namespaces=namespaces
                            ):
                                a_element.set("role", "link")
                                a_element.set("aria-label", "Start reading")

                        new_xhtml_content = etree.tostring(
                            xhtml_tree, xml_declaration=True, encoding="utf-8", pretty_print=True
                        )
                        zip_write.writestr(item.filename, new_xhtml_content)
                else:
                    zip_write.writestr(item, zip_read.read(item.filename))

    os.replace(temp_zip_path, new_file_path)


def fix_epub(file_path: str) -> None:
    """Main function to fix the epub file."""
    new_file_path = copy_epub(file_path)

    with zipfile.ZipFile(new_file_path, "r") as zip_file:
        opf_path = find_opf(zip_file)
        new_opf_content = fix_opf(zip_file, opf_path)

    update_epub(new_file_path, opf_path, new_opf_content)
    fix_attributes(new_file_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python fix_epub.py <path_to_epub_file>")
        sys.exit(1)

    epub_file_path = sys.argv[1]
    if not os.path.isfile(epub_file_path) or not epub_file_path.endswith(".epub"):
        print(f"Error: {epub_file_path} is not a valid epub file.")
        sys.exit(1)

    fix_epub(epub_file_path)
    print(f"Fixed EPUB file created: {epub_file_path.replace('.epub', '_fix.epub')}")
