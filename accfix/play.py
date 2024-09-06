import streamlit as st
import time


# Sample generator function
def message_generator(total_messages):
    messages = [f"Message {i + 1}" for i in range(total_messages)]
    for i, message in enumerate(messages):
        yield message
        time.sleep(0.5)  # Simulate some delay
    yield {"result": "Completed"}


# Number of messages
total_messages = 10

# Initialize Streamlit components
progress_bar = st.progress(0)
messages_area = st.empty()

# Get the container in which to append messages
messages_html = """
    <div id="scrollable" style="height:200px; overflow-y:scroll; border:1px solid #ccc; padding:10px;"></div>
    """
scrollable_div = st.empty()
scrollable_div.markdown(messages_html, unsafe_allow_html=True)

# Generator function call and UI update
messages_html_content = ""
for i, item in enumerate(message_generator(total_messages)):
    if isinstance(item, dict):  # End of messages with result
        result = item["result"]
        messages_html_content += f"<p style='margin: 0;'>{result}</p>"
    else:
        messages_html_content += f"<p style='margin: 0;'>{item}</p>"

    scrollable_div.markdown(
        f"""
        <div id="scrollable" style="height:200px; overflow-y:scroll; border:1px solid #ccc; padding:10px;">{messages_html_content}</div>
        <script>
            var scrollable = document.getElementById('scrollable');
            scrollable.scrollTop = scrollable.scrollHeight;
        </script>
        """,
        unsafe_allow_html=True,
    )

    # Update progress bar with values between 0 and 1
    progress_bar.progress((i + 1) / total_messages)

st.write("Done!")
