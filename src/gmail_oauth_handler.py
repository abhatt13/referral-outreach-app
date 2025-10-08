"""Automatic Gmail OAuth handler for Streamlit."""

import streamlit as st
from src.gmail_client_multi import MultiUserGmailClient
from src.database import Database


def handle_gmail_oauth_callback():
    """Handle OAuth callback from Google."""
    # Check if we have an OAuth code in the URL
    query_params = st.query_params

    if 'code' in query_params:
        code = query_params['code']

        # Check if we have a flow in session state
        if 'gmail_flow' in st.session_state and st.session_state.authenticated:
            try:
                gmail_client = MultiUserGmailClient()
                flow = st.session_state.gmail_flow

                # Exchange code for token
                creds = gmail_client.exchange_code_for_token(flow, code)

                # Save token to database
                db = Database()
                user = st.session_state.user
                db.save_gmail_token(user['id'], creds)

                # Refresh user data
                st.session_state.user = db.get_user_by_username(user['username'])

                # Clear the flow from session
                del st.session_state.gmail_flow

                # Clear query params
                st.query_params.clear()

                st.success("✅ Gmail connected successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"Error connecting Gmail: {str(e)}")
                st.query_params.clear()


def initiate_gmail_oauth(app_url: str):
    """
    Initiate Gmail OAuth flow.

    Args:
        app_url: The base URL of the app (for redirect)
    """
    try:
        gmail_client = MultiUserGmailClient()

        # Use the app URL as redirect URI
        redirect_uri = app_url.rstrip('/')

        auth_url, flow = gmail_client.get_authorization_url(redirect_uri=redirect_uri)

        # Store flow in session state
        st.session_state.gmail_flow = flow

        # Redirect user to Google OAuth
        st.markdown(f"""
        <meta http-equiv="refresh" content="0; url={auth_url}">
        """, unsafe_allow_html=True)

        st.info("Redirecting to Google for authorization...")

    except Exception as e:
        st.error(f"Error starting OAuth flow: {str(e)}")
