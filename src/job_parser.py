"""Job description parser to extract key information."""

import re
from typing import Dict, Optional

class JobParser:
    """Parser for job descriptions to extract company, title, and other info."""

    def __init__(self):
        """Initialize job parser."""
        # Common patterns for company names in job postings
        self.company_patterns = [
            r'(?:at|@)\s+([A-Z][A-Za-z0-9\s&.,]+?)(?:\s+(?:is|are|seeks|looking))',
            r'Company:\s*([A-Z][A-Za-z0-9\s&.,]+)',
            r'^([A-Z][A-Za-z0-9\s&.,]+?)\s+(?:is|are)\s+(?:hiring|seeking|looking)',
        ]

        # Common patterns for job titles
        self.title_patterns = [
            r'(?:Position|Role|Title):\s*(.+?)(?:\n|$)',
            r'(?:hiring|seeking)\s+(?:a|an)\s+(.+?)(?:\s+to|\s+at|\n|$)',
        ]

    def parse(self, job_description: str) -> Dict[str, Optional[str]]:
        """
        Parse job description to extract key information.

        Args:
            job_description: Full job description text

        Returns:
            Dictionary with extracted information (company, title, description)
        """
        result = {
            'company': None,
            'job_title': None,
            'description': job_description.strip()
        }

        # Try to extract company name
        result['company'] = self._extract_company(job_description)

        # Try to extract job title
        result['job_title'] = self._extract_title(job_description)

        return result

    def _extract_company(self, text: str) -> Optional[str]:
        """Extract company name from job description."""
        # Try each pattern
        for pattern in self.company_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                company = match.group(1).strip()
                # Clean up common suffixes
                company = re.sub(r'\s+(Inc\.?|LLC|Ltd\.?|Corporation|Corp\.?)$', '', company)
                return company

        # If no pattern matches, try to find capitalized words at the beginning
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if len(line) > 3 and line[0].isupper():
                # Check if it looks like a company name
                words = line.split()
                if len(words) <= 5 and all(w[0].isupper() or w.lower() in ['and', 'the', 'of', '&'] for w in words if w):
                    return line

        return None

    def _extract_title(self, text: str) -> Optional[str]:
        """Extract job title from job description."""
        # Try each pattern
        for pattern in self.title_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                title = match.group(1).strip()
                # Remove common trailing words
                title = re.sub(r'\s+(?:position|role|opportunity)$', '', title, flags=re.IGNORECASE)
                return title

        # Look for common job titles in the first few lines
        common_titles = [
            r'Software Engineer', r'Senior Software Engineer', r'Staff Engineer',
            r'Engineering Manager', r'Product Manager', r'Data Scientist',
            r'Frontend Developer', r'Backend Developer', r'Full[- ]?Stack Developer',
            r'DevOps Engineer', r'Machine Learning Engineer', r'Tech Lead'
        ]

        for title_pattern in common_titles:
            match = re.search(title_pattern, text[:500], re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    def extract_from_url(self, url: str) -> Dict[str, Optional[str]]:
        """
        Extract information from a job posting URL.
        Useful for LinkedIn, Indeed, etc.

        Args:
            url: Job posting URL

        Returns:
            Dictionary with extracted information
        """
        result = {
            'company': None,
            'job_title': None,
            'url': url
        }

        # LinkedIn URL pattern: /jobs/view/{id}
        if 'linkedin.com' in url:
            # Would need to scrape the page or use LinkedIn API
            pass

        # Indeed URL pattern
        elif 'indeed.com' in url:
            # Would need to scrape the page
            pass

        return result

    def validate_extraction(self, parsed_data: Dict) -> bool:
        """
        Validate that we have minimum required information.

        Args:
            parsed_data: Parsed job data

        Returns:
            True if valid, False otherwise
        """
        return parsed_data.get('company') is not None

    def manual_input(self, company: str, job_title: str, description: str = '') -> Dict:
        """
        Create job info from manual input.

        Args:
            company: Company name
            job_title: Job title
            description: Optional job description

        Returns:
            Dictionary with job information
        """
        return {
            'company': company.strip(),
            'job_title': job_title.strip(),
            'description': description.strip() if description else ''
        }
