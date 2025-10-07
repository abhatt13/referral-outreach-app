"""Tests for database module."""

import pytest
import os
import tempfile
from src.database import Database
from src.auth import AuthManager


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")

    # Initialize database
    db = Database(db_path)

    yield db

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    os.rmdir(temp_dir)


def test_create_user(test_db):
    """Test creating a user."""
    password_hash = AuthManager.hash_password("password123")
    user_id = test_db.create_user(
        email="test@example.com",
        username="testuser",
        password_hash=password_hash,
        tier="FREE"
    )

    assert user_id is not None
    assert isinstance(user_id, int)


def test_get_user_by_email(test_db):
    """Test retrieving user by email."""
    password_hash = AuthManager.hash_password("password123")
    test_db.create_user(
        email="test@example.com",
        username="testuser",
        password_hash=password_hash
    )

    user = test_db.get_user_by_email("test@example.com")

    assert user is not None
    assert user["email"] == "test@example.com"
    assert user["username"] == "testuser"
    assert user["tier"] == "FREE"
    assert user["emails_sent_count"] == 0


def test_get_user_by_username(test_db):
    """Test retrieving user by username."""
    password_hash = AuthManager.hash_password("password123")
    test_db.create_user(
        email="test@example.com",
        username="testuser",
        password_hash=password_hash
    )

    user = test_db.get_user_by_username("testuser")

    assert user is not None
    assert user["email"] == "test@example.com"
    assert user["username"] == "testuser"


def test_update_user_tier(test_db):
    """Test updating user tier."""
    password_hash = AuthManager.hash_password("password123")
    user_id = test_db.create_user(
        email="test@example.com",
        username="testuser",
        password_hash=password_hash
    )

    # Update to contributor tier
    success = test_db.update_user_tier(user_id, "CONTRIBUTOR", "cus_123")

    assert success == True

    # Verify the update
    user = test_db.get_user_by_username("testuser")
    assert user["tier"] == "CONTRIBUTOR"
    assert user["subscription_active"] == True


def test_increment_email_count(test_db):
    """Test incrementing email count."""
    password_hash = AuthManager.hash_password("password123")
    user_id = test_db.create_user(
        email="test@example.com",
        username="testuser",
        password_hash=password_hash
    )

    # Increment by 1
    count = test_db.increment_email_count(user_id, 1)
    assert count == 1

    # Increment by 5
    count = test_db.increment_email_count(user_id, 5)
    assert count == 6


def test_increment_campaign_count(test_db):
    """Test incrementing campaign count."""
    password_hash = AuthManager.hash_password("password123")
    user_id = test_db.create_user(
        email="test@example.com",
        username="testuser",
        password_hash=password_hash
    )

    # Increment campaign count
    count = test_db.increment_campaign_count(user_id)
    assert count == 1

    count = test_db.increment_campaign_count(user_id)
    assert count == 2


def test_add_contact(test_db):
    """Test adding a contact."""
    contact_id = test_db.add_contact(
        name="John Doe",
        email="john@example.com",
        title="Software Engineer",
        company="Tech Corp",
        linkedin_url="https://linkedin.com/in/johndoe"
    )

    assert contact_id is not None
    assert isinstance(contact_id, int)


def test_add_duplicate_contact(test_db):
    """Test adding duplicate contact returns same ID."""
    contact_id1 = test_db.add_contact(
        name="John Doe",
        email="john@example.com",
        title="Software Engineer",
        company="Tech Corp"
    )

    contact_id2 = test_db.add_contact(
        name="John Doe",
        email="john@example.com",
        title="Software Engineer",
        company="Tech Corp"
    )

    assert contact_id1 == contact_id2


def test_create_campaign(test_db):
    """Test creating a campaign."""
    password_hash = AuthManager.hash_password("password123")
    user_id = test_db.create_user(
        email="test@example.com",
        username="testuser",
        password_hash=password_hash
    )

    campaign_id = test_db.create_campaign(
        job_title="Software Engineer",
        company="Tech Corp",
        job_description="Looking for talented engineers",
        user_id=user_id
    )

    assert campaign_id is not None
    assert isinstance(campaign_id, int)
