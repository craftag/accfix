import streamlit as st
import tempfile
import os
from loguru import logger as log
from accfix.epub import Epub
from accfix.lang import detect_epub_lang
from accfix.ace_fix import ace_fix_mec
import shutil
import telegram
from telegram.error import TelegramError
import asyncio
import dotenv

dotenv.load_dotenv()


def save_uploaded_file(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".epub") as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        return tmp_file.name


def apply_accessibility_fixes(epub):
    progress_bar = st.progress(0)
    status_text = st.empty()

    # Create a container with custom CSS for scrolling
    message_container = st.container()
    message_container.markdown(
        """
        <style>
        .scrollable-container {
            height: 200px;
            overflow-y: auto;
            border: 1px solid var(--text-color);
            padding: 10px;
            background-color: var(--background-color);
            color: var(--text-color);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    message_area = message_container.empty()

    messages = []

    for i, message in enumerate(ace_fix_mec(epub), 1):
        messages.insert(0, message)  # Prepend new messages
        status_text.text(message)
        message_area.markdown(
            f'<div class="scrollable-container">{"<br>".join(messages)}</div>',
            unsafe_allow_html=True,
        )
        progress = min(i / 10, 1.0)  # Assuming about 10 main steps
        progress_bar.progress(progress)

    progress_bar.progress(1.0)
    status_text.text("Accessibility fixes completed successfully!")

    return epub


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

        # Add vertical space before the download button
        st.markdown("<br>", unsafe_allow_html=True)

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


async def send_telegram_notification(message, file_path=None):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    bot = telegram.Bot(token=bot_token)

    try:
        if file_path:
            with open(file_path, "rb") as file:
                await bot.send_document(chat_id=chat_id, document=file, caption=message)
        else:
            await bot.send_message(chat_id=chat_id, text=message)
    except TelegramError as e:
        log.error(f"Failed to send Telegram notification: {e}")


def send_telegram_notification_sync(message, file_path=None):
    asyncio.run(send_telegram_notification(message, file_path))


def main():
    st.title("EPUB Accessibility Fixer (Beta)")
    st.subheader("For Fixed Layout EPUBs from [MagicEPUB](https://magicepub.com)")
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
                send_telegram_notification_sync(
                    f"File processed successfully: {uploaded_file.name}"
                )

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            log.exception("Error during EPUB processing")
            send_telegram_notification_sync(
                f"Error processing file: {uploaded_file.name}\n\nError: {str(e)}", tmp_file_path
            )

        finally:
            if epub:
                cleanup(tmp_file_path, epub)


if __name__ == "__main__":
    main()
