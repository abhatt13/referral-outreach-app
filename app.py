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

# Handle OAuth callback first (before any other UI)
from gmail_oauth_handler import handle_gmail_oauth_callback
handle_gmail_oauth_callback()

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

# Load user's profile and custom templates if they exist
if 'user' in st.session_state and st.session_state.user:
    user = st.session_state.user

    # Load user profile into template manager
    if user.get('profile_completed') and user.get('profile_name'):
        st.session_state.template_manager.set_user_info(
            name=user['profile_name'],
            email=user['profile_email'],
            linkedin=user['profile_linkedin'],
            skills=[]
        )
        st.session_state.user_configured = True

    # Load custom templates
    custom_templates = st.session_state.db.get_custom_templates(user['id'])
    if custom_templates:
        st.session_state.template_manager.set_custom_templates(
            initial_template=custom_templates['initial'],
            followup_template=custom_templates['followup'],
            use_custom=custom_templates['use_custom']
        )

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

# Check if user needs onboarding
from onboarding import check_onboarding_status
if not check_onboarding_status():
    st.stop()

# Display user info in sidebar
display_user_info_sidebar()

# Display Gmail authentication UI in sidebar
gmail_authentication_ui()

# Sidebar for quick settings
with st.sidebar:
    st.markdown("---")
    st.header("⚙️ Settings")

    # Quick profile edit
    with st.expander("✏️ Edit Profile"):
        user_info = st.session_state.template_manager.user_info

        edit_name = st.text_input("Name", value=user_info.get('your_name', ''))
        edit_email = st.text_input("Email", value=user_info.get('your_email', ''))
        edit_linkedin = st.text_input("LinkedIn", value=user_info.get('your_linkedin', ''))

        if st.button("Update Profile"):
            st.session_state.template_manager.set_user_info(
                name=edit_name,
                email=edit_email,
                linkedin=edit_linkedin,
                skills=[]
            )
            st.success("✅ Profile updated!")
            st.rerun()

    # API Configuration
    with st.expander("🔑 Apollo.io API Key"):
        # Show status instead of the actual key
        current_key = os.getenv('APOLLO_API_KEY', '')
        if current_key:
            st.info(f"✅ API Key configured (ends with: ...{current_key[-4:]})")
        else:
            st.warning("⚠️ No API key configured")

        apollo_key = st.text_input("Enter New API Key", type="password",
                                   placeholder="Paste your Apollo.io API key here")

        if st.button("Save API Key"):
            if apollo_key:
                os.environ['APOLLO_API_KEY'] = apollo_key
                st.session_state.apollo_configured = True
                st.success("✅ API key saved!")
                st.rerun()

    # Scheduler Status
    st.markdown("---")
    st.subheader("⏰ Scheduler")
    if st.session_state.scheduler and st.session_state.scheduler.is_running():
        st.success("✅ Running")
        if st.button("Stop", use_container_width=True):
            st.session_state.scheduler.stop()
            st.rerun()
    else:
        st.warning("⏸️ Stopped")
        if st.button("Start", use_container_width=True):
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
tab1, tab2, tab3, tab4 = st.tabs(["📝 New Campaign", "📊 Referral Sent", "✉️ Email Templates", "📚 History"])

