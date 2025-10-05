"""Apollo.io API client for finding people at companies."""

import requests
import os
from typing import List, Dict, Optional

class ApolloClient:
    """Client for interacting with Apollo.io API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Apollo client with API key."""
        self.api_key = api_key or os.getenv('APOLLO_API_KEY')
        if not self.api_key:
            raise ValueError("Apollo API key not found. Set APOLLO_API_KEY environment variable.")

        self.base_url = "https://api.apollo.io/v1"
        self.headers = {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'X-Api-Key': self.api_key
        }

    def search_people(self, company_name: str, titles: List[str] = None,
                     limit: int = 10) -> List[Dict]:
        """
        Search for people at a company.

        Args:
            company_name: Name of the company to search
            titles: List of job titles to filter (e.g., ['Software Engineer', 'Developer'])
            limit: Maximum number of results to return

        Returns:
            List of person dictionaries with name, email, title, etc.
        """
        url = f"{self.base_url}/mixed_people/search"

        # Default titles if none provided - targeting people who can give referrals
        if not titles:
            titles = [
                "Software Engineer",
                "Senior Software Engineer",
                "Engineering Manager",
                "Staff Engineer",
                "Principal Engineer",
                "Tech Lead",
                "Developer",
                "Programmer"
            ]

        # Build search query
        payload = {
            "q_organization_name": company_name,
            "page": 1,
            "per_page": limit,
            "organization_num_employees_ranges": ["1,10", "11,50", "51,200", "201,500", "501,1000", "1001,2000", "2001,5000", "5001,10000", "10001+"],
            "reveal_personal_emails": True,  # Request email reveals
            "reveal_phone_number": False
        }

        # Add title filters if provided
        if titles:
            payload["person_titles"] = titles

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            people = data.get('people', [])

            # Extract relevant information
            results = []
            for person in people:
                email = person.get('email')
                person_id = person.get('id')

                # Check if email is locked
                is_locked = email and ('email_not_unlocked' in email or '@domain.com' in email)

                result = {
                    'name': person.get('name', 'Unknown'),
                    'first_name': person.get('first_name', ''),
                    'last_name': person.get('last_name', ''),
                    'title': person.get('title', 'Unknown'),
                    'email': email if not is_locked else None,
                    'email_locked': is_locked,
                    'person_id': person_id,
                    'linkedin_url': person.get('linkedin_url'),
                    'company': person.get('organization', {}).get('name', company_name),
                    'company_website': person.get('organization', {}).get('website_url'),
                }

                # Try to reveal email if locked
                if is_locked and person_id:
                    revealed_email = self._reveal_email(person_id)
                    if revealed_email:
                        result['email'] = revealed_email
                        result['email_locked'] = False

                # Include person even if email is locked (we'll show warning)
                results.append(result)

            return results

        except requests.exceptions.RequestException as e:
            print(f"Error searching Apollo.io: {str(e)}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            return []

    def enrich_person(self, email: str = None, linkedin_url: str = None) -> Optional[Dict]:
        """
        Enrich a person's data using their email or LinkedIn URL.

        Args:
            email: Person's email address
            linkedin_url: Person's LinkedIn URL

        Returns:
            Dictionary with enriched person data
        """
        url = f"{self.base_url}/people/match"

        payload = {}
        if email:
            payload['email'] = email
        if linkedin_url:
            payload['linkedin_url'] = linkedin_url

        if not payload:
            return None

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            person = data.get('person', {})

            return {
                'name': person.get('name'),
                'first_name': person.get('first_name'),
                'last_name': person.get('last_name'),
                'title': person.get('title'),
                'email': person.get('email'),
                'linkedin_url': person.get('linkedin_url'),
                'company': person.get('organization', {}).get('name'),
            }

        except requests.exceptions.RequestException as e:
            print(f"Error enriching person data: {str(e)}")
            return None

    def _reveal_email(self, person_id: str) -> Optional[str]:
        """
        Reveal/unlock email for a person (uses Apollo credits).

        Args:
            person_id: Apollo person ID

        Returns:
            Revealed email address or None
        """
        url = f"{self.base_url}/people/match"

        payload = {
            "id": person_id,
            "reveal_personal_emails": True
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            person = data.get('person', {})
            email = person.get('email')

            # Check if email is actually revealed
            if email and 'email_not_unlocked' not in email and '@domain.com' not in email:
                print(f"Successfully revealed email: {email}")
                return email
            else:
                print(f"Email reveal failed or no credits remaining for person {person_id}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"Error revealing email: {str(e)}")
            return None

    def get_company_info(self, company_name: str) -> Optional[Dict]:
        """
        Get information about a company.

        Args:
            company_name: Name of the company

        Returns:
            Dictionary with company information
        """
        url = f"{self.base_url}/organizations/search"

        payload = {
            "q_organization_name": company_name,
            "page": 1,
            "per_page": 1
        }

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            organizations = data.get('organizations', [])

            if organizations:
                org = organizations[0]
                return {
                    'name': org.get('name'),
                    'website': org.get('website_url'),
                    'industry': org.get('industry'),
                    'employee_count': org.get('estimated_num_employees'),
                    'linkedin_url': org.get('linkedin_url'),
                }

            return None

        except requests.exceptions.RequestException as e:
            print(f"Error getting company info: {str(e)}")
            return None
