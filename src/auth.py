"""Authentication module with JWT and tier-based access control."""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict
import os
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


class TierLimits:
    """Define limits for each subscription tier."""

    FREE = {
        'name': 'Free',
        'price': 0,
        'email_send_limit': 3,
        'campaigns_per_month': 1,
    }

    CONTRIBUTOR = {
        'name': 'Contributor',
        'price': 5,
        'email_send_limit': 30,
        'campaigns_per_month': 10,
    }

    @staticmethod
    def get_tier(tier_name: str) -> Dict:
        """Get tier configuration by name."""
        if tier_name.upper() == 'CONTRIBUTOR':
            return TierLimits.CONTRIBUTOR
        return TierLimits.FREE


class AuthManager:
    """Handle user authentication and authorization."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_access_token(token: str) -> Optional[Dict]:
        """Decode and validate a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def check_tier_limit(user_tier: str, emails_sent_count: int) -> bool:
        """Check if user has exceeded their tier's email limit."""
        tier_config = TierLimits.get_tier(user_tier)
        return emails_sent_count < tier_config['email_send_limit']

    @staticmethod
    def get_remaining_emails(user_tier: str, emails_sent_count: int) -> int:
        """Get remaining email sends for user's tier."""
        tier_config = TierLimits.get_tier(user_tier)
        remaining = tier_config['email_send_limit'] - emails_sent_count
        return max(0, remaining)
