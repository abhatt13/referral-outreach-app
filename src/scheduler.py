"""Scheduler for automated follow-up emails."""

import time
from datetime import datetime, timedelta
from typing import Optional
import threading
from src.database import Database
from src.gmail_client import GmailClient
from src.email_templates import EmailTemplateManager

class FollowUpScheduler:
    """Scheduler for sending automated follow-up emails."""

    def __init__(self, db: Database, gmail_client: GmailClient,
                 template_manager: EmailTemplateManager,
                 followup_delay_days: int = 1):
        """
        Initialize the scheduler.

        Args:
            db: Database instance
            gmail_client: Gmail client instance
            template_manager: Email template manager
            followup_delay_days: Number of days to wait before sending follow-up
        """
        self.db = db
        self.gmail_client = gmail_client
        self.template_manager = template_manager
        self.followup_delay_days = followup_delay_days
        self.running = False
        self.thread: Optional[threading.Thread] = None

    def calculate_followup_time(self, sent_time: datetime) -> datetime:
        """Calculate when follow-up should be sent."""
        return sent_time + timedelta(days=self.followup_delay_days)

    def send_followup(self, email_log) -> bool:
        """
        Send a follow-up email for a given initial email.

        Args:
            email_log: EmailLog record from database

        Returns:
            True if sent successfully, False otherwise
        """
        session = self.db.get_session()
        try:
            # Get contact and campaign info
            from database import Contact, EmailCampaign

            contact = session.query(Contact).filter_by(id=email_log.contact_id).first()
            campaign = session.query(EmailCampaign).filter_by(id=email_log.campaign_id).first()

            if not contact or not campaign:
                print(f"Could not find contact or campaign for email log {email_log.id}")
                return False

            # Prepare recipient and job info
            recipient = {
                'email': contact.email,
                'name': contact.name,
                'first_name': contact.name.split()[0] if contact.name else 'there',
                'title': contact.title,
                'company': contact.company
            }

            job_info = {
                'job_title': campaign.job_title,
                'company': campaign.company
            }

            # Generate follow-up email
            subject, body = self.template_manager.get_followup_email(recipient, job_info)

            # Send email
            success = self.gmail_client.send_email(
                to=contact.email,
                subject=subject,
                body=body
            )

            if success:
                # Log the follow-up email
                self.db.log_email(
                    campaign_id=campaign.id,
                    contact_id=contact.id,
                    email_type='followup',
                    subject=subject,
                    body=body,
                    is_sent=True
                )

                # Mark original email as having follow-up sent
                self.db.mark_followup_sent(email_log.id)

                print(f"Follow-up sent to {contact.email}")
                return True
            else:
                print(f"Failed to send follow-up to {contact.email}")
                return False

        except Exception as e:
            print(f"Error sending follow-up: {e}")
            return False
        finally:
            session.close()

    def check_and_send_followups(self):
        """Check for emails needing follow-ups and send them."""
        emails_needing_followup = self.db.get_emails_needing_followup()

        if emails_needing_followup:
            print(f"Found {len(emails_needing_followup)} emails needing follow-up")

            for email_log in emails_needing_followup:
                try:
                    self.send_followup(email_log)
                    # Add small delay between emails to avoid rate limiting
                    time.sleep(2)
                except Exception as e:
                    print(f"Error processing follow-up for email {email_log.id}: {e}")
        else:
            print("No follow-ups needed at this time")

    def run_continuously(self, check_interval_minutes: int = 60):
        """
        Run scheduler continuously in a loop.

        Args:
            check_interval_minutes: How often to check for follow-ups (in minutes)
        """
        print(f"Starting follow-up scheduler (checking every {check_interval_minutes} minutes)")
        self.running = True

        while self.running:
            try:
                self.check_and_send_followups()
            except Exception as e:
                print(f"Error in scheduler loop: {e}")

            # Wait before next check
            for _ in range(check_interval_minutes * 60):
                if not self.running:
                    break
                time.sleep(1)

        print("Scheduler stopped")

    def start_background(self, check_interval_minutes: int = 60):
        """Start the scheduler in a background thread."""
        if self.thread and self.thread.is_alive():
            print("Scheduler is already running")
            return

        self.thread = threading.Thread(
            target=self.run_continuously,
            args=(check_interval_minutes,),
            daemon=True
        )
        self.thread.start()
        print("Follow-up scheduler started in background")

    def stop(self):
        """Stop the scheduler."""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join(timeout=5)
            print("Scheduler stopped")
        else:
            print("Scheduler is not running")

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self.running and self.thread and self.thread.is_alive()
