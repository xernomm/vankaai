import streamlit as st
import ollama
import subprocess
from llama_index.core.llms import ChatMessage
import logging
import time
from openai import OpenAI
from utilities.icon import page_icon
import pandas as pd
import PyPDF2
from docx import Document
from io import StringIO

logging.basicConfig(level=logging.INFO)

def read_pdf(file):
    """
    Extract text from a PDF file.
    """
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text()
    return text

def read_csv(file):
    """
    Extract data from a CSV file.
    """
    return pd.read_csv(file)

def read_docx(file):
    """
    Extract text from a DOCX file.
    """
    doc = Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text

def extract_model_names(models_info: list) -> tuple:
    """
    Extracts the model names from the models information.

    :param models_info: A dictionary containing the models' information.

    Return:
        A tuple containing the model names.
    """
    return tuple(model["name"] for model in models_info["models"])

def login(username, password):
    """
    Handle the login logic.

    :param username: The username input.
    :param password: The password input.
    :return: True if login is successful, False otherwise.
    """
    # Preauthorized credentials
    preauthorized_username = "admin"
    preauthorized_password = "password"

    if username == preauthorized_username and password == preauthorized_password:
        return True
    return False

def main():
    st.header("Vanka AI 1.0")
    logging.info("App started")  # Log that the app has started

    # Initialize session state variables
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "combined_data" not in st.session_state:
        st.session_state.combined_data = ""

    # Display login form if not logged in
    if not st.session_state.logged_in:
        st.subheader("Login")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.button("Login")

        if login_button:
            if login(username, password):
                st.session_state.logged_in = True
                st.success("Login successful")
                st.experimental_rerun()  # Refresh the app to show the main interface
            else:
                st.error("Invalid username or password")
    else:
        # Add a logout button in the sidebar
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.experimental_rerun()  # Refresh the app to show the login form

        # Sidebar for model selection
        model = "llama3:latest"
        logging.info(f"Model selected: {model}")

        client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",  
        )

        # File upload section
        uploaded_files = st.file_uploader("Upload PDF, CSV, or DOCX", type=["pdf", "csv", "docx"], accept_multiple_files=True)

        if uploaded_files:
            combined_data = st.session_state.combined_data  # Get existing combined_data
            for uploaded_file in uploaded_files:
                if uploaded_file.type == "application/pdf":
                    combined_data += read_pdf(uploaded_file)
                elif uploaded_file.type == "text/csv":
                    df = read_csv(uploaded_file)
                    combined_data += df.to_csv(index=False)
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    combined_data += read_docx(uploaded_file)
                    
            st.session_state.combined_data = combined_data
            st.success("Files uploaded and processed successfully.")

        # Prompt for user input and save to chat history
        if prompt := st.chat_input("Ask Anything.."):
            try:
                st.session_state.messages.append({"role": "user", "content": prompt})
                logging.info(f"User input: {prompt}")

                # Display the user's query
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.write(message["content"])

                # Generate a new response if the last message is not from the assistant
                if st.session_state.messages[-1]["role"] != "assistant":
                    with st.chat_message("assistant"):
                        start_time = time.time()  # Start timing the response generation
                        logging.info("Generating response")

                    with st.spinner("Generating Response..."):
                        messages = [{"role": "system", "content": st.session_state.combined_data}]
                        messages += [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

                        stream = client.chat.completions.create(
                            model=model,
                            messages=messages,
                            stream=True,
                        )
                    # stream response
                    response = st.write_stream(stream)
                st.session_state.messages.append(
                        {"role": "assistant", "content": response})
                
            except Exception as e:
                # Handle errors and display an error message
                st.session_state.messages.append({"role": "assistant", "content": str(e)})
                st.error("An error occurred while generating the response.")
                logging.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
