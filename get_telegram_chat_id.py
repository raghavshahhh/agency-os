#!/usr/bin/env python3
"""Get Telegram Chat ID - Run this after messaging your bot"""

import requests
import json

BOT_TOKEN = "8634839248:AAForsp1IbNxQgP9s7GnM3YMQUiMCNrkKTA"

def get_chat_id():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if not data.get("ok"):
            print(f"❌ API Error: {data}")
            return

        results = data.get("result", [])

        if not results:
            print("⚠️  No messages found!")
            print("\n👉 STEPS TO GET CHAT ID:")
            print("1. Open Telegram app")
            print("2. Search for: @ragspro_bot")
            print("3. Send any message (e.g., 'Hi' or 'Test')")
            print("4. Run this script again")
            print("\n💡 After sending message, run:")
            print("   python3 get_telegram_chat_id.py")
            return

        print("✅ Found messages!\n")

        # Extract unique chats
        chats = {}
        for update in results:
            if "message" in update:
                chat = update["message"].get("chat", {})
                chat_id = chat.get("id")
                chat_type = chat.get("type")
                username = chat.get("username", "N/A")
                first_name = chat.get("first_name", "")

                if chat_id and chat_id not in chats:
                    chats[chat_id] = {
                        "username": username,
                        "first_name": first_name,
                        "type": chat_type
                    }

        if chats:
            print("📱 Your Chat IDs:")
            print("=" * 50)
            for chat_id, info in chats.items():
                print(f"\n🆔 Chat ID: {chat_id}")
                print(f"   Name: {info['first_name']}")
                print(f"   Username: @{info['username']}")
                print(f"   Type: {info['type']}")
                print(f"\n   👉 Add this to your .env file:")
                print(f"   TELEGRAM_CHAT_ID={chat_id}")

            # Save to .env automatically
            env_file = ".env"
            try:
                with open(env_file, "r") as f:
                    content = f.read()

                # Update or add CHAT_ID
                chat_id = list(chats.keys())[0]
                if "TELEGRAM_CHAT_ID=" in content:
                    import re
                    content = re.sub(
                        r"TELEGRAM_CHAT_ID=.*",
                        f"TELEGRAM_CHAT_ID={chat_id}",
                        content
                    )
                else:
                    content += f"\nTELEGRAM_CHAT_ID={chat_id}\n"

                with open(env_file, "w") as f:
                    f.write(content)

                print(f"\n✅ Auto-updated {env_file} with Chat ID: {chat_id}")
            except Exception as e:
                print(f"\n⚠️  Could not auto-update .env: {e}")

        else:
            print("⚠️  No chat info found in messages")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🔍 Checking Telegram Bot Updates...")
    print("=" * 50)
    get_chat_id()
