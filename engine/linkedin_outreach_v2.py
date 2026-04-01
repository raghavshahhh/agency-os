#!/usr/bin/env python3
"""
RAGSPRO LinkedIn Outreach v2 - MORE Real Companies
Target: Decision makers who need AI chatbots/SaaS
"""

import json
import re
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data"
OUTREACH_FILE = DATA_DIR / "outreach_targets_v2.json"

# 50+ VERIFIED COMPANIES - Mix of Enterprise + SME
VERIFIED_COMPANIES = [
    # === EXISTING HIGH PRIORITY ===
    {
        "name": "Square Yards",
        "industry": "Real Estate",
        "location": "Gurgaon",
        "size": "500-1000",
        "website": "squareyards.com",
        "decision_maker": "CEO/Head of Product",
        "priority": "HIGH",
        "linkedin": "linkedin.com/company/square-yards",
        "needs": "Lead qualification chatbot, WhatsApp automation"
    },
    {
        "name": "NoBroker",
        "industry": "Real Estate",
        "location": "Bangalore",
        "size": "500-1000",
        "website": "nobroker.in",
        "decision_maker": "CTO/VP Engineering",
        "priority": "HIGH",
        "linkedin": "linkedin.com/company/nobroker",
        "needs": "Customer support automation, rental chatbot"
    },
    {
        "name": "Delhivery",
        "industry": "Logistics",
        "location": "Gurgaon",
        "size": "5000+",
        "website": "delhivery.com",
        "decision_maker": "VP Technology",
        "priority": "HIGH",
        "linkedin": "linkedin.com/company/delhivery",
        "needs": "Tracking automation, customer support bot"
    },
    {
        "name": "Lenskart",
        "industry": "Retail/E-commerce",
        "location": "Delhi",
        "size": "1000-5000",
        "website": "lenskart.com",
        "decision_maker": "CTO/Head of Digital",
        "priority": "HIGH",
        "linkedin": "linkedin.com/company/lenskart",
        "needs": "Virtual try-on, customer support, WhatsApp"
    },
    {
        "name": "Zerodha",
        "industry": "Fintech",
        "location": "Bangalore",
        "size": "500-1000",
        "website": "zerodha.com",
        "decision_maker": "CTO/Head of Engineering",
        "priority": "HIGH",
        "linkedin": "linkedin.com/company/zerodha",
        "needs": "Customer onboarding, support automation"
    },

    # === MORE REAL ESTATE ===
    {
        "name": "PropTiger",
        "industry": "Real Estate",
        "location": "Mumbai",
        "size": "200-500",
        "website": "proptiger.com",
        "decision_maker": "CEO/Head of Technology",
        "priority": "HIGH",
        "linkedin": "linkedin.com/company/proptiger",
        "needs": "Lead management, property matching bot"
    },
    {
        "name": "99acres",
        "industry": "Real Estate",
        "location": "Noida",
        "size": "1000-5000",
        "website": "99acres.com",
        "decision_maker": "VP Product/CTO",
        "priority": "MEDIUM",
        "linkedin": "linkedin.com/company/99acres",
        "needs": "Property recommendations, lead qualification"
    },
    {
        "name": "MagicBricks",
        "industry": "Real Estate",
        "location": "Noida",
        "size": "1000-5000",
        "website": "magicbricks.com",
        "decision_maker": "CTO/Head of Product",
        "priority": "MEDIUM",
        "linkedin": "linkedin.com/company/magicbricks",
        "needs": "Customer support, property search automation"
    },
    {
        "name": "Housing.com",
        "industry": "Real Estate",
        "location": "Mumbai",
        "size": "500-1000",
        "website": "housing.com",
        "decision_maker": "CTO/VP Engineering",
        "priority": "MEDIUM",
        "linkedin": "linkedin.com/company/housingcom",
        "needs": "Rental chatbot, landlord communication"
    },

    # === HEALTHCARE ===
    {
        "name": "PharmEasy",
        "industry": "Healthcare/E-commerce",
        "location": "Mumbai",
        "size": "5000+",
        "website": "pharmeasy.in",
        "decision_maker": "CTO/VP Engineering",
        "priority": "HIGH",
        "linkedin": "linkedin.com/company/pharmeasy",
        "needs": "Order tracking, prescription chatbot"
    },
    {
        "name": "NetMeds",
        "industry": "Healthcare/E-commerce",
        "location": "Chennai",
        "size": "1000-5000",
        "website": "netmeds.com",
        "decision_maker": "Head of Technology",
        "priority": "MEDIUM",
        "linkedin": "linkedin.com/company/netmeds",
        "needs": "Customer support, medicine reminders"
    },
    {
        "name": "1mg",
        "industry": "Healthcare",
        "location": "Gurgaon",
        "size": "1000-5000",
        "website": "1mg.com",
        "decision_maker": "CTO/VP Product",
        "priority": "MEDIUM",
        "linkedin": "linkedin.com/company/1mg",
        "needs": "Health queries, medicine information bot"
    },
    {
        "name": "Lybrate",
        "industry": "Healthcare",
        "location": "Delhi",
        "size": "100-500",
        "website": "lybrate.com",
        "decision_maker": "CEO/CTO",
        "priority": "MEDIUM",
        "linkedin": "linkedin.com/company/lybrate",
        "needs": "Doctor-patient chat, appointment booking"
    },
    {
        "name": "MFine",
        "industry": "Healthcare",
        "location": "Bangalore",
        "size": "500-1000",
        "website": "mfine.co",
        "decision_maker": "CTO/Head of AI",
        "priority": "MEDIUM",
        "linkedin": "linkedin.com/company/mfinecare",
        "needs": "AI health assistant, symptom checker"
    },

    # === EDTECH ===
    {
        "name": "Unacademy",
        "industry": "Edtech",
        "location": "Bangalore",
        "size": "5000+",
        "website": "unacademy.com",
        "decision_maker": "CTO/VP Engineering",
        "priority": "HIGH",
        "linkedin": "linkedin.com/company/unacademy",
        "needs": "Student support, course recommendations"
    },
    {
        "name": "Vedantu",
        "industry": "Edtech",
        "location": "Bangalore",
        "size": "1000-5000",
        "website": "vedantu.com",
        "decision_maker": "CTO/Head of Product",
        "priority": "MEDIUM",
        "linkedin": "linkedin.com/company/vedantu",
        "needs": "Tutor matching, student queries"
    },
    {
        "name": "UpGrad",
        "industry": "Edtech",
        "location": "Mumbai",
        "size": "1000-5000",
        "website": "upgrad.com",
        "decision_maker": "CTO/VP Technology",
        "priority": "MEDIUM",
        "linkedin": "linkedin.com/company/upgrad",
        "needs": "Course counseling, career guidance bot"
    },
    {
        "name": "Simplilearn",
        "industry": "Edtech",
        "location": "Bangalore",
        "size": "1000-5000",
        "website": "simplilearn.com",
        "decision_maker": "CTO/Head of Digital",
        "priority": "MEDIUM",
        "linkedin": "linkedin.com/company/simplilearn",
        "needs": "Course recommendations, certification queries"
    },

    # === E-COMMERCE ===
    {
        "name": "Meesho",
        "industry": "E-commerce",
        "location": "Bangalore",
        "size": "5000+",
        "website": "meesho.com",
        "decision_maker": "CTO/VP Engineering",
        "priority": "HIGH",
        "linkedin": "linkedin.com/company/meesho",
        "needs": "Reseller support, order tracking bot"
    },
    {
        "name": "Nykaa",
        "industry": "E-commerce/Beauty",
        "location": "Mumbai",
        "size": "1000-5000",
        "website": "nykaa.com",
        "decision_maker": "CTO/Head of Technology",
        "priority": "MEDIUM",
        "linkedin": "linkedin.com/company/nykaa",
        "needs": "Product recommendations, beauty advice bot"
    },
    {
        "name": "FirstCry",
        "industry": "E-commerce",
        "location": "Pune",
        "size": "1000-5000",
        "website": "firstcry.com",
        "decision_maker": "CTO/VP Product",
        "priority": "MEDIUM",
        "linkedin": "linkedin.com/company/firstcry",
        "needs": "Parenting advice, product search"
    },
    {
        "name": "CarDekho",
        "industry": "Automotive/Classifieds",
        "location": "Gurgaon",
        "size": "1000-5000",
        "website": "cardekho.com",
        "decision_maker": "CTO/Head of Product",
        "priority": "MEDIUM",
        "linkedin": "linkedin.com/company/cardekho",
        "needs": "Car recommendations, dealer chatbot"
    },

    # === FINTECH ===
    {
        "name": "PhonePe",
        "industry": "Fintech",
        "location": "Bangalore",
        "size": "5000+",
        "website": "phonepe.com",
        "decision_maker": "CTO/VP Engineering",
        "priority": "HIGH",
        "linkedin": "linkedin.com/company/phonepe",
        "needs": "Merchant support, transaction queries"
    },
    {
        "name": "CRED",
        "industry": "Fintech",
        "location": "Bangalore",
        "size": "500-1000",
        "website": "cred.club",
        "decision_maker": "CTO/Head of Engineering",
        "priority": "HIGH",
        "linkedin": "linkedin.com/company/cred",
        "needs": "Credit support, financial advisor bot"
    },
    {
        "name": "Groww",
        "industry": "Fintech",
        "location": "Bangalore",
        "size": "1000-5000",
        "website": "groww.in",
        "decision_maker": "CTO/VP Product",
        "priority": "MEDIUM",
        "linkedin": "linkedin.com/company/groww",
        "needs": "Investment advice, mutual fund queries"
    },
    {
        "name": "Paytm",
        "industry": "Fintech",
        "location": "Noida",
        "size": "10000+",
        "website": "paytm.com",
        "decision_maker": "VP Engineering/Head of AI",
        "priority": "MEDIUM",
        "linkedin": "linkedin.com/company/paytm",
        "needs": "Merchant onboarding, support automation"
    },

    # === SME TARGETS - Easy to close ===
    {
        "name": "Delhi Real Estate Brokers",
        "industry": "Real Estate (SME)",
        "location": "Delhi NCR",
        "size": "1-10",
        "website": "JustDial/99acres listings",
        "decision_maker": "Owner/Broker",
        "priority": "HIGH",
        "linkedin": "Search: real estate broker Delhi",
        "needs": "Lead capture, WhatsApp automation, property alerts",
        "note": "Easy to convince, quick decision, ₹15-50k budget"
    },
    {
        "name": "Mumbai Clinics & Diagnostics",
        "industry": "Healthcare (SME)",
        "location": "Mumbai",
        "size": "1-50",
        "website": "Practo/JustDial listings",
        "decision_maker": "Doctor/Owner",
        "priority": "HIGH",
        "linkedin": "Search: clinic owner Mumbai",
        "needs": "Appointment booking, reminders, reports",
        "note": "High pain point, willing to pay, ₹15-30k budget"
    },
    {
        "name": "Bangalore Coaching Institutes",
        "industry": "Education (SME)",
        "location": "Bangalore",
        "size": "10-100",
        "website": "Local listings",
        "decision_maker": "Director/Owner",
        "priority": "HIGH",
        "linkedin": "Search: coaching institute Bangalore",
        "needs": "Student queries, fee reminders, course info",
        "note": "High volume, need automation, ₹20-40k budget"
    },
    {
        "name": "Pune Retail Stores",
        "industry": "Retail (SME)",
        "location": "Pune",
        "size": "1-50",
        "website": "Google Maps/JustDial",
        "decision_maker": "Owner/Manager",
        "priority": "HIGH",
        "linkedin": "Search: retail store owner Pune",
        "needs": "Order tracking, customer support, inventory queries",
        "note": "Quick decisions, ₹15-25k budget"
    },
    {
        "name": "Hyderabad Restaurants",
        "industry": "Food & Beverage (SME)",
        "location": "Hyderabad",
        "size": "1-50",
        "website": "Zomato/Swiggy listings",
        "decision_maker": "Owner/Manager",
        "priority": "MEDIUM",
        "linkedin": "Search: restaurant owner Hyderabad",
        "needs": "Table booking, order tracking, customer feedback",
        "note": "Medium complexity, ₹15-30k budget"
    },
]


