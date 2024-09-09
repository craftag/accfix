from typing import Generator

from loguru import logger as log
from lxml.etree import ElementTree
from lxml import etree
from accfix.epub import Epub
from accfix.lang import detect_epub_lang


def ace_fix_mec(epub: Epub):
    """Static fixing of Accessibility for MagicEpub Fixed Layout EPUBs"""
    lang = detect_epub_lang(epub)
    yield f"Detected language: {lang}"

    # Fix OPF
    yield "Fixing OPF..."
    opf_tree = epub.opf_tree()
    set_lang(opf_tree, lang)
    yield "Adding accessibility metadata..."
    for message in add_acc_meta_fxl(opf_tree):
        yield message
    etree.indent(opf_tree, space="  ")  # Ensure proper indentation
    data = etree.tostring(opf_tree, xml_declaration=True, encoding="utf-8", pretty_print=True)
    epub.write(epub.opf_path(), data)
    yield "OPF fixed and updated"

    # Fix NAV
    yield "Fixing NAV..."
    nav_tree = epub.nav_tree()
    fix_nav(nav_tree)
    set_lang(nav_tree, lang)
    data = etree.tostring(nav_tree, xml_declaration=True, encoding="utf-8", pretty_print=True)
    epub.write(epub.nav_path(), data)
    yield "NAV fixed and updated"

    # Fix CONTENT
    yield "Fixing content pages..."
    for i, page_path in enumerate(epub.pages(), 1):
        yield f"Processing page {i}..."
        data = epub.read(page_path)
        html_tree = ElementTree(etree.fromstring(data))
        set_lang(html_tree, lang)
        fix_trn_links(html_tree)
        fix_hotspot_links_kf8(html_tree)
        data = etree.tostring(html_tree, xml_declaration=True, encoding="utf-8", pretty_print=True)
        epub.write(page_path, data)
    yield "All content pages fixed and updated"

    yield "Accessibility fixes completed successfully!"
    return epub


def set_lang(tree, lang):
    # type: (ElementTree, str) -> ElementTree
    """Set language for page"""
    root = tree.getroot()
    root.set("{http://www.w3.org/XML/1998/namespace}lang", lang)
    return tree


def add_acc_meta_fxl(opf_tree):
    # type: (ElementTree) -> Generator[str, None, None]
    """Update or add default Fixed Layout metadata required by ACE"""
    root = opf_tree.getroot()
    namespaces = {"opf": "http://www.idpf.org/2007/opf"}
    metadata_element = root.find(".//opf:metadata", namespaces=namespaces)

    meta_elements = [
        ("schema:accessMode", "textual"),
        ("schema:accessMode", "visual"),
        ("schema:accessibilityFeature", "structuralNavigation"),
        ("schema:accessibilityHazard", "noFlashingHazard"),
        ("schema:accessibilityHazard", "noSoundHazard"),
        ("schema:accessModeSufficient", "textual,visual"),
        (
            "schema:accessibilitySummary",
            "Fixed Layout with html text placed over background images.",
        ),
    ]

    for property_value, text_value in meta_elements:
        existing_meta = metadata_element.xpath(
            f".//opf:meta[@property='{property_value}' and text()='{text_value}']",
            namespaces=namespaces,
        )

        if not existing_meta:
            new_meta = etree.Element(f"{{{namespaces['opf']}}}meta", property=property_value)
            new_meta.text = text_value
            metadata_element.append(new_meta)
            yield f"Add {property_value} -> {text_value}"
        else:
            yield f"Skip {property_value} -> {text_value}"


def fix_nav(nav_tree):
    # type: (ElementTree) -> ElementTree
    """Fix Navigation Document"""
    root = nav_tree.getroot()
    namespaces = {
        "xhtml": "http://www.w3.org/1999/xhtml",
        "epub": "http://www.idpf.org/2007/ops",
    }
    for nav_element in root.xpath('//xhtml:nav[@epub:type="toc"]', namespaces=namespaces):
        nav_element.set("role", "doc-toc")
        nav_element.set("aria-label", "Table of Contents")

    for nav_element in root.xpath('//xhtml:nav[@epub:type="landmarks"]', namespaces=namespaces):
        nav_element.set("role", "navigation")
        nav_element.set("aria-label", "Landmarks")
    for a_element in root.xpath('//xhtml:a[@epub:type="bodymatter"]', namespaces=namespaces):
        a_element.set("role", "link")
        a_element.set("aria-label", "Start reading")
    return nav_tree


def fix_trn_links(html_tree):
    # type: (ElementTree) -> ElementTree
    """Add required title attribute to MagicEpub trn_link elements"""
    root = html_tree.getroot()
    namespaces = {
        "xhtml": "http://www.w3.org/1999/xhtml",
        "epub": "http://www.idpf.org/2007/ops",
    }
    trn_links = root.xpath('//xhtml:a[@class="trn_link"]', namespaces=namespaces)
    for el in trn_links:
        el.set("title", "Link area")
    return html_tree


def fix_hotspot_links_kf8(html_tree):
    # type: (ElementTree) -> ElementTree
    """Add required title attribute to MagicEpub hotspot link elements"""
    root = html_tree.getroot()
    namespaces = {
        "xhtml": "http://www.w3.org/1999/xhtml",
        "epub": "http://www.idpf.org/2007/ops",
    }
    hot_spot_divs = root.xpath('//xhtml:div[@class="hotspot"]', namespaces=namespaces)
    for div in hot_spot_divs:
        link = div.find(".//xhtml:a", namespaces=namespaces)
        if link is not None:
            link.set("title", "Link area")
    return html_tree


if __name__ == "__main__":
    fp = r"../scratch/test1.epub"
    epb = Epub(fp, clone=True)
    for message in add_acc_meta_fxl(epb.opf_tree()):
        print(message)
