#!/usr/bin/env python3
"""
RAGSPRO LinkedIn Outreach - REAL client acquisition
Target: Decision makers who need AI chatbots/SaaS
"""

import json
import re
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data"
OUTREACH_FILE = DATA_DIR / "outreach_targets.json"

# HIGH-INTENT TARGETS - Companies actively hiring or scaling
TARGET_PERSONAS = [
    {
        "title": "Founder",
        "company_size": "11-50",  # Startups with budget
        "keywords": ["AI", "automation", "SaaS", "chatbot", "WhatsApp"],
        "industries": ["Real Estate", "Healthcare", "Education", "Retail", "Logistics"]
    },
    {
        "title": "CEO",
        "company_size": "1-10",  # Early stage, need MVP
        "keywords": ["building", "startup", "platform", "app"],
        "industries": ["E-commerce", "Fintech", "Edtech", "Healthtech"]
    },
    {
        "title": "CTO",
        "company_size": "51-200",  # Growth stage, scaling
        "keywords": ["automation", "AI", "chatbot", "integration"],
        "industries": ["Any"]
    },
    {
        "title": "Head of Operations",
        "company_size": "51-500",
        "keywords": ["efficiency", "automation", "CRM", "customer service"],
        "industries": ["Real Estate", "Healthcare", "Retail", "Logistics"]
    }
]

# REAL COMPANIES - Manually verified
VERIFIED_COMPANIES = [
    {
        "name": "Square Yards",
        "industry": "Real Estate",
        "location": "Gurgaon",
        "size": "500-1000",
        "website": "squareyards.com",
        "linkedin": "linkedin.com/company/square-yards",
        "needs": "Lead qualification chatbot, WhatsApp automation",
        "decision_maker": "CEO/Head of Product",
        "priority": "HIGH"
    },
    {
        "name": "NoBroker",
        "industry": "Real Estate",
        "location": "Bangalore",
        "size": "500-1000",
        "website": "nobroker.in",
        "linkedin": "linkedin.com/company/nobroker",
        "needs": "Customer support automation, rental chatbot",
        "decision_maker": "CTO/VP Engineering",
        "priority": "HIGH"
    },
    {
        "name": "Practo",
        "industry": "Healthcare",
        "location": "Bangalore",
        "size": "1000-5000",
        "website": "practo.com",
        "linkedin": "linkedin.com/company/practo",
        "needs": "Appointment booking bot, patient engagement",
        "decision_maker": "VP Engineering/Product",
        "priority": "MEDIUM"
    },
    {
        "name": "BYJU'S",
        "industry": "Edtech",
        "location": "Bangalore",
        "size": "5000+",
        "website": "byjus.com",
        "linkedin": "linkedin.com/company/byju-s",
        "needs": "Student onboarding, course recommendation AI",
        "decision_maker": "Head of AI/Product",
        "priority": "MEDIUM"
    },
    {
        "name": "Delhivery",
        "industry": "Logistics",
        "location": "Delhi/Gurgaon",
        "size": "5000+",
        "website": "delhivery.com",
        "linkedin": "linkedin.com/company/delhivery",
        "needs": "Tracking automation, customer support bot",
        "decision_maker": "VP Technology",
        "priority": "HIGH"
    },
    {
        "name": "Lenskart",
        "industry": "Retail/E-commerce",
        "location": "Delhi",
        "size": "1000-5000",
        "website": "lenskart.com",
        "linkedin": "linkedin.com/company/lenskart",
        "needs": "Virtual try-on, customer support, WhatsApp",
        "decision_maker": "CTO/Head of Digital",
        "priority": "HIGH"
    },
    {
        "name": "PolicyBazaar",
        "industry": "Fintech/Insurance",
        "location": "Delhi/Gurgaon",
        "size": "1000-5000",
        "website": "policybazaar.com",
        "linkedin": "linkedin.com/company/policybazaar",
        "needs": "Insurance recommendation bot, claims automation",
        "decision_maker": "CTO/VP Product",
        "priority": "MEDIUM"
    },
    {
        "name": "Blinkit (ex-Grofers)",
        "industry": "Quick Commerce",
        "location": "Delhi",
        "size": "1000-5000",
        "website": "blinkit.com",
        "linkedin": "linkedin.com/company/blinkit",
        "needs": "Delivery tracking, customer support",
        "decision_maker": "VP Engineering",
        "priority": "MEDIUM"
    },
    {
        "name": "Zerodha",
        "industry": "Fintech",
        "location": "Bangalore",
        "size": "500-1000",
        "website": "zerodha.com",
        "linkedin": "linkedin.com/company/zerodha",
        "needs": "Customer onboarding, support automation",
        "decision_maker": "CTO/Head of Engineering",
        "priority": "HIGH"
    },
    {
        "name": "Razorpay",
        "industry": "Fintech",
        "location": "Bangalore",
        "size": "1000-5000",
        "website": "razorpay.com",
        "linkedin": "linkedin.com/company/razorpay",
        "needs": "Merchant onboarding, support chatbot",
        "decision_maker": "VP Engineering/Product",
        "priority": "MEDIUM"
    },
    # SME Targets
    {
        "name": "Local Real Estate Agents",
        "industry": "Real Estate",
        "location": "Delhi/Mumbai/Bangalore",
        "size": "1-10",
        "website": "Various",
        "linkedin": "Search: real estate owner + city",
        "needs": "Lead capture, WhatsApp automation, property alerts",
        "decision_maker": "Owner/Founder",
        "priority": "HIGH",
        "note": "Easy to convince, quick decision"
    },
    {
        "name": "Clinics & Diagnostic Centers",
        "industry": "Healthcare",
        "location": "All cities",
        "size": "1-50",
        "website": "JustDial/Practo listings",
        "linkedin": "Search: clinic owner + city",
        "needs": "Appointment booking, reminders, reports",
        "decision_maker": "Doctor/Owner",
        "priority": "HIGH",
        "note": "High pain point, willing to pay"
    },
    {
        "name": "Coaching Institutes",
        "industry": "Education",
        "location": "All cities",
        "size": "10-100",
        "website": "Local listings",
        "linkedin": "Search: institute director + city",
        "needs": "Student queries, fee reminders, course info",
        "decision_maker": "Director/Owner",
        "priority": "HIGH",
        "note": "High volume, need automation"
    }
]

