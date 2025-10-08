"""Automatic Gmail OAuth handler for Streamlit."""

import streamlit as st
from src.gmail_client_multi import MultiUserGmailClient
from src.database import Database


def handle_gmail_oauth_callback():
    """Handle OAuth callback from Google."""
    # Check if we have an OAuth code in the URL
    query_params = st.query_params

    if 'code' in query_params and 'state' in query_params:
        code = query_params['code']
        state = query_params['state']

        # Extract user_id from state parameter
        try:
            import json
            state_data = json.loads(state)
            user_id = state_data.get('user_id')

            if not user_id:
                st.error("Invalid OAuth state")
                st.query_params.clear()
                return

            # Get user from database
            db = Database()
            user = db.get_user_by_username(state_data.get('username'))

            if not user:
                st.error("User not found")
                st.query_params.clear()
                return

            # Recreate the flow
            gmail_client = MultiUserGmailClient()
            from google_auth_oauthlib.flow import Flow
            flow = Flow.from_client_secrets_file(
                gmail_client.credentials_file,
                scopes=['https://www.googleapis.com/auth/gmail.send'],
                redirect_uri=state_data.get('redirect_uri')
            )

            # Exchange code for token
            flow.fetch_token(code=code)
            creds = flow.credentials

            # Save token to database
            db.save_gmail_token(user['id'], creds)

            # Set session state
            st.session_state.authenticated = True
            st.session_state.user = user
            st.session_state.token = state_data.get('jwt_token')

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
        import json
        gmail_client = MultiUserGmailClient()

        # Use the app URL as redirect URI
        redirect_uri = app_url.rstrip('/')

        # Get user info from session
        user = st.session_state.user
        jwt_token = st.session_state.token

        # Create state parameter with user info
        state_data = {
            'user_id': user['id'],
            'username': user['username'],
            'jwt_token': jwt_token,
            'redirect_uri': redirect_uri
        }
        state_param = json.dumps(state_data)

        # Get authorization URL with custom state
        from google_auth_oauthlib.flow import Flow
        flow = Flow.from_client_secrets_file(
            gmail_client.credentials_file,
            scopes=['https://www.googleapis.com/auth/gmail.send'],
            redirect_uri=redirect_uri,
            state=state_param
        )

        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        # Redirect user to Google OAuth
        st.markdown(f"""
        <meta http-equiv="refresh" content="0; url={auth_url}">
        """, unsafe_allow_html=True)

        st.info("Redirecting to Google for authorization...")

    except Exception as e:
        st.error(f"Error starting OAuth flow: {str(e)}")
