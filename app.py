# -*- coding: utf-8 -*-
import streamlit as st
import tempfile
from accfix.epub import Epub
from accfix.lang import detect_epub_lang


def main():
    st.title("EPUB Accessibility Fixer")
    uploaded_file = st.file_uploader("Upload an EPUB file", type=["epub"])

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_file_path = tmp_file.name

        # Detect the language of the uploaded EPUB
        epub = Epub(tmp_file_path)
        detected_language = detect_epub_lang(epub)

        if detected_language:
            st.success(f"Detected language: {detected_language}")
        else:
            st.warning("Unable to detect the language of the EPUB.")


if __name__ == "__main__":
    main()
