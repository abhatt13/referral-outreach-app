"""Streamlit web application for referral outreach automation."""

import streamlit as st
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import Database
from apollo_client import ApolloClient
from gmail_client import GmailClient
from email_templates import EmailTemplateManager
from job_parser import JobParser
from scheduler import FollowUpScheduler
from resume_parser import ResumeParser
from auth_ui import check_authentication, login_signup_page, display_user_info_sidebar, handle_payment, gmail_authentication_ui
from auth import AuthManager, TierLimits

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Referral Outreach Automation",
    page_icon="📧",
    layout="wide"
)

# Check authentication first
if not check_authentication():
    login_signup_page()
    st.stop()

# Handle payment page if active
if handle_payment():
    st.stop()

# Initialize session state
if 'db' not in st.session_state:
    st.session_state.db = Database()

if 'template_manager' not in st.session_state:
    st.session_state.template_manager = EmailTemplateManager()

if 'job_parser' not in st.session_state:
    st.session_state.job_parser = JobParser()

if 'resume_parser' not in st.session_state:
    st.session_state.resume_parser = ResumeParser()

if 'user_configured' not in st.session_state:
    st.session_state.user_configured = False

if 'resume_uploaded' not in st.session_state:
    st.session_state.resume_uploaded = False

if 'scheduler' not in st.session_state:
    st.session_state.scheduler = None

# Title
st.title("📧 Referral Outreach Automation")
st.markdown("Automate your job referral requests with personalized cold emails")

# Display user info in sidebar
display_user_info_sidebar()

# Display Gmail authentication UI
gmail_authentication_ui()

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    # User Information
    with st.expander("👤 Your Information", expanded=not st.session_state.user_configured):
        st.markdown("**Upload Your Resume** (PDF format)")
        resume_file = st.file_uploader("Resume", type=['pdf'], key="resume_upload")

        if resume_file is not None and not st.session_state.resume_uploaded:
            with st.spinner("Parsing your resume..."):
                file_bytes = resume_file.read()
                parsed_data = st.session_state.resume_parser.parse_pdf(file_bytes)

                if parsed_data:
                    # Store full parsed data for later job matching
                    st.session_state.full_parsed_resume = parsed_data

                    # Format for initial display
                    formatted_data = st.session_state.resume_parser.format_for_email(parsed_data)

                    # Pre-fill the form with parsed data
                    st.session_state.parsed_resume = formatted_data
                    st.session_state.resume_uploaded = True
                    st.success("✅ Resume parsed successfully!")
                    st.rerun()

        # Get values from parsed resume or use defaults
        default_name = st.session_state.get('parsed_resume', {}).get('your_name', 'Your Name')
        default_email = st.session_state.get('parsed_resume', {}).get('your_email', 'your.email@example.com')
        default_linkedin = st.session_state.get('parsed_resume', {}).get('your_linkedin', 'https://www.linkedin.com/in/aakashpadmanabhbhatt/')
        default_skills = st.session_state.get('parsed_resume', {}).get('your_skills', ['X years of experience in...', 'Expertise in...', 'Proven track record of...'])

        your_name = st.text_input("Your Name", value=default_name)
        your_email = st.text_input("Your Email", value=default_email)
        your_linkedin = st.text_input("Your LinkedIn URL", value=default_linkedin)

        st.markdown("**Your Key Skills/Experiences** (3 bullet points)")
        skill1 = st.text_input("Skill 1", value=default_skills[0] if len(default_skills) > 0 else "X years of experience in...")
        skill2 = st.text_input("Skill 2", value=default_skills[1] if len(default_skills) > 1 else "Expertise in...")
        skill3 = st.text_input("Skill 3", value=default_skills[2] if len(default_skills) > 2 else "Proven track record of...")

        if st.button("Save Your Info"):
            st.session_state.template_manager.set_user_info(
                name=your_name,
                email=your_email,
                linkedin=your_linkedin,
                skills=[skill1, skill2, skill3]
            )
            st.session_state.user_configured = True
            st.success("Information saved!")

    # API Configuration
    with st.expander("🔑 API Keys"):
        apollo_key = st.text_input("Apollo.io API Key", type="password",
                                   value=os.getenv('APOLLO_API_KEY', ''))

        if apollo_key:
            os.environ['APOLLO_API_KEY'] = apollo_key

        st.markdown("**Gmail OAuth**")
        st.info("Gmail authentication will be handled automatically when you send emails. Make sure you have `credentials.json` in the project root.")

    # Scheduler Status
    st.header("⏰ Follow-up Scheduler")
    if st.session_state.scheduler and st.session_state.scheduler.is_running():
        st.success("✅ Scheduler Running")
        if st.button("Stop Scheduler"):
            st.session_state.scheduler.stop()
            st.rerun()
    else:
        st.warning("⏸️ Scheduler Stopped")
        if st.button("Start Scheduler"):
            if not st.session_state.scheduler:
                # Initialize scheduler
                try:
                    gmail_client = GmailClient()
                    st.session_state.scheduler = FollowUpScheduler(
                        db=st.session_state.db,
                        gmail_client=gmail_client,
                        template_manager=st.session_state.template_manager,
                        followup_delay_days=1
                    )
                except Exception as e:
                    st.error(f"Error initializing scheduler: {e}")

            if st.session_state.scheduler:
                st.session_state.scheduler.start_background(check_interval_minutes=60)
                st.rerun()

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["📝 New Campaign", "📊 Dashboard", "✉️ Email Templates", "📚 History"])

