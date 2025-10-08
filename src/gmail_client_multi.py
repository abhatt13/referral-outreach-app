"""Multi-user Gmail API client for sending emails."""

import os
import pickle
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class MultiUserGmailClient:
    """Client for sending emails via Gmail API with per-user authentication."""

    def __init__(self, credentials_file: str = 'credentials.json'):
        """
        Initialize Gmail client.

        Args:
            credentials_file: Path to OAuth credentials JSON file
        """
        self.credentials_file = credentials_file
        self.service = None

    def get_authorization_url(self, redirect_uri: str = 'https://carole-villainous-ineffably.ngrok-free.dev'):
        """
        Get OAuth authorization URL for user to authenticate.

        Args:
            redirect_uri: OAuth redirect URI (must match Google Cloud Console config)

        Returns:
            Tuple of (authorization_url, flow_state)
        """
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(
                f"Credentials file '{self.credentials_file}' not found. "
                "Download it from Google Cloud Console."
            )

        flow = Flow.from_client_secrets_file(
            self.credentials_file,
            scopes=SCOPES,
            redirect_uri=redirect_uri
        )

        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        return auth_url, flow

    def exchange_code_for_token(self, flow, auth_code: str):
        """
        Exchange authorization code for access token.

        Args:
            flow: OAuth flow object
            auth_code: Authorization code from OAuth callback

        Returns:
            Credentials object
        """
        flow.fetch_token(code=auth_code)
        return flow.credentials

    def authenticate_with_token(self, token_data):
        """
        Authenticate Gmail service with existing token.

        Args:
            token_data: Credentials object or dict

        Returns:
            bool: True if authentication successful
        """
        try:
            if isinstance(token_data, dict):
                creds = Credentials.from_authorized_user_info(token_data, SCOPES)
            else:
                creds = token_data

            # Refresh if expired
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            self.service = build('gmail', 'v1', credentials=creds)
            return True
        except Exception as e:
            print(f"Error authenticating: {e}")
            return False

    def send_email(self, to_email: str, subject: str, body: str,
                   from_email: Optional[str] = None) -> bool:
        """
        Send an email via Gmail API.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            from_email: Sender email (optional, uses authenticated user's email)

        Returns:
            bool: True if email sent successfully
        """
        if not self.service:
            print("Gmail service not authenticated. Please authenticate first.")
            return False

        try:
            message = MIMEMultipart('alternative')
            message['To'] = to_email
            message['Subject'] = subject
            if from_email:
                message['From'] = from_email

            # Add body as both plain text and HTML
            text_part = MIMEText(body, 'plain')
            html_part = MIMEText(body.replace('\n', '<br>'), 'html')

            message.attach(text_part)
            message.attach(html_part)

            # Encode the message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            send_message = {'raw': raw_message}

            # Send the email
            result = self.service.users().messages().send(
                userId='me',
                body=send_message
            ).execute()

            print(f"Email sent successfully to {to_email}. Message ID: {result.get('id')}")
            return True

        except HttpError as error:
            print(f"An error occurred: {error}")
            return False
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def get_user_email(self) -> Optional[str]:
        """
        Get the authenticated user's email address.

        Returns:
            User's email address or None
        """
        if not self.service:
            return None

        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return profile.get('emailAddress')
        except Exception as e:
            print(f"Error getting user email: {e}")
            return None