with tab1:
    st.markdown("### 🎯 Create New Campaign")
    st.markdown("Find and contact people at your target company")
    st.markdown("---")

    # Check if user has configured their info
    if not st.session_state.user_configured:
        st.warning("⚠️ Please complete your profile setup first!")
        st.stop()

    # Modern card-style layout
    with st.container():
        col1, col2 = st.columns([3, 2])

        with col1:
            st.markdown("#### 📋 Job Details")

            # Simplified input - just company and title
            company = st.text_input(
                "Company Name",
                placeholder="e.g., Google, Microsoft, Amazon...",
                help="Enter the exact company name as it appears on LinkedIn"
            )

            job_title = st.text_input(
                "Target Job Title",
                placeholder="e.g., Software Engineer, Data Scientist...",
                help="We'll search for people with this title and related senior positions"
            )

            num_contacts = st.slider(
                "Number of people to contact",
                min_value=3,
                max_value=20,
                value=5,
                help="How many people at this company would you like to reach out to?"
            )

            if company and job_title:
                st.session_state.parsed_job = {
                    'company': company,
                    'job_title': job_title,
                    'description': ''
                }

        with col2:
            st.markdown("#### 💡 Tips")
            st.info("""
            **For best results:**

            ✅ Use the exact company name

            ✅ Target specific job titles

            ✅ We'll automatically find people with matching and senior roles

            ⏰ Follow-ups sent automatically after 1 day
            """)

    # Search button
    if 'parsed_job' in st.session_state:
        st.markdown("---")
        final_company = st.session_state.parsed_job.get('company', '')
        final_title = st.session_state.parsed_job.get('job_title', '')

        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            if st.button("🔍 Find People & Preview Emails", type="primary", use_container_width=True):
                if final_company and final_title:
                    with st.spinner("Searching for people at " + final_company + "..."):
                        try:
                            from apollo_client import generate_job_title_variations
                            apollo = ApolloClient()

                            # Generate smart job title variations
                            job_titles = generate_job_title_variations(final_title)
                            st.info(f"Searching for: {', '.join(job_titles[:5])}{'...' if len(job_titles) > 5 else ''}")

                            people = apollo.search_people(final_company, titles=job_titles, limit=num_contacts)

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
    st.header("Referral Sent")

    # Get campaign stats for current user only
    user = st.session_state.user
    session = st.session_state.db.get_session()
    try:
        from database import EmailCampaign, EmailLog

        campaigns = session.query(EmailCampaign).filter_by(user_id=user['id']).order_by(EmailCampaign.created_at.desc()).all()

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

    # Get user and their custom templates
    user = st.session_state.user
    custom_templates = st.session_state.db.get_custom_templates(user['id'])

    # Template mode selector
    st.subheader("Template Mode")
    use_custom = st.radio(
        "Select template mode:",
        ["Use Default Templates", "Use Custom Templates"],
        index=1 if custom_templates and custom_templates['use_custom'] else 0
    )

    use_custom_bool = (use_custom == "Use Custom Templates")

    # Show default templates section
    st.markdown("---")
    st.subheader("📄 Default Templates")

    with st.expander("View Default Initial Email Template", expanded=False):
        with open('templates/initial_email.txt', 'r') as f:
            default_initial = f.read()
        st.code(default_initial, language="text")

    with st.expander("View Default Follow-up Email Template", expanded=False):
        with open('templates/followup_email.txt', 'r') as f:
            default_followup = f.read()
        st.code(default_followup, language="text")

    # Custom templates section
    st.markdown("---")
    st.subheader("✏️ Custom Templates")
    st.info("Use these placeholders in your templates: {first_name}, {name}, {company}, {job_title}, {recipient_title}, {YOUR_NAME}, {YOUR_EMAIL}, {YOUR_LINKEDIN}")

    # Get existing custom templates
    initial_template_value = ""
    followup_template_value = ""
    if custom_templates:
        initial_template_value = custom_templates['initial'] or ""
        followup_template_value = custom_templates['followup'] or ""

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Custom Initial Email Template**")
        custom_initial = st.text_area(
            "Initial Email Template",
            value=initial_template_value,
            height=300,
            placeholder="Subject: Your subject here\n\nHi {first_name},\n\nYour email body...",
            key="custom_initial_template",
            label_visibility="collapsed"
        )

    with col2:
        st.markdown("**Custom Follow-up Email Template**")
        custom_followup = st.text_area(
            "Follow-up Email Template",
            value=followup_template_value,
            height=300,
            placeholder="Subject: Your follow-up subject here\n\nHi {first_name},\n\nYour follow-up body...",
            key="custom_followup_template",
            label_visibility="collapsed"
        )

    if st.button("💾 Save Custom Templates", type="primary"):
        if custom_initial.strip() or custom_followup.strip():
            success = st.session_state.db.save_custom_templates(
                user['id'],
                initial_template=custom_initial if custom_initial.strip() else None,
                followup_template=custom_followup if custom_followup.strip() else None,
                use_custom=use_custom_bool
            )
            if success:
                # Update template manager
                st.session_state.template_manager.set_custom_templates(
                    initial_template=custom_initial if custom_initial.strip() else None,
                    followup_template=custom_followup if custom_followup.strip() else None,
                    use_custom=use_custom_bool
                )
                st.success("✅ Custom templates saved successfully!")
                st.rerun()
            else:
                st.error("❌ Failed to save templates")
        else:
            st.warning("⚠️ Please enter at least one custom template")

    # Update template manager mode when switching
    if custom_templates and custom_templates['use_custom'] != use_custom_bool:
        st.session_state.db.toggle_custom_templates(user['id'], use_custom_bool)
        st.session_state.template_manager.set_custom_templates(
            initial_template=custom_templates['initial'],
            followup_template=custom_templates['followup'],
            use_custom=use_custom_bool
        )
        st.rerun()

with tab4:
    st.header("Email History")

    # Get current user's emails only
    user = st.session_state.user
    session = st.session_state.db.get_session()
    try:
        from database import EmailLog, Contact, EmailCampaign

        # Filter emails by user's campaigns
        emails = session.query(EmailLog).join(
            EmailCampaign, EmailLog.campaign_id == EmailCampaign.id
        ).filter(
            EmailCampaign.user_id == user['id']
        ).order_by(EmailLog.sent_at.desc()).limit(50).all()

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
