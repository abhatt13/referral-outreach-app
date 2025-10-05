#!/usr/bin/env python3
"""Test improved resume parser."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from resume_parser import ResumeParser

# Sample resume text with experience section
sample_resume = """
AAKASH BHATT
aakash@example.com | https://linkedin.com/in/aakash

EXPERIENCE

Data Engineer | Microsoft
2022 - Present
• Partnered with grant managers to identify analytics opportunities and delivered insights for 10+ projects by ingesting and transforming complex datasets
• Transformed and validated data using PySpark in Azure Databricks reducing processing time by 50% and improving data quality
• Built ETL pipelines processing 1TB+ daily data with automated monitoring and alerting systems

Software Engineer | Amazon
2020 - 2022
• Developed microservices using Python and AWS Lambda serving 1M+ requests per day with 99.9% uptime
• Implemented CI/CD pipelines using Jenkins and Docker, reducing deployment time from hours to minutes

SKILLS
Languages / Databases: Python, Java, SQL, PostgreSQL, MongoDB
Cloud & Tools: AWS, Azure, Docker, Kubernetes, Git
Frameworks: Django, Flask, React, Node.js

EDUCATION
Master of Science in Computer Science | Stanford University
"""

# Sample job description
job_description = """
Software Engineer - Data Platform

We are looking for a Software Engineer to join our Data Platform team. You will work on:
- Building scalable data pipelines using Python and PySpark
- Working with cloud technologies (AWS, Azure, or GCP)
- Implementing ETL processes for large-scale data processing
- Collaborating with data scientists and analysts

Requirements:
- Strong Python programming skills
- Experience with PySpark, Databricks, or similar big data technologies
- Knowledge of cloud platforms (AWS/Azure/GCP)
- Experience with data engineering and ETL pipelines
"""

def test_parser():
    """Test the resume parser."""
    print("Testing Resume Parser...")
    print("=" * 60)

    parser = ResumeParser()

    # Parse resume
    parsed = parser.parse_text(sample_resume)

    print(f"\n✓ Name: {parsed['name']}")
    print(f"✓ Email: {parsed['email']}")
    print(f"✓ LinkedIn: {parsed['linkedin']}")

    print(f"\n✓ Skills ({len(parsed['skills'])} found):")
    for skill in parsed['skills'][:5]:
        print(f"  - {skill}")

    print(f"\n✓ Experience bullets ({len(parsed['experience'])} found):")
    for i, exp in enumerate(parsed['experience'], 1):
        print(f"  {i}. {exp[:100]}..." if len(exp) > 100 else f"  {i}. {exp}")

    print("\n" + "=" * 60)
    print("Testing Job Matching...")
    print("=" * 60)

    # Test without job description
    print("\n1. WITHOUT Job Description:")
    formatted = parser.format_for_email(parsed)
    for i, skill in enumerate(formatted['your_skills'], 1):
        print(f"  {i}. {skill}")

    # Test WITH job description
    print("\n2. WITH Job Description (Data Engineering role):")
    formatted_matched = parser.format_for_email(parsed, job_description)
    for i, skill in enumerate(formatted_matched['your_skills'], 1):
        print(f"  {i}. {skill}")

    print("\n" + "=" * 60)
    print("✅ Parser test completed!")
    return True

if __name__ == "__main__":
    success = test_parser()
    sys.exit(0 if success else 1)
