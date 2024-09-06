from loguru import logger as log
from typing import Optional
from lingua import LanguageDetectorBuilder
from accfix.epub import Epub
from lxml import etree

detector = LanguageDetectorBuilder.from_all_languages().with_low_accuracy_mode().build()


def detect_lang(text: str) -> Optional[str]:
    """Detect language of text and return ISO 639-1 code"""
    detected_language = detector.detect_language_of(text)
    if not detected_language:
        return
    return detected_language.iso_code_639_1.name.lower()


def xml_text(xml: etree._Element) -> str:
    """Extract plaintext content from XML tree"""
    content = [t.strip() for t in xml.xpath("//text()") if t.strip()]
    return "\n".join(content)


def detect_epub_lang(epub: Epub, min_length=100) -> Optional[str]:
    """Detect language of epub and return ISO 639-1 code"""
    pages = epub.pages()
    start_index = len(pages) // 2  # Start from the middle of the book

    for page in pages[start_index:] + pages[:start_index]:
        try:
            content = epub.read(page)
            tree = etree.fromstring(content)
            text = xml_text(tree)

            if len(text) > min_length:
                detected_lang = detect_lang(text)
                if detected_lang:
                    return detected_lang
            log.debug(f"Not enough text in {page}")
        except Exception as e:
            print(f"Error processing page {page}: {str(e)}")

    return None


if __name__ == "__main__":
    from accfix.epub import Epub

    # Test the detect_epub_lang function
    epub_path = "../scratch/test1_fix.epub"  # Update this path to a valid EPUB file
    epub = Epub(epub_path)
    detected_language = detect_epub_lang(epub)
    print(f"Detected language for {epub_path}: {detected_language}")
