# OAuth Callback Session Fix

## Problem
After Gmail OAuth authentication, users were redirected back to Step 1 of onboarding instead of proceeding to the next step. This happened because:

1. OAuth callback caused a full page reload
2. Session state (`st.session_state.user_configured`) was lost
3. User had to re-enter their profile information

## Solution
Store onboarding progress in the **database** instead of session state.

## Changes Made

### 1. Database Schema Updates
Added new columns to `users` table:
- `profile_completed` (Boolean) - Tracks if user completed profile setup
- `profile_name` (String) - User's full name
- `profile_email` (String) - User's contact email
- `profile_linkedin` (String) - User's LinkedIn URL

### 2. Database Methods
**src/database.py:**
- Added `save_user_profile(user_id, name, email, linkedin)` - Saves profile and marks as completed
- Added `get_user_profile(user_id)` - Retrieves profile information
- Updated `get_user_by_email()` and `get_user_by_username()` to include new profile fields

### 3. Onboarding Flow Updates
**src/onboarding.py:**
- `show_onboarding_screen()`: Now checks `user['profile_completed']` from database instead of session state
- Saves profile to database using `db.save_user_profile()`
- Refreshes user data from database after saving
- `check_onboarding_status()`: Loads profile from database into template manager on every check

### 4. App Initialization
**app.py:**
- Loads user profile from database when initializing template manager
- Sets `st.session_state.user_configured = True` if profile exists in database
- Profile data persists across page reloads and OAuth callbacks

### 5. Migration Script
**migrate_profile_fields.py:**
- Adds new profile columns to existing database
- Safe to run multiple times (checks if columns exist)

## How It Works Now

### OAuth Flow:
1. User completes Step 1 (Profile) → **Saved to database** ✅
2. User clicks "Connect Gmail" → Redirected to Google
3. Google redirects back with OAuth callback
4. OAuth handler restores user session from state parameter
5. App loads user from database → `profile_completed = True` ✅
6. Onboarding checks database → Profile complete! → **Shows Step 2 (Gmail)** ✅
7. After Gmail auth → **Shows Step 3 (Apollo)** ✅
8. Onboarding complete → **Dashboard** ✅

### Key Improvements:
✅ Profile data persists across sessions
✅ OAuth callbacks don't reset onboarding progress
✅ Users never lose their configuration
✅ Works correctly with browser refresh
✅ Database is single source of truth

## Testing

### Test Scenario 1: New User
1. Create new account
2. Complete profile setup (Step 1)
3. Connect Gmail (Step 2)
4. Should land on Step 3 (Apollo), not back to Step 1 ✅

### Test Scenario 2: Existing User
1. Login with existing account
2. Should skip onboarding entirely if profile complete ✅
3. Should see dashboard immediately ✅

### Test Scenario 3: Browser Refresh
1. Complete Step 1
2. Refresh browser
3. Should still show Step 2, not Step 1 ✅

## Migration Required

Run this command to update existing database:
```bash
python migrate_profile_fields.py
```

This adds the new profile columns to the users table.
