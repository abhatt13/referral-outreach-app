"""Streamlit authentication UI components."""

import streamlit as st
from src.auth import AuthManager, TierLimits
from src.database import Database
from src.payment import PaymentManager


def check_authentication():
    """Check if user is authenticated and return user data."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user = None

    return st.session_state.authenticated


def login_signup_page():
    """Display login/signup page."""
    st.title("🔐 Referral Outreach App")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        login_form()

    with tab2:
        signup_form()


def login_form():
    """Display login form."""
    st.subheader("Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            if not username or not password:
                st.error("Please fill in all fields")
                return

            # Authenticate user
            db = Database()
            user = db.get_user_by_username(username)

            if user and AuthManager.verify_password(password, user['password_hash']):
                # Login successful
                token = AuthManager.create_access_token({'user_id': user['id'], 'username': username})

                st.session_state.authenticated = True
                st.session_state.user = user
                st.session_state.token = token

                # Update last login
                db.update_last_login(user['id'])

                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")


def signup_form():
    """Display signup form."""
    st.subheader("Sign Up")

    with st.form("signup_form"):
        email = st.text_input("Email")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Sign Up")

        if submit:
            if not email or not username or not password:
                st.error("Please fill in all fields")
                return

            if password != confirm_password:
                st.error("Passwords do not match")
                return

            if len(password) < 6:
                st.error("Password must be at least 6 characters")
                return

            # Create user
            db = Database()

            # Check if email or username already exists
            if db.get_user_by_email(email):
                st.error("Email already registered")
                return

            if db.get_user_by_username(username):
                st.error("Username already taken")
                return

            # Hash password and create user
            password_hash = AuthManager.hash_password(password)
            user_id = db.create_user(email, username, password_hash, tier='FREE')

            if user_id:
                st.success("Account created successfully! Please login.")
            else:
                st.error("Error creating account. Please try again.")


def logout():
    """Logout current user."""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.token = None
    st.rerun()


def gmail_authentication_ui(app_url: str = "https://carole-villainous-ineffably.ngrok-free.dev"):
    """Display Gmail authentication UI in sidebar."""
    if not st.session_state.authenticated:
        return

    from src.database import Database
    from src.gmail_oauth_handler import initiate_gmail_oauth

    db = Database()
    user = st.session_state.user

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📧 Gmail Authentication")

    # Check if user has authenticated Gmail
    if user.get('gmail_authenticated'):
        st.sidebar.success("✅ Gmail Connected")
        if st.sidebar.button("Disconnect Gmail"):
            db.revoke_gmail_token(user['id'])
            st.session_state.user = db.get_user_by_username(user['username'])
            st.success("Gmail disconnected successfully!")
            st.rerun()
    else:
        st.sidebar.warning("⚠️ Gmail Not Connected")
        st.sidebar.info("Connect your Gmail to send emails")

        with st.sidebar.expander("ℹ️ How to Connect Gmail"):
            st.markdown("""
            **Quick Setup:**
            1. Click "Connect Gmail Account" below
            2. Authorize on Google's page
            3. **Important:** Click "Advanced" → "Go to App (unsafe)" on the warning
            4. You'll be redirected back automatically

            *The warning is normal - the app only sends emails, nothing else!*
            """)

        if st.sidebar.button("Connect Gmail Account", type="primary"):
            initiate_gmail_oauth(app_url)


def display_user_info_sidebar():
    """Display user info and tier limits in sidebar."""
    if not st.session_state.authenticated:
        return

    user = st.session_state.user
    tier_config = TierLimits.get_tier(user['tier'])

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"### 👤 {user['username']}")
    st.sidebar.markdown(f"**Tier:** {tier_config['name']}")

    # Show usage
    remaining_emails = AuthManager.get_remaining_emails(
        user['tier'],
        user['emails_sent_count']
    )

    st.sidebar.metric(
        "Emails Remaining",
        f"{remaining_emails}/{tier_config['email_send_limit']}"
    )

    # Progress bar
    progress = user['emails_sent_count'] / tier_config['email_send_limit']
    st.sidebar.progress(min(progress, 1.0))

    # Upgrade option for free users
    if user['tier'] == 'FREE':
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🚀 Upgrade to Contributor")
        st.sidebar.markdown(f"**${tier_config['price']}/month**")
        st.sidebar.markdown("- 30 email sends per month")
        st.sidebar.markdown("- 10 campaigns per month")

        if st.sidebar.button("Upgrade Now"):
            show_payment_page()

    # Logout button
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        logout()


def show_payment_page():
    """Display payment/upgrade page."""
    st.session_state.show_payment = True


def handle_payment():
    """Handle payment flow for tier upgrade."""
    if not st.session_state.get('show_payment', False):
        return False

    st.markdown("## 🚀 Upgrade to Contributor Tier")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Free Tier")
        st.markdown("- 3 email sends per month")
        st.markdown("- 1 campaign per month")
        st.markdown("- Basic features")

    with col2:
        st.markdown("### Contributor Tier - $5/month")
        st.markdown("- ✅ 30 email sends per month")
        st.markdown("- ✅ 10 campaigns per month")
        st.markdown("- ✅ All features")

    st.markdown("---")

    # In production, you would create a Stripe checkout session here
    st.info("💳 Payment integration: Connect your Stripe account to enable payments")

    # For demo purposes, show what would happen
    if st.button("Simulate Payment (Demo)"):
        db = Database()
        db.update_user_tier(st.session_state.user['id'], 'CONTRIBUTOR')

        # Refresh user data
        st.session_state.user = db.get_user_by_username(st.session_state.user['username'])
        st.session_state.show_payment = False

        st.success("✅ Upgraded to Contributor tier!")
        st.rerun()

    if st.button("Cancel"):
        st.session_state.show_payment = False
        st.rerun()

    return True
