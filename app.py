import streamlit as st
import tempfile
import os
from loguru import logger as log
from accfix.epub import Epub
from accfix.lang import detect_epub_lang
from accfix.ace_fix import ace_fix_mec
import shutil


def save_uploaded_file(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        return tmp_file.name


def apply_accessibility_fixes(epub):
    with st.spinner("Applying accessibility fixes..."):
        fixed_epub = ace_fix_mec(epub)
    st.success("Accessibility fixes applied successfully!")
    return fixed_epub


def offer_download(fixed_epub, original_filename):
    # Save the fixed EPUB to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp_file:
        fixed_epub._zf.close()  # Ensure the ZipFile is closed
        shutil.copy2(fixed_epub.path, tmp_file.name)

        # Log file size for debugging
        log.debug(f"Fixed EPUB size: {os.path.getsize(tmp_file.name)} bytes")

        # Read the temporary file
        with open(tmp_file.name, "rb") as file:
            fixed_epub_bytes = file.read()

        # Offer download
        st.download_button(
            label="Download Fixed EPUB",
            data=fixed_epub_bytes,
            file_name=f"fixed_{original_filename}",
            mime="application/epub+zip",
        )

    # Clean up the temporary file
    os.unlink(tmp_file.name)


def cleanup(tmp_file_path, epub):
    try:
        os.unlink(tmp_file_path)
        log.info(f"Temporary file {tmp_file_path} deleted successfully")
    except Exception as e:
        log.warning(f"Failed to delete temporary file {tmp_file_path}: {str(e)}")

    if hasattr(epub, "_clone") and epub._clone:
        try:
            os.unlink(epub._clone)
            log.info(f"Cloned file {epub._clone} deleted successfully")
            os.rmdir(os.path.dirname(epub._clone))
            log.info(f"Temporary directory {os.path.dirname(epub._clone)} deleted successfully")
        except Exception as e:
            log.warning(f"Failed to delete cloned file or directory: {str(e)}")


def main():
    st.title("EPUB Accessibility Fixer")
    uploaded_file = st.file_uploader("Upload an EPUB file", type=["epub"])

    if uploaded_file is not None:
        tmp_file_path = save_uploaded_file(uploaded_file)
        epub = None

        try:
            epub = Epub(tmp_file_path, clone=True)
            detected_language = detect_epub_lang(epub)
            if detected_language:
                st.success(f"Detected language: {detected_language}")
            else:
                st.warning("Unable to detect the language of the EPUB.")

            if st.button("Fix Accessibility"):
                fixed_epub = apply_accessibility_fixes(epub)
                offer_download(fixed_epub, uploaded_file.name)

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            log.exception("Error during EPUB processing")

        finally:
            if epub:
                cleanup(tmp_file_path, epub)


if __name__ == "__main__":
    main()
