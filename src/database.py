"""Database models and utilities for tracking outreach campaigns."""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class Contact(Base):
    """Model for storing contact information."""
    __tablename__ = 'contacts'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200), nullable=False, unique=True)
    title = Column(String(200))
    company = Column(String(200), nullable=False)
    linkedin_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

class EmailCampaign(Base):
    """Model for tracking email campaigns."""
    __tablename__ = 'email_campaigns'

    id = Column(Integer, primary_key=True)
    job_title = Column(String(300), nullable=False)
    company = Column(String(200), nullable=False)
    job_description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class EmailLog(Base):
    """Model for logging sent emails."""
    __tablename__ = 'email_logs'

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, nullable=False)
    contact_id = Column(Integer, nullable=False)
    email_type = Column(String(50), nullable=False)  # 'initial' or 'followup'
    subject = Column(String(500))
    body = Column(Text)
    sent_at = Column(DateTime, default=datetime.utcnow)
    is_sent = Column(Boolean, default=False)
    followup_sent = Column(Boolean, default=False)
    followup_scheduled_at = Column(DateTime)
    error_message = Column(Text)

class Database:
    """Database manager class."""

    def __init__(self, db_path='data/outreach.db'):
        """Initialize database connection."""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        """Get a new database session."""
        return self.Session()

    def add_contact(self, name, email, title, company, linkedin_url=None):
        """Add a new contact to the database."""
        session = self.get_session()
        try:
            # Check if contact already exists
            existing = session.query(Contact).filter_by(email=email).first()
            if existing:
                contact_id = existing.id
                session.close()
                return contact_id

            contact = Contact(
                name=name,
                email=email,
                title=title,
                company=company,
                linkedin_url=linkedin_url
            )
            session.add(contact)
            session.commit()
            contact_id = contact.id
            return contact_id
        finally:
            session.close()

    def create_campaign(self, job_title, company, job_description):
        """Create a new email campaign."""
        session = self.get_session()
        try:
            campaign = EmailCampaign(
                job_title=job_title,
                company=company,
                job_description=job_description
            )
            session.add(campaign)
            session.commit()
            campaign_id = campaign.id
            return campaign_id
        finally:
            session.close()

    def log_email(self, campaign_id, contact_id, email_type, subject, body,
                   is_sent=False, error_message=None, followup_scheduled_at=None):
        """Log an email send attempt."""
        session = self.get_session()
        try:
            email_log = EmailLog(
                campaign_id=campaign_id,
                contact_id=contact_id,
                email_type=email_type,
                subject=subject,
                body=body,
                is_sent=is_sent,
                error_message=error_message,
                followup_scheduled_at=followup_scheduled_at
            )
            session.add(email_log)
            session.commit()
            return email_log
        finally:
            session.close()

    def get_emails_needing_followup(self):
        """Get emails that need follow-up sent."""
        session = self.get_session()
        try:
            now = datetime.utcnow()
            emails = session.query(EmailLog).filter(
                EmailLog.email_type == 'initial',
                EmailLog.is_sent == True,
                EmailLog.followup_sent == False,
                EmailLog.followup_scheduled_at <= now
            ).all()
            return emails
        finally:
            session.close()

    def mark_followup_sent(self, email_log_id):
        """Mark that a follow-up has been sent."""
        session = self.get_session()
        try:
            email_log = session.query(EmailLog).filter_by(id=email_log_id).first()
            if email_log:
                email_log.followup_sent = True
                session.commit()
        finally:
            session.close()

    def get_campaign_stats(self, campaign_id):
        """Get statistics for a campaign."""
        session = self.get_session()
        try:
            total_sent = session.query(EmailLog).filter_by(
                campaign_id=campaign_id,
                email_type='initial',
                is_sent=True
            ).count()

            total_followups = session.query(EmailLog).filter_by(
                campaign_id=campaign_id,
                email_type='followup',
                is_sent=True
            ).count()

            return {
                'total_initial_sent': total_sent,
                'total_followups_sent': total_followups
            }
        finally:
            session.close()