def generate_outreach_message(company):
    """Generate personalized outreach message"""
    templates = {
        "Real Estate": f"""Hi [Name],

Noticed {company['name']} is scaling fast in {company['location']}.

Quick question: Are you losing leads because your team can't respond instantly to property queries?

We built an AI WhatsApp chatbot for a Delhi realtor that:
✅ Captures leads 24/7
✅ Answers property questions automatically
✅ Qualifies serious buyers vs time-wasters
✅ Books site visits without human intervention

Result: 3x more qualified leads, 60% less time on calls.

Worth a 10-min chat this week?

Best,
Raghav
RAGS Pro | AI Automation for Real Estate""",

        "Healthcare": f"""Hi [Name],

Quick question about {company['name']}:

How much time does your staff spend answering "What are your timings?" and "Do you have [specialist] available?"

We built an AI assistant for clinics that:
✅ Handles appointment bookings 24/7
✅ Sends automatic reminders (reduces no-shows by 40%)
✅ Answers FAQs instantly
✅ Integrates with your existing system

One Delhi clinic saved 15 hours/week.

Worth showing you a demo?

Raghav
RAGS Pro | AI for Healthcare""",

        "E-commerce": f"""Hi [Name],

Noticed {company['name']} is growing fast.

Quick question: What's your current response time for "Where's my order?" queries?

We built a WhatsApp automation for e-commerce that:
✅ Answers order tracking instantly
✅ Handles returns/refunds automatically
✅ Upsells relevant products
✅ Reduces support tickets by 70%

Want to see it in action?

Raghav
RAGS Pro | AI for E-commerce""",

        "default": f"""Hi [Name],

Saw {company['name']} and the work you're doing in {company['industry']}.

Quick question: Are repetitive customer queries taking up your team's time?

We help companies like yours automate with AI chatbots that:
✅ Handle 80% of common questions automatically
✅ Work 24/7 on WhatsApp/Website
✅ Integrate with your existing tools
✅ Cost 1/10th of a full-time employee

Any interest in a quick 10-min demo this week?

Raghav
RAGS Pro | AI Automation Solutions"""
    }

    return templates.get(company['industry'], templates['default'])

def generate_linkedin_search_url(company):
    """Generate LinkedIn search URL for decision makers"""
    role = company['decision_maker'].split('/')[0].replace(' ', '%20')
    company_name = company['name'].replace(' ', '%20')
    return f"https://www.linkedin.com/search/results/people/?keywords={role}%20{company_name}&origin=GLOBAL_SEARCH_HEADER"

def save_targets():
    """Save all targets with outreach messages"""
    targets = []
    for company in VERIFIED_COMPANIES:
        target = {
            **company,
            "linkedin_search": generate_linkedin_search_url(company),
            "outreach_message": generate_outreach_message(company),
            "status": "NOT_CONTACTED",
            "added_at": datetime.now().isoformat(),
            "priority_score": 100 if company['priority'] == "HIGH" else 70
        }
        targets.append(target)

    with open(OUTREACH_FILE, 'w') as f:
        json.dump(targets, f, indent=2)

    print(f"✅ Saved {len(targets)} verified targets")
    return targets

def print_action_plan():
    """Print actionable next steps"""
    print("\n" + "="*70)
    print("🎯 RAGSPRO CLIENT ACQUISITION PLAN")
    print("="*70)

    print("\n📋 STEP 1: LinkedIn Outreach (Highest Conversion)")
    print("-" * 50)
    print("1. Get LinkedIn Premium (1 month free trial)")
    print("2. Search each company + decision maker title")
    print("3. Send connection request with note:")
    print("   'Hi [Name], love what you're building at [Company].")
    print("    Would love to connect and learn more!'")
    print("4. After they accept, send the outreach message")
    print("5. Follow up in 3 days if no response")

    print("\n📧 STEP 2: Cold Email (Apollo/Hunter)")
    print("-" * 50)
    print("1. Sign up for Apollo.io (50 free credits)")
    print("2. Search: [Company name] + [Title]")
    print("3. Verify email and send")
    print("4. Track opens/clicks")

    print("\n📱 STEP 3: Direct Outreach (Immediate)")
    print("-" * 50)
    print("1. Real Estate: Search 'real estate broker [city] WhatsApp'")
    print("2. Clinics: Search 'diagnostic center [city] contact'")
    print("3. Call directly: 'Hi, I help clinics automate patient queries...'")

    print("\n💰 PRICING STRATEGY")
    print("-" * 50)
    print("Enterprise (Square Yards, NoBroker): ₹50,000 - ₹2,00,000")
    print("SME (Clinics, Real Estate): ₹15,000 - ₹50,000")
    print("Retainer: ₹5,000/month maintenance")

    print("\n📁 Files saved:")
    print(f"   {OUTREACH_FILE}")
    print("\n" + "="*70)

if __name__ == "__main__":
    print("🚀 Generating verified client targets...")
    save_targets()
    print_action_plan()
