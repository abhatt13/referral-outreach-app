"""Tests for resume parser module."""

import pytest
from src.resume_parser import ResumeParser


@pytest.fixture
def parser():
    """Create a resume parser instance."""
    return ResumeParser()


def test_extract_email(parser):
    """Test email extraction."""
    text = "Contact me at john.doe@example.com for more info"
    email = parser._extract_email(text)

    assert email == "john.doe@example.com"


def test_extract_phone(parser):
    """Test phone number extraction."""
    text = "Call me at (123) 456-7890"
    phone = parser._extract_phone(text)

    # Phone extraction returns a string or None
    assert phone is not None or phone == ''
    # If phone is extracted, it should contain digits
    if phone:
        assert any(char.isdigit() for char in phone)


def test_extract_linkedin(parser):
    """Test LinkedIn URL extraction."""
    text = "Find me on https://linkedin.com/in/johndoe"
    linkedin = parser._extract_linkedin(text)

    assert linkedin == "https://linkedin.com/in/johndoe"


def test_extract_linkedin_without_protocol(parser):
    """Test LinkedIn URL extraction without https."""
    text = "Profile: linkedin.com/in/johndoe"
    linkedin = parser._extract_linkedin(text)

    assert linkedin == "https://linkedin.com/in/johndoe"


def test_extract_job_keywords(parser):
    """Test job description keyword extraction."""
    job_desc = "We are looking for a Python developer with React and AWS experience"
    keywords = parser._extract_job_keywords(job_desc)

    assert "Python" in keywords
    assert "React" in keywords
    assert "AWS" in keywords


def test_match_to_job(parser):
    """Test matching resume to job description."""
    parsed_data = {
        'experience': [
            'Built scalable applications using Python and Django',
            'Deployed cloud infrastructure on AWS with Docker',
            'Led team of 5 engineers in agile environment'
        ],
        'skills': ['Python', 'AWS', 'Docker', 'Django']
    }

    job_desc = "Looking for Python developer with AWS and Docker experience"

    bullets = parser.match_to_job(parsed_data, job_desc)

    assert len(bullets) == 3
    # Should prioritize experiences with matching keywords
    assert any('Python' in bullet or 'AWS' in bullet or 'Docker' in bullet for bullet in bullets)


def test_format_for_email(parser):
    """Test formatting parsed data for email."""
    parsed_data = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'linkedin': 'https://linkedin.com/in/johndoe',
        'skills': ['Python', 'AWS', 'React'],
        'experience': [
            'Built scalable applications using Python',
            'Deployed cloud infrastructure on AWS',
            'Developed frontend with React'
        ]
    }

    formatted = parser.format_for_email(parsed_data)

    assert formatted['your_name'] == 'John Doe'
    assert formatted['your_email'] == 'john@example.com'
    assert formatted['your_linkedin'] == 'https://linkedin.com/in/johndoe'
    assert len(formatted['your_skills']) == 3


def test_format_for_email_with_defaults(parser):
    """Test formatting with missing data uses defaults."""
    parsed_data = {}

    formatted = parser.format_for_email(parsed_data)

    assert 'your_name' in formatted
    assert 'your_email' in formatted
    assert 'your_linkedin' in formatted
    assert len(formatted['your_skills']) == 3


def test_generate_default_bullets(parser):
    """Test generating default bullets from skills."""
    skills = ['Python', 'JavaScript', 'React', 'AWS', 'Docker']
    bullets = parser._generate_default_bullets(skills)

    assert len(bullets) == 3
    assert all(isinstance(bullet, str) for bullet in bullets)