with tab1:
    st.header("Create New Outreach Campaign")

    # Check if user has configured their info
    if not st.session_state.user_configured:
        st.warning("⚠️ Please upload your resume and save your information in the sidebar before creating a campaign!")
        st.info("👈 Go to the sidebar and upload your resume to get started.")
        st.stop()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Job Information")

        # Input method selection
        input_method = st.radio("How would you like to input job details?",
                               ["Paste Job Description", "Manual Entry"])

        if input_method == "Paste Job Description":
            job_description = st.text_area("Paste Job Description", height=200,
                                          placeholder="Paste the full job description here...")

            if st.button("Parse Job Description"):
                if job_description:
                    parsed = st.session_state.job_parser.parse(job_description)

                    if parsed['company']:
                        st.session_state.parsed_job = parsed
                        st.success(f"✅ Detected Company: {parsed['company']}")
                        if parsed['job_title']:
                            st.success(f"✅ Detected Title: {parsed['job_title']}")
                    else:
                        st.warning("Could not auto-detect company. Please enter manually below.")
                        st.session_state.parsed_job = parsed

        else:  # Manual Entry
            company = st.text_input("Company Name", placeholder="e.g., Google")
            job_title = st.text_input("Job Title", placeholder="e.g., Senior Software Engineer")

            if company and job_title:
                st.session_state.parsed_job = {
                    'company': company,
                    'job_title': job_title,
                    'description': ''
                }

        # Allow editing of parsed data
        if 'parsed_job' in st.session_state:
            st.markdown("---")
            st.subheader("Confirm Details")

            final_company = st.text_input("Company", value=st.session_state.parsed_job.get('company', ''))
            final_title = st.text_input("Job Title", value=st.session_state.parsed_job.get('job_title', ''))

            num_contacts = st.slider("Number of people to contact", min_value=3, max_value=20, value=3)

            if st.button("🔍 Find People & Preview Emails", type="primary"):
                if final_company and final_title:
                    with st.spinner("Searching for people at " + final_company + "..."):
                        try:
                            apollo = ApolloClient()
                            people = apollo.search_people(final_company, limit=num_contacts)

                            if people:
                                # Filter out people without emails
                                people_with_emails = [p for p in people if p.get('email')]
                                people_without_emails = [p for p in people if not p.get('email')]

                                st.session_state.found_people = people_with_emails
                                st.session_state.campaign_info = {
                                    'company': final_company,
                                    'job_title': final_title,
                                    'description': st.session_state.parsed_job.get('description', '')
                                }

                                # Re-match resume to job description for better personalization
                                # Only if user hasn't manually configured their info
                                if 'full_parsed_resume' in st.session_state and st.session_state.campaign_info['description'] and not st.session_state.user_configured:
                                    job_matched_data = st.session_state.resume_parser.format_for_email(
                                        st.session_state.full_parsed_resume,
                                        st.session_state.campaign_info['description']
                                    )
                                    # Update template manager with job-specific skills
                                    st.session_state.template_manager.set_user_info(
                                        name=job_matched_data['your_name'],
                                        email=job_matched_data['your_email'],
                                        linkedin=job_matched_data['your_linkedin'],
                                        skills=job_matched_data['your_skills']
                                    )

                                if people_with_emails:
                                    st.success(f"Found {len(people_with_emails)} people with unlocked emails!")

                                if people_without_emails:
                                    st.warning(f"⚠️ {len(people_without_emails)} contacts found but emails are locked (need Apollo credits to unlock)")
                                    with st.expander("View locked contacts"):
                                        for p in people_without_emails:
                                            st.text(f"• {p['name']} - {p['title']}")

                                if not people_with_emails:
                                    st.error("No contacts with unlocked emails. You need Apollo credits to reveal emails, or try a different company.")
                            else:
                                st.error("No people found. Try a different company name or check your Apollo API key.")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                else:
                    st.error("Please provide both company name and job title")

    with col2:
        st.subheader("Tips")
        st.info("""
        **For best results:**
        - Use the exact company name as it appears on LinkedIn
        - Be specific with job titles
        - The app will find Software Engineers and related roles by default
        - Follow-ups are sent automatically after 1 day
        """)

    # Show found people and email previews
    if 'found_people' in st.session_state:
        st.markdown("---")
        st.subheader("📋 Found Contacts & Email Previews")

        for i, person in enumerate(st.session_state.found_people):
            with st.expander(f"{person['name']} - {person['title']} ({person['email']})"):
                col_a, col_b = st.columns(2)

                with col_a:
                    st.markdown("**Initial Email Preview:**")
                    subject, body = st.session_state.template_manager.get_initial_email(
                        person, st.session_state.campaign_info
                    )
                    st.text_input(f"Subject {i}", value=subject, key=f"subj_init_{i}", disabled=True)
                    st.text_area(f"Body {i}", value=body, height=200, key=f"body_init_{i}", disabled=True)

                with col_b:
                    st.markdown("**Follow-up Email Preview:**")
                    subj_f, body_f = st.session_state.template_manager.get_followup_email(
                        person, st.session_state.campaign_info
                    )
                    st.text_input(f"Subject F {i}", value=subj_f, key=f"subj_f_{i}", disabled=True)
                    st.text_area(f"Body F {i}", value=body_f, height=200, key=f"body_f_{i}", disabled=True)

        st.markdown("---")
        if st.button("🚀 Send All Emails", type="primary"):
            if not st.session_state.user_configured:
                st.error("Please configure your information in the sidebar first!")
            else:
                # Check tier limits
                user = st.session_state.user
                num_emails_to_send = len([p for p in st.session_state.found_people if p.get('email')])

                can_send = AuthManager.check_tier_limit(
                    user['tier'],
                    user['emails_sent_count'] + num_emails_to_send
                )

                if not can_send:
                    tier_config = TierLimits.get_tier(user['tier'])
                    remaining = AuthManager.get_remaining_emails(user['tier'], user['emails_sent_count'])

                    st.error(f"❌ Email limit exceeded! You have {remaining} emails remaining in your {tier_config['name']} tier.")
                    st.info(f"Trying to send {num_emails_to_send} emails, but you only have {remaining} remaining.")

                    if user['tier'] == 'FREE':
                        if st.button("🚀 Upgrade to Contributor Tier"):
                            st.session_state.show_payment = True
                            st.rerun()
                    st.stop()

                # Check if user has authenticated Gmail
                if not user.get('gmail_authenticated'):
                    st.error("❌ Please connect your Gmail account in the sidebar before sending emails!")
                    st.stop()

                with st.spinner("Sending emails..."):
                    try:
                        # Initialize multi-user Gmail client
                        from gmail_client_multi import MultiUserGmailClient
                        gmail = MultiUserGmailClient()

                        # Get user's Gmail token
                        token_data = st.session_state.db.get_gmail_token(user['id'])
                        if not token_data:
                            st.error("❌ Gmail authentication error. Please reconnect your Gmail account.")
                            st.stop()

                        # Authenticate with user's token
                        if not gmail.authenticate_with_token(token_data):
                            st.error("❌ Failed to authenticate Gmail. Please reconnect your Gmail account.")
                            st.stop()

                        # Create campaign (returns campaign_id) with user_id
                        campaign_id = st.session_state.db.create_campaign(
                            job_title=st.session_state.campaign_info['job_title'],
                            company=st.session_state.campaign_info['company'],
                            job_description=st.session_state.campaign_info['description'],
                            user_id=user['id']
                        )

                        sent_count = 0
                        failed_count = 0

                        progress_bar = st.progress(0)
                        status_text = st.empty()

                        for idx, person in enumerate(st.session_state.found_people):
                            # Skip if no email
                            if not person.get('email'):
                                failed_count += 1
                                continue

                            status_text.text(f"Sending to {person['name']}...")

                            # Add contact to database (returns contact_id)
                            contact_id = st.session_state.db.add_contact(
                                name=person['name'],
                                email=person['email'],
                                title=person['title'],
                                company=person['company'],
                                linkedin_url=person.get('linkedin_url')
                            )

                            # Generate and send email
                            subject, body = st.session_state.template_manager.get_initial_email(
                                person, st.session_state.campaign_info
                            )

                            success = gmail.send_email(person['email'], subject, body)

                            # Calculate follow-up time (1 day from now)
                            followup_time = datetime.utcnow() + timedelta(days=1)

                            # Log email
                            st.session_state.db.log_email(
                                campaign_id=campaign_id,
                                contact_id=contact_id,
                                email_type='initial',
                                subject=subject,
                                body=body,
                                is_sent=success,
                                followup_scheduled_at=followup_time if success else None
                            )

                            if success:
                                sent_count += 1
                            else:
                                failed_count += 1

                            progress_bar.progress((idx + 1) / len(st.session_state.found_people))

                        status_text.empty()
                        progress_bar.empty()

                        # Update user's email count
                        st.session_state.db.increment_email_count(user['id'], sent_count)

                        # Update user's campaign count
                        st.session_state.db.increment_campaign_count(user['id'])

                        # Refresh user data
                        st.session_state.user = st.session_state.db.get_user_by_username(user['username'])

                        st.success(f"✅ Campaign completed! Sent: {sent_count}, Failed: {failed_count}")
                        st.info("Follow-up emails will be sent automatically after 1 day. Make sure the scheduler is running!")

                        # Clear session
                        del st.session_state.found_people
                        del st.session_state.campaign_info

                    except Exception as e:
                        st.error(f"Error sending emails: {str(e)}")

