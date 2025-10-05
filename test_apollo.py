#!/usr/bin/env python3
"""Test Apollo.io API connection."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
from apollo_client import ApolloClient

# Load environment variables
load_dotenv()

def test_apollo():
    """Test Apollo API connection."""
    print("Testing Apollo.io API...")
    print(f"API Key: {os.getenv('APOLLO_API_KEY')[:10]}...")

    try:
        apollo = ApolloClient()
        print("\n✓ Apollo client initialized")

        # Test search
        print("\nSearching for people at Google...")
        people = apollo.search_people("Google", limit=3)

        print(f"\n✓ Found {len(people)} people")

        for i, person in enumerate(people, 1):
            email_status = "✓ Unlocked" if person.get('email') else "✗ Locked"
            print(f"\n{i}. {person['name']}")
            print(f"   Title: {person['title']}")
            print(f"   Email: {person.get('email', 'Not available')} [{email_status}]")
            print(f"   LinkedIn: {person.get('linkedin_url', 'N/A')}")

        unlocked = len([p for p in people if p.get('email')])
        print(f"\n✓ {unlocked}/{len(people)} emails unlocked")

        return True

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_apollo()
    sys.exit(0 if success else 1)