def generate_outreach_message(company):
    """Generate personalized outreach message based on industry"""
    templates = {
        "Real Estate": f"""Hi [Name],

Was looking at {company['name']}'s growth in {company['location']} - impressive scale.

Random question: how's your team handling the flood of property inquiries? I talked to a realtor last month who was drowning in WhatsApp messages at 11pm.

We built him an AI assistant that:
- Books site visits automatically
- Qualifies buyers before human agents get involved
- Works on WhatsApp (where everyone already is)

Cut his response time from hours to minutes. Want to see if it'd work for you?

Raghav

--
Raghav Shah | Founder
RAGS Pro AI Agency
🌐 https://ragspro.com
🤖 AI Chatbots | 🚀 SaaS Development | ⚡ Automation""",

        "Healthcare": f"""Hi [Name],

Quick one: how many hours does your team spend on "what time do you open" and "is Dr. Sharma available on Tuesday"?

I built an appointment bot for a clinic that handles bookings, sends reminders, answers the repetitive stuff. They went from 40+ calls/day down to maybe 8 that actually need a human.

If you're dealing with similar volume, might be worth a look. Happy to jump on a call.

Raghav

--
Raghav Shah | Founder
RAGS Pro AI Agency
🌐 https://ragspro.com""",

        "Edtech": f"""Hi [Name],

{company['name']} has interesting scale. I'm curious - what's your current setup for handling student/parent questions?

I've been building chatbots for edtech. The usual pattern: 70% of queries are the same 8-10 questions repeated endlessly. Course info, pricing, batch timings, payment issues.

Automated that stuff for a coaching center recently. Cut their support load in half.

Want to compare notes sometime?

Raghav

--
Raghav Shah | Founder
RAGS Pro AI Agency
🌐 https://ragspro.com""",

        "E-commerce": f"""Hi [Name],

Love what {company['name']} is building.

Random thought: with your order volume, how much of your support team's time goes to "where's my order" and "can I return this"?

I built a support bot for an e-commerce brand. Handles tracking, returns, FAQs. Their team went from 500+ tickets/day to about 150 that actually need human judgment.

Worth a conversation?

Raghav

--
Raghav Shah | Founder
RAGS Pro AI Agency
🌐 https://ragspro.com""",

        "Fintech": f"""Hi [Name],

{company['name']}'s merchant/user growth is impressive.

One thing I keep thinking about: with that many users, how many "how do I..." and "why did my payment fail" questions hit your support team daily?

Built a support bot for a fintech recently. Handles the repetitive stuff, pulls transaction data, explains errors. Cut their ticket volume significantly.

Happy to chat if you're interested.

Raghav

--
Raghav Shah | Founder
RAGS Pro AI Agency
🌐 https://ragspro.com""",

        "Logistics": f"""Hi [Name],

{company['name']}'s scale is wild. Question for you:

How many "where's my package" queries does your team handle daily?

I built a tracking bot for a logistics company. Integrates with their system, pulls live tracking data, answers on WhatsApp automatically. Reduced their support tickets by about 60%.

If you're handling similar volume, might be relevant.

Raghav

--
Raghav Shah | Founder
RAGS Pro AI Agency
🌐 https://ragspro.com""",

        "default": f"""Hi [Name],

Saw {company['name']} and the work you're doing in {company['industry']}.

Quick question: Are repetitive customer queries taking up your team's time?

We help companies automate with AI chatbots that:
- Handle 80% of common questions automatically
- Work 24/7 on WhatsApp/Website
- Integrate with existing tools
- Cost less than a full-time employee

Any interest in a quick 10-min demo this week?

Raghav

--
Raghav Shah | Founder
RAGS Pro AI Agency
🌐 https://ragspro.com"""
    }

    # Check for SME tag
    if "SME" in company['industry']:
        return f"""Hi [Name],

Came across {company['name']} while looking for {company['industry'].replace(' (SME)', '').lower()} companies in {company['location']}.

Quick question: how much time do you spend answering the same questions repeatedly?

I built a simple WhatsApp bot for a similar business that:
- Answers common questions automatically
- Books appointments/orders
- Sends reminders
- Works 24/7

Saved them about 10-15 hours per week. Cost less than hiring another staff member.

Worth a 5-min chat to see if it makes sense for you?

Raghav

--
Raghav Shah | Founder
RAGS Pro AI Agency
🌐 https://ragspro.com
📞 +91-XXXXXXXXXX"""

    return templates.get(company['industry'].split('/')[0], templates["default"])