with tab2:
    st.header("Campaign Dashboard")

    # Get campaign stats
    session = st.session_state.db.get_session()
    try:
        from database import EmailCampaign, EmailLog

        campaigns = session.query(EmailCampaign).order_by(EmailCampaign.created_at.desc()).all()

        if campaigns:
            for campaign in campaigns:
                with st.expander(f"📌 {campaign.job_title} at {campaign.company} - {campaign.created_at.strftime('%Y-%m-%d')}"):
                    stats = st.session_state.db.get_campaign_stats(campaign.id)

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Initial Emails Sent", stats['total_initial_sent'])
                    col2.metric("Follow-ups Sent", stats['total_followups_sent'])
                    col3.metric("Follow-up Rate",
                               f"{(stats['total_followups_sent'] / max(stats['total_initial_sent'], 1) * 100):.1f}%")
        else:
            st.info("No campaigns yet. Create one in the 'New Campaign' tab!")
    finally:
        session.close()

with tab3:
    st.header("Email Templates")

    st.markdown("You can customize your email templates by editing the files in the `templates/` folder:")
    st.code("templates/initial_email.txt", language="text")
    st.code("templates/followup_email.txt", language="text")

    st.info("Use these placeholders in your templates: {first_name}, {name}, {company}, {job_title}, {recipient_title}")

with tab4:
    st.header("Email History")

    session = st.session_state.db.get_session()
    try:
        from database import EmailLog, Contact, EmailCampaign

        emails = session.query(EmailLog).order_by(EmailLog.sent_at.desc()).limit(50).all()

        if emails:
            for email in emails:
                contact = session.query(Contact).filter_by(id=email.contact_id).first()
                campaign = session.query(EmailCampaign).filter_by(id=email.campaign_id).first()

                status = "✅ Sent" if email.is_sent else "❌ Failed"
                followup_status = "✅" if email.followup_sent else "⏳ Pending" if email.followup_scheduled_at else "N/A"

                st.text(f"{status} | {email.email_type.title()} | {contact.name if contact else 'Unknown'} | "
                       f"{campaign.company if campaign else 'Unknown'} | "
                       f"{email.sent_at.strftime('%Y-%m-%d %H:%M')} | Follow-up: {followup_status}")
        else:
            st.info("No email history yet.")
    finally:
        session.close()

# Footer
st.markdown("---")
st.markdown("💡 **Tip:** Keep the scheduler running to automatically send follow-up emails!")
