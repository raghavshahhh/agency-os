#!/usr/bin/env python3
"""Test all Agency OS features"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "engine"))

print("=" * 60)
print("🧪 AGENCY OS - Full System Test")
print("=" * 60)

# Test 1: Config
print("\n1️⃣ Testing Config...")
try:
    from config import DATA_DIR, RESEND_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
    print(f"   ✅ DATA_DIR: {DATA_DIR}")
    print(f"   ✅ RESEND_API_KEY: {'Set' if RESEND_API_KEY else 'Missing'}")
    print(f"   ✅ TELEGRAM_BOT_TOKEN: {'Set' if TELEGRAM_BOT_TOKEN else 'Missing'}")
    print(f"   ✅ TELEGRAM_CHAT_ID: {TELEGRAM_CHAT_ID}")
except Exception as e:
    print(f"   ❌ Config Error: {e}")

# Test 2: Outreach Engine
print("\n2️⃣ Testing Outreach Engine...")
try:
    from outreach_engine import generate_cold_email, validate_email_format, get_outreach_stats
    test_lead = {
        "name": "Test",
        "title": "[Hiring] Need AI chatbot",
        "requirement": "Looking for WhatsApp chatbot",
        "platform": "r/forhire"
    }
    email = generate_cold_email(test_lead)
    print(f"   ✅ Email generation: {'Working' if email else 'Failed'}")
    print(f"   ✅ Email validation: {validate_email_format('test@example.com')}")
    stats = get_outreach_stats()
    print(f"   ✅ Outreach stats: {stats}")
except Exception as e:
    print(f"   ❌ Outreach Error: {e}")

# Test 3: Lead Scraper
print("\n3️⃣ Testing Lead Scraper...")
try:
    from lead_scraper import is_hiring_post, score_lead

    # Test [FOR HIRE] rejection
    for_hire = is_hiring_post("[FOR HIRE] Developer available", "I am available for work")
    print(f"   ✅ [FOR HIRE] rejected: {not for_hire}")

    # Test [HIRING] acceptance
    hiring = is_hiring_post("[HIRING] Need developer", "We need someone to build")
    print(f"   ✅ [HIRING] accepted: {hiring}")

    # Test scoring
    score = score_lead("Need AI chatbot", "Looking for developer")
    print(f"   ✅ Lead scoring: {score} points")
except Exception as e:
    print(f"   ❌ Scraper Error: {e}")

# Test 4: Data Files
print("\n4️⃣ Testing Data Files...")
try:
    import json
    leads_file = DATA_DIR / "leads.json"
    revenue_file = DATA_DIR / "revenue.json"

    if leads_file.exists():
        with open(leads_file) as f:
            leads = json.load(f)
        print(f"   ✅ Leads: {len(leads)} records")
    else:
        print("   ⚠️  leads.json not found")

    if revenue_file.exists():
        with open(revenue_file) as f:
            revenue = json.load(f)
        print(f"   ✅ Revenue: {len(revenue.get('entries', []))} entries")
    else:
        print("   ⚠️  revenue.json not found")
except Exception as e:
    print(f"   ❌ Data Error: {e}")

# Test 5: Pages
print("\n5️⃣ Testing Pages...")
pages_dir = Path(__file__).parent / "pages"
expected_pages = ["1_Daily_Ops.py", "2_Leads.py", "3_Content.py", "4_Pipeline.py",
                  "5_Analytics.py", "6_AI_Assistant.py", "7_Revenue.py", "8_Clients.py", "9_Settings.py"]
for page in expected_pages:
    if (pages_dir / page).exists():
        print(f"   ✅ {page}")
    else:
        print(f"   ⚠️  {page} missing")

# Test 6: Engine Files
print("\n6️⃣ Testing Engine...")
engine_dir = Path(__file__).parent / "engine"
expected = ["config.py", "lead_scraper.py", "outreach_engine.py", "content_engine.py",
            "linkedin_scraper.py", "n8n_connector.py"]
for file in expected:
    if (engine_dir / file).exists():
        print(f"   ✅ {file}")
    else:
        print(f"   ⚠️  {file} missing")

print("\n" + "=" * 60)
print("✅ Test Complete!")
print("=" * 60)
print("\n🚀 Ready to start:")
print("   streamlit run app.py")
