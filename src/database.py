"""Database models and utilities for tracking outreach campaigns."""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

Base = declarative_base()

class User(Base):
    """Model for storing user accounts."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(200), nullable=False, unique=True)
    username = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(200), nullable=False)
    tier = Column(String(50), default='FREE')  # FREE or CONTRIBUTOR
    emails_sent_count = Column(Integer, default=0)
    campaigns_count = Column(Integer, default=0)
    stripe_customer_id = Column(String(200))
    subscription_active = Column(Boolean, default=False)
    subscription_ends_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    # Gmail OAuth credentials (stored per user)
    gmail_token = Column(Text)  # Pickled token data
    gmail_authenticated = Column(Boolean, default=False)

    # Custom email templates (optional, per user)
    custom_initial_template = Column(Text)  # Custom initial email template
    custom_followup_template = Column(Text)  # Custom follow-up email template
    use_custom_templates = Column(Boolean, default=False)

    # Onboarding and profile completion
    profile_completed = Column(Boolean, default=False)
    profile_name = Column(String(200))
    profile_email = Column(String(200))
    profile_linkedin = Column(String(500))

    def reset_monthly_limits(self):
        """Reset monthly usage counters."""
        self.emails_sent_count = 0
        self.campaigns_count = 0

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
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
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

    # User Management Methods

    def create_user(self, email, username, password_hash, tier='FREE'):
        """Create a new user account."""
        session = self.get_session()
        try:
            user = User(
                email=email,
                username=username,
                password_hash=password_hash,
                tier=tier
            )
            session.add(user)
            session.commit()
            user_id = user.id
            return user_id
        finally:
            session.close()

    def get_user_by_email(self, email):
        """Get user by email."""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(email=email).first()
            if user:
                return {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'password_hash': user.password_hash,
                    'tier': user.tier,
                    'emails_sent_count': user.emails_sent_count,
                    'campaigns_count': user.campaigns_count,
                    'subscription_active': user.subscription_active,
                    'gmail_authenticated': user.gmail_authenticated or False,
                    'profile_completed': user.profile_completed or False,
                    'profile_name': user.profile_name,
                    'profile_email': user.profile_email,
                    'profile_linkedin': user.profile_linkedin
                }
            return None
        finally:
            session.close()

    def get_user_by_username(self, username):
        """Get user by username."""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(username=username).first()
            if user:
                return {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'password_hash': user.password_hash,
                    'tier': user.tier,
                    'emails_sent_count': user.emails_sent_count,
                    'campaigns_count': user.campaigns_count,
                    'subscription_active': user.subscription_active,
                    'gmail_authenticated': user.gmail_authenticated or False,
                    'profile_completed': user.profile_completed or False,
                    'profile_name': user.profile_name,
                    'profile_email': user.profile_email,
                    'profile_linkedin': user.profile_linkedin
                }
            return None
        finally:
            session.close()

    def update_user_tier(self, user_id, tier, stripe_customer_id=None):
        """Update user's subscription tier."""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.tier = tier
                user.subscription_active = (tier == 'CONTRIBUTOR')
                if stripe_customer_id:
                    user.stripe_customer_id = stripe_customer_id
                if tier == 'CONTRIBUTOR':
                    from datetime import timedelta
                    user.subscription_ends_at = datetime.utcnow() + timedelta(days=30)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def increment_email_count(self, user_id, count=1):
        """Increment user's email sent count."""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.emails_sent_count += count
                session.commit()
                return user.emails_sent_count
            return None
        finally:
            session.close()

    def increment_campaign_count(self, user_id):
        """Increment user's campaign count."""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.campaigns_count += 1
                session.commit()
                return user.campaigns_count
            return None
        finally:
            session.close()

    def update_last_login(self, user_id):
        """Update user's last login timestamp."""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                session.commit()
        finally:
            session.close()

    def save_gmail_token(self, user_id, token_data):
        """Save Gmail OAuth token for a user."""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                import pickle
                import base64
                # Serialize and encode token
                token_bytes = pickle.dumps(token_data)
                token_str = base64.b64encode(token_bytes).decode('utf-8')
                user.gmail_token = token_str
                user.gmail_authenticated = True
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_gmail_token(self, user_id):
        """Get Gmail OAuth token for a user."""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user and user.gmail_token:
                import pickle
                import base64
                # Decode and deserialize token
                token_bytes = base64.b64decode(user.gmail_token)
                token_data = pickle.loads(token_bytes)
                return token_data
            return None
        finally:
            session.close()

    def revoke_gmail_token(self, user_id):
        """Revoke Gmail OAuth token for a user."""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.gmail_token = None
                user.gmail_authenticated = False
                session.commit()
                return True
            return False
        finally:
            session.close()

    def save_custom_templates(self, user_id, initial_template=None, followup_template=None, use_custom=True):
        """Save custom email templates for a user."""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                if initial_template:
                    user.custom_initial_template = initial_template
                if followup_template:
                    user.custom_followup_template = followup_template
                user.use_custom_templates = use_custom
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_custom_templates(self, user_id):
        """Get custom email templates for a user."""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                return {
                    'initial': user.custom_initial_template,
                    'followup': user.custom_followup_template,
                    'use_custom': user.use_custom_templates
                }
            return None
        finally:
            session.close()

    def toggle_custom_templates(self, user_id, use_custom):
        """Toggle between custom and default templates."""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.use_custom_templates = use_custom
                session.commit()
                return True
            return False
        finally:
            session.close()

    def save_user_profile(self, user_id, name, email, linkedin):
        """Save user profile information and mark profile as completed."""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                user.profile_name = name
                user.profile_email = email
                user.profile_linkedin = linkedin
                user.profile_completed = True
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_user_profile(self, user_id):
        """Get user profile information."""
        session = self.get_session()
        try:
            user = session.query(User).filter_by(id=user_id).first()
            if user:
                return {
                    'name': user.profile_name,
                    'email': user.profile_email,
                    'linkedin': user.profile_linkedin,
                    'completed': user.profile_completed
                }
            return None
        finally:
            session.close()

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

    def create_campaign(self, job_title, company, job_description, user_id=None):
        """Create a new email campaign."""
        session = self.get_session()
        try:
            campaign = EmailCampaign(
                user_id=user_id,
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
