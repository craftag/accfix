from loguru import logger as log
from lxml.etree import ElementTree
from lxml import etree
from accfix.epub import Epub
from accfix.lang import detect_epub_lang


def ace_fix_mec(epub: Epub):
    """Static fixing of Accessibility for MagicEpub Fixed Layout EPUBs"""
    lang = detect_epub_lang(epub)

    # Fix OPF
    opf_tree = epub.opf_tree()
    set_lang(opf_tree, lang)
    add_acc_meta_fxl(opf_tree)
    etree.indent(opf_tree, space="  ")  # Ensure proper indentation
    data = etree.tostring(opf_tree, xml_declaration=True, encoding="utf-8", pretty_print=True)
    epub.write(epub.opf_path(), data)

    # Fix NAV
    nav_tree = epub.nav_tree()
    fix_nav(nav_tree)
    set_lang(nav_tree, lang)
    data = etree.tostring(nav_tree, xml_declaration=True, encoding="utf-8", pretty_print=True)
    epub.write(epub.nav_path(), data)

    # Fix CONTENT
    for page_path in epub.pages():
        data = epub.read(page_path)
        html_tree = ElementTree(etree.fromstring(data))
        set_lang(html_tree, lang)
        fix_trn_links(html_tree)
        data = etree.tostring(html_tree, xml_declaration=True, encoding="utf-8", pretty_print=True)
        epub.write(page_path, data)
    return epub


def set_lang(tree, lang):
    # type: (ElementTree, str) -> ElementTree
    """Set language for page"""
    root = tree.getroot()
    root.set("{http://www.w3.org/XML/1998/namespace}lang", lang)
    return tree


def add_acc_meta_fxl(opf_tree):
    # type: (ElementTree) -> ElementTree
    """Update or add default Fixed Layout metadata required by ACE"""
    root = opf_tree.getroot()
    metadata_element = root.find(".//{http://www.idpf.org/2007/opf}metadata")

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
        existing_metas = metadata_element.findall(f".//meta[@property='{property_value}']")
        if not any(existing_meta.text == text_value for existing_meta in existing_metas):
            new_meta = etree.Element("meta", property=property_value)
            new_meta.text = text_value
            metadata_element.append(new_meta)
            log.debug(f"Add {property_value} -> {text_value}")
        else:
            log.debug(f"Skip {property_value} -> {text_value}")

    return opf_tree


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


if __name__ == "__main__":
    fp = r"../scratch/test1.epub"
    epb = Epub(fp, clone=True)
    ace_fix_mec(epub=epb)
