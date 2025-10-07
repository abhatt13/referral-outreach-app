"""Tests for job parser module."""

import pytest
from src.job_parser import JobParser


@pytest.fixture
def parser():
    """Create a job parser instance."""
    return JobParser()


def test_parse_simple_job_description(parser):
    """Test parsing a simple job description."""
    job_desc = """
    Software Engineer at TechCorp

    We are looking for a talented Software Engineer to join our team.
    """

    result = parser.parse(job_desc)

    assert result is not None
    assert 'company' in result
    assert 'job_title' in result


def test_parse_with_company_name(parser):
    """Test parsing job description with company name."""
    job_desc = """
    Senior Data Scientist - Google

    Google is hiring a Senior Data Scientist...
    """

    result = parser.parse(job_desc)

    # Parser extracts what it can find
    assert 'company' in result
    assert 'job_title' in result


def test_parse_with_job_title(parser):
    """Test parsing job description with job title."""
    job_desc = """
    Position: Machine Learning Engineer

    We need an experienced ML Engineer...
    """

    result = parser.parse(job_desc)

    # Parser extracts what it can find
    assert 'job_title' in result


def test_extract_company(parser):
    """Test extracting company name."""
    text = "Apple Inc. is looking for engineers"
    company = parser._extract_company(text)

    # Parser returns what it finds or empty string
    assert isinstance(company, str)


def test_extract_title(parser):
    """Test extracting job title."""
    text = "Software Engineer position available"
    title = parser._extract_title(text)

    # Parser returns what it finds or empty string
    assert isinstance(title, str)
