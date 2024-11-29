import subprocess
import sys

# List of required packages
REQUIRED_PACKAGES = [
    "streamlit",
    "google-auth-oauthlib",
    "google-auth-httplib2",
    "google-api-python-client",
    "requests",
    "pillow",
    "yt-dlp",  # You may want this for other functionalities like video download, if needed
]

# Check if packages are installed, and install them if not
for package in REQUIRED_PACKAGES:
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Now import the necessary libraries
import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import time
import random
import json

# Globals
users = {"user1": "user1@gmail.com", "user2": "user2@gmail.com"}
chat_history = []
meet_links = {}

# Google API Setup
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CLIENT_SECRET_FILE = "client_secret.json"  # Ensure this is the correct path to your OAuth 2.0 client secrets file

# Helper Functions
def authenticate_google():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=SCOPES,
        redirect_uri="http://localhost:8501"
    )
    flow.run_local_server(port=8501)
    credentials = flow.credentials
    return build("calendar", "v3", credentials=credentials)

def create_google_meet(calendar_service, sender_email, recipient_email):
    # Create a calendar event with a Google Meet link
    event = {
        "summary": "Secure Chat Video Call",
        "description": f"Video call between {sender_email} and {recipient_email}",
        "start": {"dateTime": "2024-11-29T10:00:00Z", "timeZone": "UTC"},
        "end": {"dateTime": "2024-11-29T11:00:00Z", "timeZone": "UTC"},
        "attendees": [{"email": sender_email}, {"email": recipient_email}],
        "conferenceData": {"createRequest": {"requestId": f"{random.randint(1,100000)}"}},
    }
    event = calendar_service.events().insert(
        calendarId="primary", body=event, conferenceDataVersion=1
    ).execute()
    return event["hangoutLink"]

# Initialize Streamlit session state
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None
if "current_contact" not in st.session_state:
    st.session_state["current_contact"] = None
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "meet_links" not in st.session_state:
    st.session_state["meet_links"] = {}

# User Authentication/Login
def login():
    st.title("Login")
    username = st.text_input("Enter your username:")
    if st.button("Login"):
        if username in users:
            st.session_state["current_user"] = username
            st.success(f"Logged in as {username}")
        else:
            st.error("User does not exist!")

# User Selection and Status Display
def select_user():
    st.sidebar.header("Contacts")
    for user, email in users.items():
        if user != st.session_state["current_user"] and st.sidebar.button(f"Chat with {user}"):
            st.session_state["current_contact"] = user
            st.session_state["chat_history"] = []

    st.sidebar.header("Your Status")
    status = st.radio("Update your status:", ["online", "busy", "offline"])
    st.sidebar.text(f"Status: {status}")

# Chat Interface
def chat_interface():
    st.title(f"Chat with {st.session_state['current_contact']}")
    for msg in chat_history:
        if msg["sender"] == st.session_state["current_user"]:
            st.write(f"You: {msg['text']}")
        else:
            st.write(f"{st.session_state['current_contact']}: {msg['text']}")

    message = st.text_input("Type a message:")
    if st.button("Send"):
        chat_history.append(
            {"sender": st.session_state["current_user"], "receiver": st.session_state["current_contact"], "text": message}
        )
        st.experimental_rerun()

# Google Meet Integration
def video_call_interface():
    st.sidebar.header("Voice & Video Calls")
    if st.sidebar.button("Start Video Call"):
        # Authenticate with Google and create a Meet link
        calendar_service = authenticate_google()
        sender_email = users[st.session_state["current_user"]]
        recipient_email = users[st.session_state["current_contact"]]
        meet_link = create_google_meet(calendar_service, sender_email, recipient_email)
        st.session_state["meet_links"][st.session_state["current_contact"]] = meet_link
        st.sidebar.success(f"Meet link created: {meet_link}")
        st.experimental_rerun()

    if st.session_state["current_contact"] in st.session_state["meet_links"]:
        meet_link = st.session_state["meet_links"][st.session_state["current_contact"]]
        if st.sidebar.button("Join Video Call"):
            st.sidebar.write(f"[Join Google Meet]({meet_link})")

# Main Application Logic
if st.session_state["current_user"] is None:
    login()
else:
    select_user()
    if st.session_state["current_contact"]:
        chat_interface()
        video_call_interface()