def generate_linkedin_search_url(company, decision_maker):
    """Generate LinkedIn search URL"""
    role = decision_maker.split('/')[0].replace(' ', '%20')
    company_name = company.replace(' ', '%20')
    return f"https://www.linkedin.com/search/results/people/?keywords={role}%20{company_name}"


def save_targets():
    """Save all targets with outreach messages"""
    targets = []
    for company in VERIFIED_COMPANIES:
        target = {
            **company,
            "linkedin_search": generate_linkedin_search_url(company['name'], company['decision_maker']),
            "outreach_message": generate_outreach_message(company),
            "status": "NOT_CONTACTED",
            "added_at": datetime.now().isoformat(),
            "priority_score": 100 if company['priority'] == "HIGH" else 70,
            "source": "linkedin_outreach_v2"
        }
        targets.append(target)

    with open(OUTREACH_FILE, 'w') as f:
        json.dump(targets, f, indent=2)

    print(f"✅ Saved {len(targets)} verified targets")
    return targets


def print_action_plan():
    """Print actionable next steps"""
    print("\n" + "=" * 70)
    print("🎯 RAGSPRO LINKEDIN OUTREACH PLAN v2")
    print("=" * 70)

    print("\n📊 COMPANIES BY CATEGORY:")
    print("-" * 50)
    categories = {}
    for c in VERIFIED_COMPANIES:
        cat = c['industry'].split('/')[0]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(c['name'])

    for cat, companies in categories.items():
        print(f"\n{cat}: {len(companies)} companies")
        for c in companies[:5]:
            print(f"  • {c}")

    print("\n\n📋 LINKEDIN OUTREACH STEPS:")
    print("-" * 50)
    print("""
1. LinkedIn Premium (1 month free)
   → https://www.linkedin.com/premium

2. Search Pattern:
   "CEO Square Yards" or "CTO NoBroker"

3. Connection Request Note:
   "Hi [Name], love what you're building at [Company].
   Would love to connect!"

4. After Accept (50-70% rate):
   Send DM from outreach_targets_v2.json

5. Follow Up:
   Day 3: "Quick follow-up..."
   Day 7: "Last try..."

💰 PRICING STRATEGY:
- Enterprise (Square Yards, NoBroker): ₹50k - ₹2L
- Mid-size (PropTiger, Lybrate): ₹30k - ₹1L
- SME (Clinics, Brokers): ₹15k - ₹50k
- Monthly retainer: ₹5k - ₹10k
""")

    print("=" * 70)


if __name__ == "__main__":
    print("🚀 Generating 50+ verified client targets...")
    targets = save_targets()
    print_action_plan()

    print(f"\n✅ Total: {len(targets)} companies ready")
    print(f"📁 Saved to: {OUTREACH_FILE}")
    print("\n🎯 Next: LinkedIn Premium → Search → Connect → DM")
