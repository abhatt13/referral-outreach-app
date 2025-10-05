"""Gmail API client for sending emails."""

import os
import pickle
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

class GmailClient:
    """Client for sending emails via Gmail API."""

    def __init__(self, credentials_file: str = 'credentials.json',
                 token_file: str = 'token.pickle'):
        """
        Initialize Gmail client.

        Args:
            credentials_file: Path to OAuth credentials JSON file
            token_file: Path to store/load the authentication token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Gmail API using OAuth 2.0."""
        creds = None

        # Load existing credentials
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}\n"
                        "Please download OAuth credentials from Google Cloud Console:\n"
                        "1. Go to https://console.cloud.google.com/\n"
                        "2. Create a project or select existing one\n"
                        "3. Enable Gmail API\n"
                        "4. Create OAuth 2.0 credentials (Desktop app)\n"
                        "5. Download and save as credentials.json"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)

    def create_message(self, to: str, subject: str, body: str,
                      from_email: Optional[str] = None) -> dict:
        """
        Create an email message.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (HTML or plain text)
            from_email: Sender email (defaults to authenticated account)

        Returns:
            Dictionary containing the message
        """
        message = MIMEMultipart('alternative')
        message['To'] = to
        message['Subject'] = subject
        if from_email:
            message['From'] = from_email

        # Attach body (treat as HTML if it contains HTML tags)
        if '<html>' in body.lower() or '<br>' in body.lower():
            part = MIMEText(body, 'html')
        else:
            part = MIMEText(body, 'plain')
        message.attach(part)

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw_message}

    def send_email(self, to: str, subject: str, body: str,
                   from_email: Optional[str] = None) -> bool:
        """
        Send an email via Gmail.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            from_email: Sender email (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            message = self.create_message(to, subject, body, from_email)
            sent_message = self.service.users().messages().send(
                userId='me', body=message).execute()

            print(f"Email sent successfully to {to}. Message ID: {sent_message['id']}")
            return True

        except HttpError as error:
            print(f"Error sending email to {to}: {error}")
            return False
        except Exception as e:
            print(f"Unexpected error sending email to {to}: {e}")
            return False

    def send_bulk_emails(self, recipients: list, subject: str, body_template: str,
                        personalization_func=None) -> dict:
        """
        Send emails to multiple recipients.

        Args:
            recipients: List of recipient dictionaries with 'email', 'name', etc.
            subject: Email subject (can include {name}, {company} placeholders)
            body_template: Email body template (can include placeholders)
            personalization_func: Optional function to personalize each email

        Returns:
            Dictionary with success/failure counts and details
        """
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }

        for recipient in recipients:
            try:
                # Personalize subject and body
                personalized_subject = subject.format(**recipient)

                if personalization_func:
                    personalized_body = personalization_func(body_template, recipient)
                else:
                    personalized_body = body_template.format(**recipient)

                # Send email
                success = self.send_email(
                    to=recipient['email'],
                    subject=personalized_subject,
                    body=personalized_body
                )

                if success:
                    results['sent'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'email': recipient['email'],
                        'error': 'Failed to send'
                    })

            except KeyError as e:
                results['failed'] += 1
                results['errors'].append({
                    'email': recipient.get('email', 'unknown'),
                    'error': f'Missing template variable: {str(e)}'
                })
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'email': recipient.get('email', 'unknown'),
                    'error': str(e)
                })

        return results

    def get_user_email(self) -> Optional[str]:
        """Get the authenticated user's email address."""
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return profile.get('emailAddress')
        except Exception as e:
            print(f"Error getting user email: {e}")
            return None
