"""Tests for authentication module."""

import pytest
from src.auth import AuthManager, TierLimits


def test_password_hashing():
    """Test password hashing and verification."""
    password = "test_password_123"
    hashed = AuthManager.hash_password(password)

    # Verify correct password
    assert AuthManager.verify_password(password, hashed) == True

    # Verify incorrect password
    assert AuthManager.verify_password("wrong_password", hashed) == False


def test_create_access_token():
    """Test JWT token creation."""
    data = {"user_id": 1, "username": "testuser"}
    token = AuthManager.create_access_token(data)

    # Token should be a non-empty string
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token():
    """Test JWT token decoding."""
    data = {"user_id": 1, "username": "testuser"}
    token = AuthManager.create_access_token(data)

    # Decode the token
    decoded = AuthManager.decode_access_token(token)

    assert decoded is not None
    assert decoded["user_id"] == 1
    assert decoded["username"] == "testuser"


def test_decode_invalid_token():
    """Test decoding invalid JWT token."""
    invalid_token = "invalid.token.here"
    decoded = AuthManager.decode_access_token(invalid_token)

    assert decoded is None


def test_tier_limits_free():
    """Test free tier limits."""
    tier = TierLimits.get_tier("FREE")

    assert tier["name"] == "Free"
    assert tier["price"] == 0
    assert tier["email_send_limit"] == 3
    assert tier["campaigns_per_month"] == 1


def test_tier_limits_contributor():
    """Test contributor tier limits."""
    tier = TierLimits.get_tier("CONTRIBUTOR")

    assert tier["name"] == "Contributor"
    assert tier["price"] == 5
    assert tier["email_send_limit"] == 30
    assert tier["campaigns_per_month"] == 10


def test_check_tier_limit():
    """Test tier limit checking."""
    # Free tier with 2 emails sent (under limit)
    assert AuthManager.check_tier_limit("FREE", 2) == True

    # Free tier with 3 emails sent (at limit)
    assert AuthManager.check_tier_limit("FREE", 3) == False

    # Contributor tier with 29 emails sent (under limit)
    assert AuthManager.check_tier_limit("CONTRIBUTOR", 29) == True

    # Contributor tier with 30 emails sent (at limit)
    assert AuthManager.check_tier_limit("CONTRIBUTOR", 30) == False


def test_get_remaining_emails():
    """Test getting remaining emails."""
    # Free tier with 0 sent
    assert AuthManager.get_remaining_emails("FREE", 0) == 3

    # Free tier with 2 sent
    assert AuthManager.get_remaining_emails("FREE", 2) == 1

    # Free tier with 3 sent
    assert AuthManager.get_remaining_emails("FREE", 3) == 0

    # Contributor tier with 20 sent
    assert AuthManager.get_remaining_emails("CONTRIBUTOR", 20) == 10
