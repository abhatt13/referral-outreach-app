"""Resume parser to extract user information."""

import re
from typing import Dict, List, Optional
import PyPDF2
import io

class ResumeParser:
    """Parser for extracting information from resumes."""

    def __init__(self):
        """Initialize resume parser."""
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        self.phone_pattern = r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        self.linkedin_pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+'

    def parse_pdf(self, file_content: bytes) -> Dict:
        """
        Parse PDF resume.

        Args:
            file_content: PDF file content as bytes

        Returns:
            Dictionary with extracted information
        """
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()

            return self._extract_info(text)
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return {}

    def parse_text(self, text: str) -> Dict:
        """
        Parse text resume.

        Args:
            text: Resume text

        Returns:
            Dictionary with extracted information
        """
        return self._extract_info(text)

    def _extract_info(self, text: str) -> Dict:
        """Extract information from resume text."""
        result = {
            'name': self._extract_name(text),
            'email': self._extract_email(text),
            'phone': self._extract_phone(text),
            'linkedin': self._extract_linkedin(text),
            'skills': self._extract_skills(text),
            'experience': self._extract_experience(text),
            'education': self._extract_education(text),
            'summary': self._extract_summary(text),
            'raw_text': text
        }

        return result

    def _extract_name(self, text: str) -> Optional[str]:
        """Extract name from resume (usually first line)."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        if lines:
            # First non-empty line is usually the name
            first_line = lines[0]
            # Remove common prefixes
            first_line = re.sub(r'^(Resume|CV|Curriculum Vitae)[\s:-]*', '', first_line, flags=re.IGNORECASE)

            # Check if it looks like a name (2-4 words, mostly capital letters)
            words = first_line.split()
            if 1 <= len(words) <= 4 and not '@' in first_line and not 'http' in first_line.lower():
                return first_line.strip()

        return None

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email from resume."""
        matches = re.findall(self.email_pattern, text)
        if matches:
            return matches[0]
        return None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from resume."""
        matches = re.findall(self.phone_pattern, text)
        if matches:
            phone = ''.join(matches[0]) if isinstance(matches[0], tuple) else matches[0]
            return phone.strip()
        return None

    def _extract_linkedin(self, text: str) -> Optional[str]:
        """Extract LinkedIn URL from resume."""
        matches = re.findall(self.linkedin_pattern, text, re.IGNORECASE)
        if matches:
            url = matches[0]
            if not url.startswith('http'):
                url = 'https://' + url
            return url
        return None

    def _extract_skills(self, text: str) -> List[str]:
        """Extract key technical skills from resume."""
        skills = []

        # Look for skills section
        skills_section = re.search(
            r'(?:SKILLS|TECHNICAL SKILLS|CORE COMPETENCIES|TECHNOLOGIES)[\s:-]*(.*?)(?:\n\n|\n[A-Z][A-Z\s]+\n)',
            text,
            re.IGNORECASE | re.DOTALL
        )

        if skills_section:
            skills_text = skills_section.group(1)
            # Clean up the text
            skills_text = re.sub(r'\s+', ' ', skills_text)

            # Look for structured lists (e.g., "Languages: Python, Java")
            categories = re.findall(r'([A-Za-z\s/]+?)[:—-]\s*([^\n]+)', skills_text)

            for category, items in categories:
                # Split items by commas, semicolons, or pipes
                skill_items = re.split(r'[,;|]', items)
                for item in skill_items:
                    item = item.strip()
                    # Only add substantial skills (not single letters/numbers)
                    if len(item) > 2 and not item.isdigit():
                        skills.append(item)

        # Remove duplicates while preserving order
        seen = set()
        skills = [s for s in skills if not (s.lower() in seen or seen.add(s.lower()))]

        return skills[:10]  # Return top 10 skills

    def _extract_experience(self, text: str) -> List[str]:
        """Extract complete work experience bullet points."""
        experiences = []

        # Look for experience section
        exp_section = re.search(
            r'(?:EXPERIENCE|WORK EXPERIENCE|PROFESSIONAL EXPERIENCE)[\s:-]*(.*?)(?:EDUCATION|SKILLS|PROJECTS|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )

        if exp_section:
            exp_text = exp_section.group(1)

            # Split by bullet markers
            bullets = re.split(r'\n\s*[•·∙○▪●]\s*', exp_text)

            for bullet in bullets:
                if not bullet.strip():
                    continue

                # Clean the bullet text
                lines = []
                for line in bullet.split('\n'):
                    line = line.strip()
                    # Skip if empty
                    if not line:
                        break
                    # Skip if it's a header (company name, title, dates)
                    if re.match(r'^[A-Z][A-Z\s]+$', line):  # All caps header
                        break
                    if re.search(r'\d{4}\s*[-–—]\s*(\d{4}|Present|Current)', line, re.IGNORECASE):  # Date range
                        break
                    # Check if it's likely a job title (capitalized, short)
                    if re.match(r'^[A-Z][a-z\s,&]+(\||at|@)', line) and len(line) < 60:
                        break

                    lines.append(line)

                if lines:
                    # Join multi-line bullet into complete sentence
                    complete_bullet = ' '.join(lines)
                    # Clean up whitespace
                    complete_bullet = re.sub(r'\s+', ' ', complete_bullet).strip()

                    # Ensure it's substantial (minimum 60 chars to avoid incomplete sentences)
                    if len(complete_bullet) >= 60:
                        # Ensure proper capitalization
                        if complete_bullet and complete_bullet[0].islower():
                            complete_bullet = complete_bullet[0].upper() + complete_bullet[1:]

                        experiences.append(complete_bullet)

                        if len(experiences) >= 5:
                            break

        return experiences

    def _extract_education(self, text: str) -> Optional[str]:
        """Extract education information."""
        edu_section = re.search(
            r'(?:EDUCATION)[\s:-]*(.*?)(?:\n\n[A-Z][A-Z\s]+\n|$)',
            text,
            re.IGNORECASE | re.DOTALL
        )

        if edu_section:
            edu_text = edu_section.group(1).strip()
            # Get first meaningful line (degree and university)
            lines = [l.strip() for l in edu_text.split('\n') if l.strip()]
            for line in lines:
                # Skip date lines
                if re.search(r'\d{4}', line) and len(line) < 20:
                    continue
                if len(line) > 10:
                    return line

        return None

    def _extract_summary(self, text: str) -> Optional[str]:
        """Extract professional summary."""
        summary_section = re.search(
            r'(?:SUMMARY|PROFESSIONAL SUMMARY|PROFILE|OBJECTIVE|ABOUT)[\s:-]*(.*?)(?:\n\n[A-Z][A-Z\s]+\n|EXPERIENCE|EDUCATION)',
            text,
            re.IGNORECASE | re.DOTALL
        )

        if summary_section:
            summary = summary_section.group(1).strip()
            # Clean up and take first 2 sentences
            summary = re.sub(r'\s+', ' ', summary)
            sentences = re.split(r'[.!?]\s+', summary)
            return '. '.join(sentences[:2]) + '.' if sentences else None

        return None

    def match_to_job(self, parsed_data: Dict, job_description: str) -> List[str]:
        """
        Match resume experience to job description and return most relevant bullets.

        Args:
            parsed_data: Parsed resume data
            job_description: Job description text

        Returns:
            List of 3 most relevant experience bullets
        """
        experiences = parsed_data.get('experience', [])
        skills = parsed_data.get('skills', [])

        if not experiences:
            return self._generate_default_bullets(skills)

        # Extract keywords from job description
        job_keywords = self._extract_job_keywords(job_description)

        # Score each experience based on keyword matches
        scored_experiences = []
        for exp in experiences:
            score = 0
            exp_lower = exp.lower()

            # Count keyword matches
            for keyword in job_keywords:
                if keyword.lower() in exp_lower:
                    score += 1

            scored_experiences.append((score, exp))

        # Sort by score (highest first)
        scored_experiences.sort(reverse=True, key=lambda x: x[0])

        # Take top 3 most relevant
        top_experiences = [exp for score, exp in scored_experiences[:3]]

        # If we don't have 3, fill with skill-based bullets
        if len(top_experiences) < 3 and skills:
            # Create skill-based bullets
            skill_groups = []
            if len(skills) >= 3:
                skill_groups.append(f"Proficient in {skills[0]}, {skills[1]}, and {skills[2]}")
            elif len(skills) == 2:
                skill_groups.append(f"Proficient in {skills[0]} and {skills[1]}")
            elif len(skills) == 1:
                skill_groups.append(f"Proficient in {skills[0]}")

            for skill_bullet in skill_groups:
                if len(top_experiences) < 3:
                    top_experiences.append(skill_bullet)

        # Fill remaining with generic bullets if still not enough
        generic_bullets = [
            "Strong analytical and problem-solving skills with attention to detail",
            "Proven ability to work effectively in team environments and deliver results",
            "Quick learner with passion for adopting new technologies and methodologies"
        ]

        for generic in generic_bullets:
            if len(top_experiences) >= 3:
                break
            if generic not in top_experiences:
                top_experiences.append(generic)

        return top_experiences[:3]

    def _extract_job_keywords(self, job_description: str) -> List[str]:
        """Extract key technical terms from job description."""
        # Common tech keywords and frameworks
        tech_keywords = [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'React', 'Node.js', 'Angular', 'Vue',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'SQL', 'NoSQL', 'MongoDB', 'PostgreSQL',
            'Machine Learning', 'AI', 'Data Science', 'Analytics', 'Big Data', 'Spark', 'Hadoop',
            'DevOps', 'CI/CD', 'Agile', 'Scrum', 'REST', 'GraphQL', 'Microservices',
            'TensorFlow', 'PyTorch', 'Pandas', 'NumPy', 'Scikit-learn',
            'Git', 'Jenkins', 'Terraform', 'Ansible', 'ETL', 'API', 'Cloud',
            'Databricks', 'PySpark', 'Data Engineering', 'Data Pipeline'
        ]

        found_keywords = []
        job_lower = job_description.lower()

        for keyword in tech_keywords:
            if keyword.lower() in job_lower:
                found_keywords.append(keyword)

        return found_keywords

    def _generate_default_bullets(self, skills: List[str]) -> List[str]:
        """Generate default bullets if experience extraction fails."""
        bullets = []

        if skills:
            # Group skills into categories
            prog_langs = [s for s in skills if any(lang in s.lower() for lang in ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'go'])]
            frameworks = [s for s in skills if any(fw in s.lower() for fw in ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'node'])]
            cloud_tools = [s for s in skills if any(ct in s.lower() for ct in ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'cloud'])]

            if prog_langs:
                bullets.append(f"Proficient in {', '.join(prog_langs[:3])}")
            if frameworks:
                bullets.append(f"Experience with {', '.join(frameworks[:3])}")
            if cloud_tools:
                bullets.append(f"Skilled in cloud technologies including {', '.join(cloud_tools[:2])}")

        # Fill remaining slots with generic bullets
        while len(bullets) < 3:
            default_bullets = [
                "Strong technical background with proven problem-solving abilities",
                "Experience delivering high-quality software solutions",
                "Passionate about learning new technologies and best practices"
            ]
            bullets.append(default_bullets[len(bullets)])

        return bullets[:3]

    def format_for_email(self, parsed_data: Dict, job_description: str = '') -> Dict:
        """
        Format parsed resume data for email templates.

        Args:
            parsed_data: Parsed resume data
            job_description: Optional job description to match against

        Returns:
            Dictionary formatted for email template
        """
        # Get relevant experience bullets based on job description
        if job_description:
            bullets = self.match_to_job(parsed_data, job_description)
        else:
            bullets = parsed_data.get('experience', [])[:3]
            if len(bullets) < 3:
                bullets = self._generate_default_bullets(parsed_data.get('skills', []))

        return {
            'your_name': parsed_data.get('name') or 'Your Name',
            'your_email': parsed_data.get('email') or 'your.email@example.com',
            'your_linkedin': parsed_data.get('linkedin') or 'https://www.linkedin.com/in/aakashpadmanabhbhatt/',
            'your_skills': bullets[:3]
        }
