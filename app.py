import streamlit as st
import os
import logging
from dotenv import load_dotenv
from back import get_access_token, send_to_llm_api, fetch_user_packs
import requests

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Initialize session state
if 'access_token' not in st.session_state:
    st.session_state['access_token'] = None
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'

# Initialize session state for conversation history
if 'conversation_history' not in st.session_state:
    st.session_state['conversation_history'] = []

# Define a function for the login page
def login_page():
    st.title("Login")
    email = st.text_input("Enter your email:")
    password = st.text_input("Enter your password:", type="password")

    if st.button("Login"):
        logging.debug("Login button clicked")
        logging.debug(f"Attempting login with email: {email}")
        access_token = get_access_token(email, password)
        if access_token:
            st.session_state['access_token'] = access_token
            st.session_state['page'] = 'chat'
            st.success("Logged in successfully!")
            logging.info("User logged in successfully")
            logging.debug(f"Access token received: {access_token}")
            st.rerun()
        else:
            st.error("Failed to authenticate. Please check your credentials.")
            logging.warning("Failed to authenticate user")

# Define a function for the chat interface
def chat_interface():
    st.title("Chatbot with Pack Data Access")

    # Fetch and display user packs
    logging.debug("Fetching user packs")
    packs = fetch_user_packs(st.session_state['access_token'])
    if packs:
        logging.info(f"Fetched {len(packs)} user packs")
        pack_info = [{"id": pack['id'], "name": pack['pack_name']} for pack in packs]
        logging.debug(f"User packs info: {pack_info}")
        pack_names = ["None"] + [pack['pack_name'] for pack in packs]
        selected_pack = st.selectbox("Select a pack", pack_names)
    else:
        st.error("No packs available or failed to fetch packs.")
        logging.error("Failed to fetch user packs or no packs available")
        selected_pack = "None"
    
    # File uploader
    uploaded_files = st.file_uploader("Upload files", type=["pdf", "docx", "txt", "csv"], accept_multiple_files=True)
    if uploaded_files:
        logging.debug(f"Uploaded files: {[file.name for file in uploaded_files]}")

    # Display conversation history
    st.subheader("Conversation History")
    for message in st.session_state['conversation_history']:
        if message['role'] == 'user':
            st.markdown(f"**User:** {message['content']}")
        elif message['role'] == 'assistant':
            st.markdown(f"**Assistant:** {message['content']}")

    # Chat input
    prompt = st.chat_input("Say something")
    if prompt:
        logging.debug(f"User prompt: {prompt}")
        st.session_state['conversation_history'].append({"role": "user", "content": prompt})
        st.markdown(f"**User:** {prompt}")

        # Prepare file contents
        file_contents = ""
        if uploaded_files:
            for uploaded_file in uploaded_files:
                logging.debug(f"Processing uploaded file: {uploaded_file.name}")
                if uploaded_file.type == "text/plain":
                    file_contents += uploaded_file.read().decode("utf-8") + "\n"
                elif uploaded_file.type == "text/csv":
                    import pandas as pd
                    df = pd.read_csv(uploaded_file)
                    file_contents += df.to_string(index=False) + "\n"

        # Combine user message and file contents
        context = prompt + "\n" + file_contents
        logging.debug(f"Context for API call: {context}")

        # Determine the selected pack ID, if any
        selected_pack_id = None
        if selected_pack != "None":
            selected_pack_id = next((pack['id'] for pack in packs if pack['pack_name'] == selected_pack), None)
            if selected_pack_id is None:
                logging.error("Invalid pack selected, no matching pack ID found.")
                st.error("Invalid pack selected. Please try again.")
                return
            logging.info(f"Selected pack ID: {selected_pack_id}")
            logging.debug(f"Payload for LLM API: {{'user_message': context, 'pack_id': selected_pack_id, 'history': st.session_state['conversation_history']}}")
            logging.debug(f"Authorization header: Bearer {st.session_state['access_token']}")

        # Call the LLM API
        logging.debug("Sending request to LLM API")
        result = send_to_llm_api(context, st.session_state['conversation_history'], selected_pack_id, st.session_state['access_token'])

        # Check for errors in the result
        if "error" in result:
            st.error(result["error"])
            logging.error(f"Error from LLM API: {result['error']}")
        else:
            assistant_message = result.get("message", "")
            st.session_state['conversation_history'].append({"role": "assistant", "content": assistant_message})
            st.markdown(f"**Assistant:** {assistant_message}")
            logging.debug(f"Assistant response: {assistant_message}")

# Main application logic
if st.session_state['page'] == 'login':
    login_page()
else:
    chat_interface()
