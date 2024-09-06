from lxml.etree import ElementTree
from lxml import etree
from accfix.epub import Epub
from accfix.lang import detect_epub_lang


def ace_fix_mec(epub: Epub):
    """Static fixing of Accessibility for MagicEpub Fixed Layout EPUBs"""
    # Fix OPF
    opf_tree = epub.opf_tree()
    lang = detect_epub_lang(epub)
    opf_add_lang(opf_tree, lang)
    add_acc_meta_fxl(opf_tree)
    data = etree.tostring(opf_tree, xml_declaration=True, encoding="utf-8", pretty_print=True)
    epub.write(epub.opf_path(), data)

    # Fix NAV
    nav_tree = epub.nav_tree()
    fix_nav(nav_tree)
    data = etree.tostring(nav_tree, xml_declaration=True, encoding="utf-8", pretty_print=True)
    epub.write(epub.nav_path(), data)

    # Fix CONTENT
    for page_path in epub.pages():
        data = epub.read(page_path)
        html_tree = etree.fromstring(data)
        html_set_lang(html_tree, lang)
        fix_trn_links(html_tree)
        data = etree.tostring(html_tree, xml_declaration=True, encoding="utf-8", pretty_print=True)
        epub.write(page_path, data)
    return epub


def opf_add_lang(opf_tree, lang):
    # type: (ElementTree, str) -> ElementTree
    """Add language to OPF tree"""
    package_element = opf_tree.getroot()
    package_element.set("{http://www.w3.org/XML/1998/namespace}lang", lang)
    return opf_tree


def add_acc_meta_fxl(opf_tree):
    # type: (ElementTree) -> ElementTree
    """Add default Fixed Layout metadata required by ACE"""
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
    package_element = opf_tree.getroot()
    metadata_element = package_element.find(".//{http://www.idpf.org/2007/opf}metadata")
    metadata_element.append(new_meta1)
    metadata_element.append(new_meta2)
    metadata_element.append(new_meta3)
    metadata_element.append(new_meta4)
    metadata_element.append(new_meta5)
    metadata_element.append(new_meta6)
    metadata_element.append(new_meta7)
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


def html_set_lang(html_tree, lang):
    # type: (ElementTree, str) -> ElementTree
    """Set language for page"""
    root = html_tree.getroot()
    root.set("lang", lang)
    root.set("{http://www.w3.org/XML/1998/namespace}lang", lang)
    return html_tree


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
