# -*- coding: utf-8 -*-
import streamlit as st
import tempfile


def main():
    st.title("EPUB Accessibility Fixer")
    uploaded_file = st.file_uploader("Upload an EPUB file", type=["epub"])

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_file_path = tmp_file.name
            st.text(f"File at {tmp_file_path}")


if __name__ == "__main__":
    main()
