from lxml.etree import ElementTree
from lxml import etree


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


def html_set_lang(tree, lang):
    # type: (ElementTree, str) -> ElementTree
    """Set language for page"""
    root = tree.getroot()
    root.set("lang", lang)
    root.set("{http://www.w3.org/XML/1998/namespace}lang", lang)
    return tree


def fix_trn_links(tree):
    # type: (ElementTree) -> ElementTree
    """Add required title attribute to MagicEpub trn_link elements"""
    root = tree.getroot()
    namespaces = {
        "xhtml": "http://www.w3.org/1999/xhtml",
        "epub": "http://www.idpf.org/2007/ops",
    }
    trn_links = root.xpath('//xhtml:a[@class="trn_link"]', namespaces=namespaces)
    for el in trn_links:
        el.set("title", "Link area")
    return tree


def fix_nav(tree):
    # type: (ElementTree) -> ElementTree
    """Fix nav.html"""
