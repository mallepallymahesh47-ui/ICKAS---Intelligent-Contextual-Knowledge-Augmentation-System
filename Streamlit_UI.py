import streamlit as st
import requests

# Backend URLs
BASE_URL = "http://localhost:8000"

# Page config
st.set_page_config(page_title="ICKAS Chat", layout="centered")

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

if "file_uploaded" not in st.session_state:
    st.session_state.file_uploaded = False



st.sidebar.title("Controls")

# Upload file
uploaded_file = st.sidebar.file_uploader(
    "Upload Document",
    type=["pdf", "txt", "csv", "xlsx", "docx"]
)

if uploaded_file:
    with st.sidebar.spinner("Uploading & processing..."):
        files = {"file": uploaded_file.getvalue()}
        response = requests.post(f"{BASE_URL}/Upload", files={"file": uploaded_file})
        
        if response.status_code == 200:
            st.sidebar.success("File uploaded successfully")
            st.session_state.file_uploaded = True
        else:
            st.sidebar.error("Upload failed")

# New Chat Button
if st.sidebar.button("New Chat"):
    st.session_state.messages = [
        {"role": "assistant", "content": "How can I help you?"}
    ]

# Clear History Button
if st.sidebar.button("Clear History"):
    st.session_state.messages = []


st.title("Intelligent Contextual Knowledge Augmentation System")

# Display messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# User input
user_input = st.chat_input("Type your message...")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # Decide mode
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                if st.session_state.file_uploaded:
                    # RAG mode (File-based)
                    response = requests.post(
                        f"{BASE_URL}/Query",
                        json={"question": user_input}
                    )
                    if response.status_code == 200:
                        answer = response.json()["response"]
                    else:
                        answer = "Error from RAG API"

                else:
                    # Normal LLM Chat 
                    response = requests.post(
                        f"{BASE_URL}/chat",   
                        json={"question": user_input}
                    )
                    if response.status_code == 200:
                        answer = response.json()["response"]
                    else:
                        answer = "Error from Chat API"

            except Exception as e:
                answer = f"Error: {str(e)}"

            st.markdown(answer)

    # Save assistant response
    st.session_state.messages.append({"role": "assistant", "content": answer})