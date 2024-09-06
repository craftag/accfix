from pathlib import Path
from loguru import logger as log
import streamlit as st
import tempfile
import subprocess
import shutil
import re

ace_path = Path(shutil.which("ace"))
ansi_escape = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")


def main():
    st.title("EPUB Accessibility Fixer")
    uploaded_file = st.file_uploader("Upload an EPUB file", type=["epub"])

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_file_path = tmp_file.name

        st.text("Checking EPUB for accessibility violations...")

        # Placeholder for log messages
        log_placeholder = st.empty()
        log_lines = []

        # Define the maximum number of lines to display
        max_log_lines = 6

        for log_line in check_epub(tmp_file_path):
            # Add new log line to the list
            log_lines.append(log_line)

            # Keep only the last 'max_log_lines' lines
            if len(log_lines) > max_log_lines:
                log_lines = log_lines[-max_log_lines:]

            # Join the log lines into a single string
            log_messages = "\n".join(log_lines)

            # Update the log placeholder
            log_placeholder.text(log_messages)

        st.text("Accessibility check completed.")
        # Placeholder for fixing process
        st.text("Fixing issues... (implementation required)")
        fixed_file_path = tmp_file_path.replace(".epub", "_fixed.epub")

        # Example of saving fixed file (this should be replaced with actual fixing logic)
        with open(fixed_file_path, "wb") as fixed_file:
            fixed_file.write(uploaded_file.getbuffer())

        st.text("Download the fixed EPUB file:")
        with open(fixed_file_path, "rb") as fixed_file:
            st.download_button(label="Download Fixed EPUB", data=fixed_file, file_name="fixed.epub")


# def main():
#     st.title("EPUB Accessibility Fixer")
#     uploaded_file = st.file_uploader("Upload an EPUB file", type=["epub"])
#
#     if uploaded_file is not None:
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp_file:
#             tmp_file.write(uploaded_file.getbuffer())
#             tmp_file_path = tmp_file.name
#
#         st.text("Checking EPUB for accessibility violations...")
#
#         # Placeholder for log messages
#         log_placeholder = st.empty()
#
#         for log_line in check_epub(tmp_file_path):
#             log_placeholder.text(log_line, append=True)
#
#         st.text("Accessibility check completed.")
#         # Placeholder for fixing process
#         st.text("Fixing issues... (implementation required)")
#         fixed_file_path = tmp_file_path.replace(".epub", "_fixed.epub")
#
#         # Example of saving fixed file (this should be replaced with actual fixing logic)
#         with open(fixed_file_path, "wb") as fixed_file:
#             fixed_file.write(uploaded_file.getbuffer())
#
#         st.text("Download the fixed EPUB file:")
#         with open(fixed_file_path, "rb") as fixed_file:
#             st.download_button(label="Download Fixed EPUB", data=fixed_file, file_name="fixed.epub")


if __name__ == "__main__":
    main()
