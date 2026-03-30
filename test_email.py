#!/usr/bin/env python3
"""Test email sending via Resend"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "engine"))

from outreach_engine import send_email_resend, validate_email_format
from config import RESEND_API_KEY

print("=" * 50)
print("📧 Email Sending Test")
print("=" * 50)

# Check API key
if not RESEND_API_KEY:
    print("❌ RESEND_API_KEY not set in .env")
    print("   Get from: https://resend.com/api-keys")
    sys.exit(1)

print(f"✅ RESEND_API_KEY: {RESEND_API_KEY[:8]}...")

# Test email validation
test_emails = ["ragsproai@gmail.com", "invalid@email", "test@example.com"]
print("\n📧 Email Validation Tests:")
for email in test_emails:
    is_valid = validate_email_format(email)
    print(f"   {email}: {'✅ Valid' if is_valid else '❌ Invalid'}")

# Send test email (to yourself)
print("\n📤 Sending test email to ragsproai@gmail.com...")
result = send_email_resend(
    to_email="ragsproai@gmail.com",
    subject="🧪 Agency OS Email Test",
    body="""Hi Raghav,

This is a test email from your Agency OS dashboard.

If you're reading this, email sending is working! ✅

Best regards,
RAGSPRO Automation
"""
)

if result.get("success"):
    print(f"✅ Email sent successfully!")
    print(f"   Resend ID: {result.get('resend_id')}")
else:
    print(f"❌ Failed to send email")
    print(f"   Error: {result.get('error')}")

print("\n" + "=" * 50)
