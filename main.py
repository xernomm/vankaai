import streamlit as st
import firebase_admin
from firebase_admin import auth, exceptions, credentials, initialize_app
import asyncio
from httpx_oauth.clients.google import GoogleOAuth2
from components import get_email_from_session_storage, set_email_to_session_storage
from app import main
import yaml
from yaml.loader import SafeLoader
import secrets   
from pages import Login

st.set_page_config(
    page_title="Vanka AI",
    page_icon="💬",
    layout="centered",
    
    # initial_sidebar_state="expanded",
    )

hide_warning_css = """
    <style>
    .stAlert {
        display: none;
    }
    .stTitle {
        text-align: center;
    }
    .css-1d391kg {
        text-align: center;
    }
    .css-1v0mbdj {
        text-align: center;
    }
    .btn-pinet {
        display: block;
        margin-left: auto;
        margin-right: auto;
        border-radius : 8px;
        padding: 2%;
        margin-top: 200px;
    }
    </style>
    """
st.markdown(hide_warning_css, unsafe_allow_html=True)

# Set up OAuth 2.0 credentials
# Initialize Firebase app
cred = credentials.Certificate("vankaai-330d9-86b390be6510.json")
try:
    firebase_admin.get_app()
except ValueError as e:
    initialize_app(cred)

# Initialize Google OAuth2 client
client_id = st.secrets["client_id"]
client_secret = st.secrets["client_secret"]
redirect_url = "http://localhost:8501/"  # Your redirect URL

client = GoogleOAuth2(client_id=client_id, client_secret=client_secret)

# Function to get the access token using the authorization code
async def get_access_token(client: GoogleOAuth2, redirect_url: str, code: str):
    return await client.get_access_token(code, redirect_url)

# Function to get the user's email using the access token
async def get_email(client: GoogleOAuth2, token: str):
    try:
        user_id, user_email = await client.get_id_email(token)
        print("User ID:", user_id)
        print("User Email:", user_email)
        return user_id, user_email
    except Exception as e:
        print("Error retrieving email:", e)
        return None

# Function to manage the login process and retrieve the user's email
def get_logged_in_user_email():
    try:
        query_params = st.experimental_get_query_params()
        code = query_params.get('code')
        if code:
            token = asyncio.run(get_access_token(client, redirect_url, code))
            st.experimental_set_query_params()

            if token:
                user_id, user_email = asyncio.run(get_email(client, token['access_token']))
                if user_email:
                    try:
                        user = auth.get_user_by_email(user_email)
                    except exceptions.FirebaseError:
                        user = auth.create_user(email=user_email)
                    st.session_state.email = user.email
                    return user.email
        return None
    except:
        pass
    
if 'email' not in st.session_state:
    st.session_state.email = None  # Initialize the email attribute
    email = get_logged_in_user_email()
    if email:
        st.session_state.email = email
        
# Display the logged-in user's email
if st.session_state.email:
    st.sidebar.subheader('Logged in as:')
    st.sidebar.write(st.session_state.email)
    main()
else:
    pass


def show_login_button():
    authorization_url = asyncio.run(client.get_authorization_url(
        redirect_url,
        scope=["email", "profile"],
        extras_params={"access_type": "offline"},
    ))
    st.markdown(
        f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Vanka</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.3.0/font/bootstrap-icons.css">
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM" crossorigin="anonymous"></script>
        </head>
        <body>
            <div class="container">
                <div class="col-12 d-lg-flex align-items-center justify-content-center mt-5">
                    <div class="col-10 text-center">
                        <h1 class="display-1">Welcome to Vanka AI!</h1>
                        <a href="{authorization_url}" type="button" class="btn col-10 btn-outline-danger text-white p-2">
                            Login with Google <span class="mb-2 ms-1"><i class="bi bi-google"></i></span>
                        </a>
                        <br>

                    
        </body>
        </html>
        """,
        unsafe_allow_html=True
    )
    get_logged_in_user_email()
    




def app():
    if not st.session_state.email:
        get_logged_in_user_email()
        if not st.session_state.email:

            show_login_button()

    if st.session_state.email:
        # st.write(st.session_state.email)
        if st.sidebar.button("Logout", type="primary", key="logout_non_required"):
            st.session_state.email = ''
            st.rerun()
        

app()
