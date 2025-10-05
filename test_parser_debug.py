#!/usr/bin/env python3
"""Debug resume parser."""

import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Sample resume text (exactly as it appears in PDF)
sample_resume = """
EXPERIENCE

Data Engineer | Microsoft
2022 - Present
• Partnered with grant managers to identify analytics opportunities and delivered insights for 10+ projects by ingesting
and transforming complex datasets
• Transformed and validated data using PySpark in Azure Databricks reducing processing time by 50% and improving
data quality
• Built ETL pipelines processing 1TB+ daily data with automated monitoring and alerting systems

EDUCATION
"""

# Look for experience section
exp_section = re.search(
    r'(?:EXPERIENCE|WORK EXPERIENCE|PROFESSIONAL EXPERIENCE)[\s:-]*(.*?)(?:\n\n[A-Z][A-Z\s]+\n|EDUCATION|SKILLS|PROJECTS|$)',
    sample_resume,
    re.IGNORECASE | re.DOTALL
)

if exp_section:
    exp_text = exp_section.group(1)
    print("EXPERIENCE SECTION EXTRACTED:")
    print("=" * 60)
    print(exp_text)
    print("=" * 60)

    # Split by bullet markers
    bullets = re.split(r'\n\s*[•·∙○▪●]\s*', exp_text)

    print(f"\nFound {len(bullets)} bullet splits:")
    for i, bullet in enumerate(bullets):
        print(f"\nBullet {i}:")
        print(f"Length: {len(bullet)}")
        print(f"Content: {repr(bullet[:200])}")

