"""Email template management."""

import os
from typing import Dict

class EmailTemplateManager:
    """Manager for email templates."""

    def __init__(self, templates_dir: str = 'templates'):
        """Initialize template manager."""
        self.templates_dir = templates_dir

        # Default user info (should be configured by user)
        self.user_info = {
            'your_name': '[YOUR_NAME]',
            'your_email': '[YOUR_EMAIL]',
            'your_linkedin': '[YOUR_LINKEDIN]',
            'your_skills': [
                '[ADD YOUR KEY SKILL/EXPERIENCE 1]',
                '[ADD YOUR KEY SKILL/EXPERIENCE 2]',
                '[ADD YOUR KEY SKILL/EXPERIENCE 3]'
            ]
        }

    def load_template(self, template_name: str) -> str:
        """Load a template from file."""
        template_path = os.path.join(self.templates_dir, template_name)

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, 'r') as f:
            return f.read()

    def set_user_info(self, name: str, email: str, linkedin: str, skills: list):
        """Set user information for personalization."""
        self.user_info = {
            'your_name': name,
            'your_email': email,
            'your_linkedin': linkedin,
            'your_skills': skills
        }

    def personalize_email(self, template: str, recipient: Dict, job_info: Dict) -> tuple:
        """
        Personalize email template with recipient and job information.

        Args:
            template: Email template string
            recipient: Dictionary with recipient info (name, email, title, company)
            job_info: Dictionary with job info (title, company, description)

        Returns:
            Tuple of (subject, body)
        """
        # Split subject and body
        lines = template.split('\n')
        subject_line = ''
        body_lines = []

        for i, line in enumerate(lines):
            if line.startswith('Subject:'):
                subject_line = line.replace('Subject:', '').strip()
            elif subject_line and i > 0:  # Skip the subject line and get body
                body_lines.append(line)

        body = '\n'.join(body_lines).strip()

        # Prepare replacement dictionary
        replacements = {
            'first_name': recipient.get('first_name', recipient.get('name', '').split()[0] if recipient.get('name') else 'there'),
            'name': recipient.get('name', 'there'),
            'recipient_title': recipient.get('title', 'your role'),
            'company': job_info.get('company', recipient.get('company', '')),
            'job_title': job_info.get('job_title', ''),
            'YOUR_NAME': self.user_info['your_name'],
            'YOUR_EMAIL': self.user_info['your_email'],
            'YOUR_LINKEDIN': self.user_info['your_linkedin'],
        }

        # Add individual skill replacements
        skills = self.user_info['your_skills']
        for i in range(3):
            skill_key = f'SKILL_{i+1}'
            replacements[skill_key] = skills[i] if i < len(skills) else f'Key skill {i+1}'

        # Perform replacements
        for key, value in replacements.items():
            subject_line = subject_line.replace(f'{{{key}}}', str(value))
            body = body.replace(f'{{{key}}}', str(value))
            body = body.replace(f'[{key}]', str(value))

        return subject_line, body

    def get_initial_email(self, recipient: Dict, job_info: Dict) -> tuple:
        """
        Get personalized initial email.

        Args:
            recipient: Recipient information
            job_info: Job information

        Returns:
            Tuple of (subject, body)
        """
        template = self.load_template('initial_email.txt')
        return self.personalize_email(template, recipient, job_info)

    def get_followup_email(self, recipient: Dict, job_info: Dict) -> tuple:
        """
        Get personalized follow-up email.

        Args:
            recipient: Recipient information
            job_info: Job information

        Returns:
            Tuple of (subject, body)
        """
        template = self.load_template('followup_email.txt')
        return self.personalize_email(template, recipient, job_info)

    def preview_email(self, template_type: str, recipient: Dict, job_info: Dict) -> str:
        """
        Preview an email without sending.

        Args:
            template_type: 'initial' or 'followup'
            recipient: Recipient information
            job_info: Job information

        Returns:
            Formatted email preview
        """
        if template_type == 'initial':
            subject, body = self.get_initial_email(recipient, job_info)
        else:
            subject, body = self.get_followup_email(recipient, job_info)

        preview = f"To: {recipient.get('email', 'N/A')}\n"
        preview += f"Subject: {subject}\n"
        preview += f"\n{'-' * 60}\n\n"
        preview += body

        return preview
