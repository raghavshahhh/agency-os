#!/usr/bin/env python3
"""Test Telegram bot"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "engine"))

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

print("=" * 50)
print("📱 Telegram Bot Test")
print("=" * 50)
print(f"Bot Token: {TELEGRAM_BOT_TOKEN[:15]}...")
print(f"Chat ID: {TELEGRAM_CHAT_ID}")

if not TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in ["", "MANUAL_STEP_REQUIRED"]:
    print("\n❌ Missing configuration!")
    sys.exit(1)

import requests

message = """🚀 <b>RAGSPRO Agency OS</b>

✅ Bot is working!

Your automation is ready.
"""

try:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    response = requests.post(url, json=payload, timeout=10)

    if response.status_code == 200:
        print("\n✅ Message sent successfully!")
        print("Check your Telegram.")
    else:
        print(f"\n❌ Failed: {response.text}")
except Exception as e:
    print(f"\n❌ Error: {e}")
