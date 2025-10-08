# Gmail Authentication Setup Guide

## How to Connect Your Gmail Account

When you click "Connect Gmail Account" in the app, you'll need to authorize the app to send emails on your behalf. Follow these steps:

### Step 1: Click "Connect Gmail Account"
In the sidebar, click the blue **"Connect Gmail Account"** button.

### Step 2: Authorize with Google
A link will appear. Click it to open the Google authorization page.

### Step 3: Handle the "Unverified App" Warning

⚠️ **You'll see a warning: "Google hasn't verified this app"**

**This is normal!** Here's how to proceed safely:

1. Click **"Advanced"** at the bottom of the warning
2. Click **"Go to [App Name] (unsafe)"**
3. Review the permissions (the app only needs to send emails, nothing else)
4. Click **"Continue"** or **"Allow"**

### Step 4: Copy the Authorization Code
After authorizing, Google will show you an authorization code.

1. **Copy the entire code**
2. Go back to the app
3. **Paste the code** in the "Paste authorization code here" field
4. Press Enter or click outside the box

### Step 5: You're Done! ✅
You'll see "✅ Gmail Connected" in the sidebar. You can now send referral emails from your own Gmail account!

---

## Why the "Unverified App" Warning?

- The app is **new and hasn't completed Google's verification process** yet
- The app **only requests permission to send emails** (gmail.send scope)
- It **does NOT** read your emails, contacts, or any other data
- Your Gmail password is **never shared** with the app
- You can **revoke access anytime** from your [Google Account Settings](https://myaccount.google.com/permissions)

---

## Troubleshooting

### "Access Denied" Error
Make sure you:
1. Clicked "Advanced" → "Go to [App Name] (unsafe)"
2. Authorized all permissions
3. Copied the ENTIRE authorization code

### "Invalid Grant" Error
The authorization code may have expired. Try again:
1. Click "Connect Gmail Account" again
2. Get a fresh authorization code
3. Paste it immediately

### Need to Disconnect?
Click **"Disconnect Gmail"** in the sidebar anytime. Your emails remain private and secure.

---

## Security & Privacy

✅ **What the app CAN do:**
- Send emails from your Gmail on your behalf
- Only when YOU click "Send Emails"

❌ **What the app CANNOT do:**
- Read your emails
- Access your contacts
- Delete or modify existing emails
- Access any other Google services
- Use your account without your permission

You remain in full control. You can revoke access anytime from [Google Account Permissions](https://myaccount.google.com/permissions).
