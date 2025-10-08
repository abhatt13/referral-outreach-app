"""Onboarding and configuration UI for new users."""

import streamlit as st
from database import Database


def show_onboarding_screen():
    """
    Show onboarding configuration screen for new users.
    Returns True if onboarding is complete, False otherwise.
    """
    user = st.session_state.user
    db = st.session_state.db

    # Check if user has already configured their profile (from database)
    if user.get('profile_completed'):
        # Load profile into template manager
        if user.get('profile_name'):
            st.session_state.template_manager.set_user_info(
                name=user['profile_name'],
                email=user['profile_email'],
                linkedin=user['profile_linkedin'],
                skills=[]
            )
            st.session_state.user_configured = True
        return True

    # Center the content with a max width
    st.markdown("""
        <style>
        .main-header {
            text-align: center;
            padding: 2rem 0 1rem 0;
        }
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 3rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-header">Welcome to Referral Outreach! 👋</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Let\'s set up your profile to get started with automated referral requests</p>', unsafe_allow_html=True)

    # Progress indicator
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.progress(0.33)
        st.caption("Step 1 of 3: Basic Information")

    st.markdown("---")

    # Main configuration form
    with st.container():
        col_left, col_center, col_right = st.columns([1, 3, 1])

        with col_center:
            st.markdown("### 📝 Your Information")
            st.markdown("This information will be included in your outreach emails")

            # Get default values from parsed resume if available
            default_name = st.session_state.get('parsed_resume', {}).get('your_name', '')
            default_email = st.session_state.get('parsed_resume', {}).get('your_email', user.get('email', ''))
            default_linkedin = st.session_state.get('parsed_resume', {}).get('your_linkedin', '')

            # Form fields
            with st.form("onboarding_form"):
                your_name = st.text_input(
                    "Full Name *",
                    value=default_name,
                    placeholder="e.g., John Doe",
                    help="Your name as it will appear in email signatures"
                )

                your_email = st.text_input(
                    "Contact Email *",
                    value=default_email,
                    placeholder="e.g., john.doe@example.com",
                    help="The email address recruiters can use to contact you"
                )

                your_linkedin = st.text_input(
                    "LinkedIn URL *",
                    value=default_linkedin,
                    placeholder="e.g., https://www.linkedin.com/in/johndoe/",
                    help="Your LinkedIn profile URL"
                )

                st.markdown("---")

                col_a, col_b, col_c = st.columns([1, 1, 1])
                with col_b:
                    submitted = st.form_submit_button("Continue →", type="primary", use_container_width=True)

                if submitted:
                    # Validate inputs
                    errors = []
                    if not your_name.strip():
                        errors.append("Full Name is required")
                    if not your_email.strip():
                        errors.append("Contact Email is required")
                    if not your_linkedin.strip():
                        errors.append("LinkedIn URL is required")
                    elif not your_linkedin.startswith('http'):
                        errors.append("LinkedIn URL must start with http:// or https://")

                    if errors:
                        for error in errors:
                            st.error(f"❌ {error}")
                    else:
                        # Save configuration to database
                        success = db.save_user_profile(
                            user_id=user['id'],
                            name=your_name,
                            email=your_email,
                            linkedin=your_linkedin
                        )

                        if success:
                            # Update template manager
                            st.session_state.template_manager.set_user_info(
                                name=your_name,
                                email=your_email,
                                linkedin=your_linkedin,
                                skills=[]  # Not used in default template
                            )
                            st.session_state.user_configured = True

                            # Refresh user data from database
                            st.session_state.user = db.get_user_by_username(user['username'])

                            st.success("✅ Profile configured successfully!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to save profile. Please try again.")

            # Optional: Resume upload section
            with st.expander("📄 Optional: Upload Resume (Coming Soon)", expanded=False):
                st.info("Resume parsing feature will auto-fill your information from your PDF resume")
                st.file_uploader("Upload PDF Resume", type=['pdf'], disabled=True)


def show_gmail_onboarding():
    """
    Show Gmail authentication onboarding screen.
    Returns True if Gmail is connected, False otherwise.
    """
    user = st.session_state.user

    if user.get('gmail_authenticated'):
        return True

    # Center the content
    st.markdown('<h1 class="main-header">Connect Your Gmail 📧</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Connect your Gmail account to send personalized referral requests</p>', unsafe_allow_html=True)

    # Progress indicator
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.progress(0.66)
        st.caption("Step 2 of 3: Email Authentication")

    st.markdown("---")

    col_left, col_center, col_right = st.columns([1, 3, 1])

    with col_center:
        st.markdown("### 🔐 Why do we need Gmail access?")
        st.markdown("""
        - ✉️ Send referral requests **from your own Gmail account**
        - 🔒 Your emails appear personal and authentic
        - 📊 Track responses and follow-ups automatically
        - 🚫 We **never** read your existing emails
        """)

        st.markdown("---")

        st.markdown("### 🛡️ Security & Privacy")
        st.info("We only request permission to **send emails** on your behalf. We cannot read, delete, or access your existing emails.")

        st.markdown("---")

        col_a, col_b, col_c = st.columns([1, 2, 1])
        with col_b:
            if st.button("🔗 Connect Gmail Account", type="primary", use_container_width=True):
                from gmail_oauth_handler import initiate_gmail_oauth
                app_url = "https://carole-villainous-ineffably.ngrok-free.dev"
                initiate_gmail_oauth(app_url)

        with col_b:
            if st.button("Skip for Now", use_container_width=True):
                st.warning("⚠️ You won't be able to send emails until you connect Gmail")
                st.session_state.gmail_skipped = True
                return True

    return False


def show_api_onboarding():
    """
    Show Apollo API key onboarding screen.
    Returns True if API is configured, False otherwise.
    """
    import os

    if os.getenv('APOLLO_API_KEY') or st.session_state.get('apollo_configured'):
        return True

    # Center the content
    st.markdown('<h1 class="main-header">Connect Apollo.io 🔍</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Find people at your target companies using Apollo.io</p>', unsafe_allow_html=True)

    # Progress indicator
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.progress(1.0)
        st.caption("Step 3 of 3: Company Search")

    st.markdown("---")

    col_left, col_center, col_right = st.columns([1, 3, 1])

    with col_center:
        st.markdown("### 🎯 What is Apollo.io?")
        st.markdown("""
        Apollo.io helps you find employees at companies you're interested in:
        - 🔎 Search for people by job title and company
        - 📧 Get verified email addresses
        - 💼 Find the right people to ask for referrals
        """)

        st.markdown("---")

        st.markdown("### 🔑 Get Your API Key")
        st.markdown("""
        1. Go to [Apollo.io](https://apollo.io) and sign up for a free account
        2. Navigate to Settings → API
        3. Copy your API key
        4. Paste it below
        """)

        st.markdown("---")

        with st.form("apollo_form"):
            apollo_key = st.text_input(
                "Apollo.io API Key",
                type="password",
                placeholder="Paste your API key here"
            )

            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                submitted = st.form_submit_button("Continue →", type="primary", use_container_width=True)

            if submitted:
                if apollo_key.strip():
                    os.environ['APOLLO_API_KEY'] = apollo_key
                    st.session_state.apollo_configured = True
                    st.success("✅ Apollo.io connected successfully!")
                    st.rerun()
                else:
                    st.error("❌ Please enter a valid API key")

        st.markdown("---")
        st.caption("Don't have an Apollo.io account? You can skip this step and add it later in Settings")


def check_onboarding_status():
    """
    Check if user needs onboarding and show appropriate screen.
    Returns True if onboarding complete, False if still in progress.
    """
    user = st.session_state.user

    # Step 1: Profile configuration (check database)
    if not user.get('profile_completed'):
        show_onboarding_screen()
        return False

    # Ensure profile is loaded into session and template manager
    if not st.session_state.get('user_configured') and user.get('profile_name'):
        st.session_state.template_manager.set_user_info(
            name=user['profile_name'],
            email=user['profile_email'],
            linkedin=user['profile_linkedin'],
            skills=[]
        )
        st.session_state.user_configured = True

    # Step 2: Gmail authentication (check database)
    if not user.get('gmail_authenticated') and not st.session_state.get('gmail_skipped'):
        show_gmail_onboarding()
        return False

    # Step 3: Apollo.io API (optional)
    import os
    if not os.getenv('APOLLO_API_KEY') and not st.session_state.get('apollo_configured'):
        show_api_onboarding()
        return False

    # All steps complete
    return True
