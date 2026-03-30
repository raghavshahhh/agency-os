"""
RAGSPRO AI Assistant — Intelligent Agency AI with Full Dashboard CRUD
Speaks Hinglish + English, no BS, executes real actions
"""

import streamlit as st
import json
import subprocess
import sys
import re
import requests
from datetime import datetime
from pathlib import Path

ENGINE_DIR = Path(__file__).parent.parent / "engine"
sys.path.insert(0, str(ENGINE_DIR))

from config import (
    NVIDIA_API_KEY, NVIDIA_API_URL, NVIDIA_MODEL, DATA_DIR,
    AGENCY_NAME, SERVICES, CALENDLY_URL, RESEND_API_KEY
)

st.set_page_config(page_title=f"{AGENCY_NAME} AI", page_icon="🤖", layout="wide")

# ─── Data Paths ───────────────────────────────────────────────────────────────

LEADS_FILE = DATA_DIR / "leads.json"
PIPELINE_FILE = DATA_DIR / "pipeline.json"
CLIENTS_FILE = DATA_DIR / "clients.json"
REVENUE_FILE = DATA_DIR / "revenue.json"
OUTREACH_FILE = DATA_DIR / "outreach_log.json"
TEMPLATES_FILE = DATA_DIR / "email_templates.json"
CHAT_HISTORY_FILE = DATA_DIR / "chat_history.json"


# ─── Email Templates ─────────────────────────────────────────────────────────

DEFAULT_TEMPLATES = [
    {
        "id": "cold_intro",
        "name": "Cold Introduction",
        "category": "outreach",
        "subject": "Quick question about {project_type}",
        "body": "Hi {name},\n\nSaw your post about {requirement_short}. We've built similar solutions for clients — {relevant_example}.\n\nWould a 15-min call this week make sense? Here's my calendar: {calendly}\n\nBest,\nRaghav | RAGSPRO"
    },
    {
        "id": "followup_1",
        "name": "Follow-up #1 (3 days)",
        "category": "follow_up",
        "subject": "Re: {previous_subject}",
        "body": "Hi {name},\n\nJust following up on my last email. I put together a quick idea for your {project_type} — happy to share if you're interested.\n\nNo pressure either way.\n\nRaghav"
    },
    {
        "id": "followup_2",
        "name": "Follow-up #2 (7 days) — Value Add",
        "category": "follow_up",
        "subject": "{name}, thought this might help",
        "body": "Hi {name},\n\nI noticed {observation_about_their_business}. We recently helped a client in a similar spot and they saw {result}.\n\nHere's a quick case study if you're curious: {link}\n\nWorth a quick chat?\n\nRaghav | RAGSPRO"
    },
    {
        "id": "followup_3",
        "name": "Follow-up #3 (14 days) — Breakup",
        "category": "follow_up",
        "subject": "Closing the loop",
        "body": "Hi {name},\n\nI've reached out a couple times about helping with your {project_type}. Totally understand if the timing isn't right.\n\nIf things change, my calendar is always open: {calendly}\n\nWishing you the best!\n\nRaghav"
    },
    {
        "id": "proposal_followup",
        "name": "After Proposal Sent",
        "category": "proposal",
        "subject": "Thoughts on the proposal?",
        "body": "Hi {name},\n\nJust checking in — did you get a chance to look at the proposal for {project_type}?\n\nHappy to hop on a quick call to walk through it or adjust anything.\n\nRaghav"
    },
    {
        "id": "linkedin_connect",
        "name": "LinkedIn Connection",
        "category": "linkedin",
        "subject": "",
        "body": "Hey {name}, saw your post about {requirement_short}. I run RAGSPRO — we build AI chatbots and automation for businesses. Would love to connect!"
    },
    {
        "id": "reddit_dm",
        "name": "Reddit DM",
        "category": "reddit",
        "subject": "Re: {title_short}",
        "body": "Hey! Saw your post about {requirement_short}. We've done exactly this for other clients — {relevant_example}.\n\nHappy to share our approach if you're interested. No strings."
    },
    {
        "id": "fiverr_proposal",
        "name": "Fiverr Proposal",
        "category": "proposal",
        "subject": "",
        "body": "Hi! I read your requirements carefully — {requirement_short}.\n\nI've built similar {project_type} solutions. Here's what I'd do:\n1. {step_1}\n2. {step_2}\n3. {step_3}\n\nTimeline: {timeline}\nPortfolio: ragspro.com\n\nLet's discuss?"
    }
]


# ─── CRUD Functions ───────────────────────────────────────────────────────────

def load_json(filepath, default=None):
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return default if default is not None else []


def save_json(filepath, data):
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def get_dashboard_context():
    """Build complete dashboard context for AI"""
    leads = load_json(LEADS_FILE, [])
    pipeline = load_json(PIPELINE_FILE, [])
    clients = load_json(CLIENTS_FILE, [])
    revenue = load_json(REVENUE_FILE, {"entries": []})
    outreach = load_json(OUTREACH_FILE, [])
    templates = load_json(TEMPLATES_FILE, DEFAULT_TEMPLATES)

    rev = revenue.get("entries", []) if isinstance(revenue, dict) else []
    month = datetime.now().strftime("%Y-%m")
    month_income = sum(e["amount"] for e in rev if e.get("type") == "income" and e.get("date", "").startswith(month))
    month_expense = sum(e["amount"] for e in rev if e.get("type") == "expense" and e.get("date", "").startswith(month))

    # Leads breakdown
    new_leads = [l for l in leads if l.get("status") == "NEW"]
    contacted = [l for l in leads if l.get("status") == "CONTACTED"]
    hot = [l for l in leads if l.get("status") == "HOT_LEAD"]
    replied = [l for l in leads if l.get("status") == "REPLIED"]

    # Top 10 leads with contact info
    top_leads = sorted(leads, key=lambda x: x.get("score", 0), reverse=True)[:10]
    leads_detail = "\n".join([
        f"  - [{l.get('score')}] {l.get('title','')[:60]} | Email: {l.get('contact',{}).get('email','none')} | Status: {l.get('status')} | ID: {l.get('id')}"
        for l in top_leads
    ])

    pipeline_detail = "\n".join([
        f"  - {d.get('name','')[:50]} | Stage: {d.get('stage','')} | ₹{d.get('value',0):,} | ID: {d.get('id','')}"
        for d in pipeline[:5]
    ]) or "  No deals in pipeline"

    client_detail = "\n".join([
        f"  - {c.get('name','')} | Status: {c.get('status','')} | Paid: ₹{c.get('total_paid',0):,} | ID: {c.get('id','')}"
        for c in clients[:5]
    ]) or "  No clients yet"

    template_list = "\n".join([f"  - [{t['id']}] {t['name']} ({t['category']})" for t in templates])

    return f"""
=== RAGSPRO DASHBOARD LIVE DATA ===
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

📊 LEADS ({len(leads)} total):
  New: {len(new_leads)} | Contacted: {len(contacted)} | Replied: {len(replied)} | Hot: {len(hot)}
  WITH Email: {len([l for l in leads if l.get('contact',{}).get('email')])}
  WITH LinkedIn: {len([l for l in leads if l.get('contact',{}).get('linkedin')])}

Top 10 Leads:
{leads_detail}

💼 PIPELINE ({len(pipeline)} deals):
  Total Value: ₹{sum(d.get('value',0) for d in pipeline):,}
{pipeline_detail}

👥 CLIENTS ({len(clients)} total):
  Active: {len([c for c in clients if c.get('status')=='Active'])}
{client_detail}

💰 REVENUE (This Month):
  Income: ₹{month_income:,}
  Expenses: ₹{month_expense:,}
  Profit: ₹{month_income - month_expense:,}

📧 OUTREACH:
  Total Sent: {len(outreach)}
  Emails: {len([o for o in outreach if o.get('type')=='email'])}
  Via Resend: {len([o for o in outreach if o.get('sent_via')=='resend'])}
  Resend API: {'✅ Connected' if RESEND_API_KEY else '❌ Not set'}

📋 EMAIL TEMPLATES Available:
{template_list}

🛠️ AVAILABLE ACTIONS (I can execute these):
  [SCRAPE_LEADS] — Scrape new leads from Reddit
  [GENERATE_EMAIL lead_id] — Generate cold email for a lead
  [SEND_EMAIL lead_id email subject body] — Send email via Resend
  [GENERATE_CALL_SCRIPT lead_id] — Generate call script
  [GENERATE_LINKEDIN_DM lead_id] — Generate LinkedIn message
  [ADD_LEAD name title email] — Add a manual lead
  [UPDATE_LEAD_STATUS lead_id status] — Change lead status
  [DELETE_LEAD lead_id] — Remove a lead
  [ADD_CLIENT name email project_name value] — Add new client
  [ADD_REVENUE type amount category client] — Add revenue entry
  [ADD_PIPELINE name value stage] — Add pipeline deal
  [GENERATE_CONTENT platform topic] — Generate content
  [SHOW_TEMPLATE template_id] — Show an email template
  [TELEGRAM_BRIEF] — Send Telegram daily brief
"""


# ─── Action Executor ──────────────────────────────────────────────────────────

def execute_action(action_text):
    """Parse and execute actions from AI response"""
    results = []

    # Detect action commands in AI response
    action_patterns = {
        r'\[SCRAPE_LEADS\]': 'scrape_leads',
        r'\[GENERATE_EMAIL\s+(\S+)\]': 'generate_email',
        r'\[SEND_EMAIL\s+(\S+)\s+(\S+)\s+"([^"]+)"\s+"([^"]+)"\]': 'send_email',
        r'\[GENERATE_CALL_SCRIPT\s+(\S+)\]': 'generate_call_script',
        r'\[GENERATE_LINKEDIN_DM\s+(\S+)\]': 'generate_linkedin_dm',
        r'\[ADD_LEAD\s+"([^"]+)"\s+"([^"]+)"\s+"([^"]*)"\]': 'add_lead',
        r'\[UPDATE_LEAD_STATUS\s+(\S+)\s+(\S+)\]': 'update_lead_status',
        r'\[DELETE_LEAD\s+(\S+)\]': 'delete_lead',
        r'\[ADD_CLIENT\s+"([^"]+)"\s+"([^"]*)"\s+"([^"]+)"\s+(\d+)\]': 'add_client',
        r'\[ADD_REVENUE\s+(\S+)\s+(\d+)\s+"([^"]+)"\s+"([^"]*)"\]': 'add_revenue',
        r'\[ADD_PIPELINE\s+"([^"]+)"\s+(\d+)\s+"([^"]+)"\]': 'add_pipeline',
        r'\[GENERATE_CONTENT\s+"([^"]+)"\s+"([^"]+)"\]': 'generate_content',
        r'\[SHOW_TEMPLATE\s+(\S+)\]': 'show_template',
        r'\[TELEGRAM_BRIEF\]': 'telegram_brief',
    }

    for pattern, action_type in action_patterns.items():
        matches = re.findall(pattern, action_text)
        for match in matches:
            try:
                result = _execute_single(action_type, match)
                results.append(result)
            except Exception as e:
                results.append(f"❌ Error executing {action_type}: {str(e)}")

    return results


def _execute_single(action_type, params):
    """Execute a single action"""

    if action_type == 'scrape_leads':
        subprocess.Popen(["python3", str(ENGINE_DIR / "lead_scraper.py")],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return "🔄 Lead scraping started in background!"

    elif action_type == 'generate_email':
        lead_id = params if isinstance(params, str) else params[0]
        leads = load_json(LEADS_FILE, [])
        lead = next((l for l in leads if l.get("id") == lead_id), None)
        if not lead:
            return f"❌ Lead {lead_id} not found"

        from outreach_engine import generate_cold_email
        email = generate_cold_email(lead)
        return f"✅ Email generated:\n\n{email}" if email else "❌ Email generation failed"

    elif action_type == 'send_email':
        lead_id, to_email, subject, body = params
        from outreach_engine import send_email_resend, log_outreach
        result = send_email_resend(to_email, subject, body)
        if result["success"]:
            log_outreach(lead_id, "email", f"Subject: {subject}\n\n{body}",
                        sent_via="resend", to_email=to_email, resend_id=result.get("resend_id",""))
            leads = load_json(LEADS_FILE, [])
            for l in leads:
                if l.get("id") == lead_id:
                    l["status"] = "CONTACTED"
                    l["contacted_at"] = datetime.now().isoformat()
            save_json(LEADS_FILE, leads)
            return f"✅ Email sent to {to_email} via Resend!"
        return f"❌ Send failed: {result['error']}"

    elif action_type == 'generate_call_script':
        lead_id = params if isinstance(params, str) else params[0]
        leads = load_json(LEADS_FILE, [])
        lead = next((l for l in leads if l.get("id") == lead_id), None)
        if not lead:
            return f"❌ Lead {lead_id} not found"
        from outreach_engine import generate_call_script
        script = generate_call_script(lead)
        return f"✅ Call Script:\n\n{script}" if script else "❌ Script generation failed"

    elif action_type == 'generate_linkedin_dm':
        lead_id = params if isinstance(params, str) else params[0]
        leads = load_json(LEADS_FILE, [])
        lead = next((l for l in leads if l.get("id") == lead_id), None)
        if not lead:
            return f"❌ Lead {lead_id} not found"
        from outreach_engine import generate_linkedin_dm
        dm = generate_linkedin_dm(lead)
        return f"✅ LinkedIn DM:\n\n{dm}" if dm else "❌ DM generation failed"

    elif action_type == 'add_lead':
        name, title, email = params
        leads = load_json(LEADS_FILE, [])
        new_lead = {
            "id": f"ai_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": name, "title": title,
            "requirement": "", "url": "",
            "platform": "AI Added", "score": 80,
            "status": "NEW",
            "extracted_at": datetime.now().isoformat(),
            "posted_at": datetime.now().isoformat(),
            "contact": {"email": email, "emails": [email] if email else [],
                       "linkedin": "", "phone": "", "phones": [], "reddit_user": ""},
            "pain_points": [], "tags": []
        }
        leads.append(new_lead)
        save_json(LEADS_FILE, leads)
        return f"✅ Lead added: {name} — {title}"

    elif action_type == 'update_lead_status':
        lead_id, new_status = params
        leads = load_json(LEADS_FILE, [])
        found = False
        for l in leads:
            if l.get("id") == lead_id:
                l["status"] = new_status
                if new_status == "CONTACTED":
                    l["contacted_at"] = datetime.now().isoformat()
                found = True
                break
        if found:
            save_json(LEADS_FILE, leads)
            return f"✅ Lead {lead_id} → {new_status}"
        return f"❌ Lead {lead_id} not found"

    elif action_type == 'delete_lead':
        lead_id = params if isinstance(params, str) else params[0]
        leads = load_json(LEADS_FILE, [])
        original = len(leads)
        leads = [l for l in leads if l.get("id") != lead_id]
        if len(leads) < original:
            save_json(LEADS_FILE, leads)
            return f"✅ Lead {lead_id} deleted"
        return f"❌ Lead {lead_id} not found"

    elif action_type == 'add_client':
        name, email, project, value = params
        clients = load_json(CLIENTS_FILE, [])
        new_client = {
            "id": f"client_ai_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": name, "email": email, "phone": "", "company": "",
            "industry": "Technology", "source": "AI Added",
            "status": "Active",
            "projects": [{"name": project, "value": int(value), "status": "In Progress",
                         "started_at": datetime.now().isoformat()}],
            "total_paid": 0, "notes": "",
            "created_at": datetime.now().isoformat(),
            "communication_log": []
        }
        clients.append(new_client)
        save_json(CLIENTS_FILE, clients)
        return f"✅ Client added: {name} — {project} (₹{value})"

    elif action_type == 'add_revenue':
        rev_type, amount, category, client = params
        revenue = load_json(REVENUE_FILE, {"entries": [], "goals": {"monthly": 100000}})
        if not isinstance(revenue, dict):
            revenue = {"entries": [], "goals": {"monthly": 100000}}
        entry = {
            "id": f"rev_ai_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "type": rev_type, "amount": int(amount),
            "category": category, "client": client,
            "description": f"Added by AI", "date": datetime.now().strftime("%Y-%m-%d"),
            "created_at": datetime.now().isoformat()
        }
        revenue.setdefault("entries", []).append(entry)
        save_json(REVENUE_FILE, revenue)
        return f"✅ Revenue entry: {rev_type} ₹{amount} ({category})"

    elif action_type == 'add_pipeline':
        name, value, stage = params
        pipeline = load_json(PIPELINE_FILE, [])
        deal = {
            "id": f"deal_ai_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "name": name, "value": int(value), "stage": stage,
            "client": "", "created_at": datetime.now().isoformat()
        }
        pipeline.append(deal)
        save_json(PIPELINE_FILE, pipeline)
        return f"✅ Pipeline deal: {name} ₹{value} ({stage})"

    elif action_type == 'generate_content':
        platform, topic = params
        subprocess.Popen(["python3", str(ENGINE_DIR / "content_engine.py")],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return f"🔄 Content generation started for {platform} — {topic}"

    elif action_type == 'show_template':
        template_id = params if isinstance(params, str) else params[0]
        templates = load_json(TEMPLATES_FILE, DEFAULT_TEMPLATES)
        template = next((t for t in templates if t.get("id") == template_id), None)
        if template:
            return f"📋 Template: **{template['name']}**\n\nSubject: {template.get('subject','')}\n\n{template['body']}"
        return f"❌ Template '{template_id}' not found"

    elif action_type == 'telegram_brief':
        subprocess.Popen(["python3", str(ENGINE_DIR / "telegram_brief.py")],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return "📱 Telegram brief sent!"

    return "❌ Unknown action"


# ─── AI Call ──────────────────────────────────────────────────────────────────

def call_ai(messages, context):
    """Call NVIDIA NIM with full dashboard context"""
    if not NVIDIA_API_KEY:
        return "❌ NVIDIA API key not set. Go to Settings to configure."

    system_prompt = f"""Tu RAGSPRO ka AI Assistant hai — intelligent, practical, and action-oriented.

PERSONALITY:
- Bolna tujhe Hinglish (Hindi + English) mein hi hai, lekin **STRICTLY english letters/alphabets use kar** (No Devanagari script). Example: 'Kaam ho gaya' likhna hai, 'काम हो गया' NAHI likhna hai. Ye sabse important rule hai!
- Aisa behave kar jaise tu mera agency partner hai.
- Bakwas mat kar. Seedha kaam ki baat kar.
- Professional but friendly — client ke saamne toh professional reh lekin apne team (user) ke saath casual
- Proactively suggest karo — improvements, next steps, strategies
- Jab action lena ho toh seedha action commands use kar

CAPABILITIES — Tu ye sab kar sakta hai:
1. LEADS — Read, add, delete, update status, generate outreach (email/call script/LinkedIn DM)
2. PIPELINE — Read deals, add new deals, update stages
3. CLIENTS — Read, add clients, track projects
4. REVENUE — Read, add income/expenses
5. CONTENT — Generate social media content
6. EMAIL — Generate + send via Resend
7. TEMPLATES — Show email/message templates for outreach
8. LEAD VERIFICATION: Jab user puche ki 'verified leads kaise milenge', toh unko suggest kar ki: "Abhi hum Reddit scraping use kar rahe hain (intent-based). Verified emails ke liye, humein Apollo.io API (search verified B2B emails via domain/person) ya Hunter.io API (domain search) integrate karna padega `outreach_engine.py` mein." Thoda detail dena inke bare me agar puche.

OUTREACH STRATEGY (follow this when advising):
- Reddit leads: DM first, then email if available
- LinkedIn leads: Connection request with note → follow up with value
- Email leads: Cold email → Follow-up #1 (3 days) → Follow-up #2 (7 days) → Breakup email (14 days)
- Call: Use when lead has phone number and is HOT_LEAD
- Always personalize. Reference their EXACT requirement.
- Never send generic copy-paste messages.

WHEN USER ASKS TO DO SOMETHING:
- Use action commands in your response: [ACTION_NAME params]
- Example: User says "is lead ko email bhej do" → Generate email and include [SEND_EMAIL lead_id email "subject" "body"]
- Example: User says "new client add karo" → [ADD_CLIENT "name" "email" "project" value]

CURRENT DASHBOARD DATA:
{context}

RULES:
1. Har response mein value de — data, insight, ya action
2. Jab lead ke baare mein baat ho toh uska ID mention kar
3. Templates suggest kar jab outreach ki baat ho
4. Agar user kuch ask kare jo tu kar sakta hai → seedha kar de, permission mat maang
5. Revenue/pipeline numbers accurately bata
6. Proactively batao kya improve ho sakta hai"""

    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }

    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages[-10:]:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    payload = {
        "model": NVIDIA_MODEL,
        "messages": api_messages,
        "temperature": 0.7,
        "max_tokens": 1200
    }

    try:
        response = requests.post(NVIDIA_API_URL, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ AI Error: {str(e)}"


# ─── CSS ──────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .main { font-family: 'Inter', sans-serif; }

    .ai-header {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1rem;
    }
    .ai-header h2 {
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        font-size: 1.3rem;
    }
    .ai-header p { color: rgba(255,255,255,0.6); font-size: 0.8rem; margin: 0.25rem 0 0; }

    .template-card {
        background: #f8f9ff;
        border: 1px solid #e0e5ff;
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        margin-bottom: 0.4rem;
        font-size: 0.82rem;
        cursor: pointer;
    }
    .template-card:hover { background: #eef2ff; }

    .action-result {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 8px;
        padding: 0.6rem;
        font-size: 0.85rem;
        margin: 0.3rem 0;
    }

    .quick-btn {
        display: inline-block;
        background: #667eea;
        color: white !important;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 500;
        margin: 3px;
        text-decoration: none;
    }
</style>
""", unsafe_allow_html=True)


# ─── Layout ───────────────────────────────────────────────────────────────────

st.markdown("""
<div class='ai-header'>
    <h2>🤖 RAGSPRO AI Assistant</h2>
    <p>Full CRUD access • Leads • Pipeline • Clients • Revenue • Outreach • Templates</p>
</div>
""", unsafe_allow_html=True)

# Sidebar with templates + stats
with st.sidebar:
    st.markdown("### ⚡ Quick Actions")

    qa_col1, qa_col2 = st.columns(2)
    with qa_col1:
        if st.button("🔄 Scrape Leads", use_container_width=True, key="qa_scrape"):
            st.session_state.setdefault("messages", []).append({"role": "user", "content": "New leads scrape karo Reddit se"})
            st.rerun()
        if st.button("📊 Dashboard Summary", use_container_width=True, key="qa_summary"):
            st.session_state.setdefault("messages", []).append({"role": "user", "content": "Full dashboard summary de — leads, pipeline, revenue, clients sab"})
            st.rerun()
    with qa_col2:
        if st.button("📧 Top Lead Email", use_container_width=True, key="qa_email"):
            st.session_state.setdefault("messages", []).append({"role": "user", "content": "Top 3 leads dikhao aur sabse best ke liye cold email generate karo"})
            st.rerun()
        if st.button("📱 Telegram Brief", use_container_width=True, key="qa_tg"):
            st.session_state.setdefault("messages", []).append({"role": "user", "content": "Telegram brief bhej do"})
            st.rerun()

    st.markdown("---")

    # Email Templates
    st.markdown("### 📋 Email Templates")
    templates = load_json(TEMPLATES_FILE, DEFAULT_TEMPLATES)
    for t in templates:
        with st.expander(f"{t['name']}", expanded=False):
            if t.get("subject"):
                st.caption(f"Subject: {t['subject']}")
            st.text(t["body"][:200])
            if st.button("Use Template", key=f"use_{t['id']}"):
                st.session_state.setdefault("messages", []).append(
                    {"role": "user", "content": f"Template '{t['name']}' use karo top lead ke liye"}
                )
                st.rerun()

    st.markdown("---")

    # Live Stats
    st.markdown("### 📊 Live Stats")
    leads = load_json(LEADS_FILE, [])
    pipeline = load_json(PIPELINE_FILE, [])
    clients = load_json(CLIENTS_FILE, [])
    outreach = load_json(OUTREACH_FILE, [])

    st.metric("Leads", len(leads))
    st.metric("Hot Leads 🔥", len([l for l in leads if l.get("status") == "HOT_LEAD"]))
    st.metric("Pipeline Value", f"₹{sum(d.get('value',0) for d in pipeline):,}")
    st.metric("Clients", len([c for c in clients if c.get("status") == "Active"]))
    st.metric("Emails Sent", len([o for o in outreach if o.get("type") == "email"]))


# ─── Chat ─────────────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []

# Load chat history
if not st.session_state.messages:
    history = load_json(CHAT_HISTORY_FILE, [])
    if history:
        st.session_state.messages = history[-20:]  # Last 20 messages

# Display chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Show action results
        if msg.get("action_results"):
            for result in msg["action_results"]:
                st.markdown(f"<div class='action-result'>{result}</div>", unsafe_allow_html=True)

# Welcome message
if not st.session_state.messages:
    with st.chat_message("assistant"):
        leads_data = load_json(LEADS_FILE, [])
        hot = len([l for l in leads_data if l.get("status") == "HOT_LEAD"])
        new = len([l for l in leads_data if l.get("status") == "NEW"])

        welcome = f"""Yo! 🤖 Main RAGSPRO AI hun — tera agency ka right hand.

**Kya kya kar sakta hun:**
- 📊 Dashboard ki puri intel — leads, pipeline, revenue, clients
- ✉️ Cold emails, call scripts, LinkedIn DMs generate + **seedha send** via Resend
- 📋 Email templates ready hai sidebar mein — use karo ya customize karo
- 👥 Leads add/delete/update, clients add, pipeline deals manage
- 🔄 Reddit se fresh leads scrape karo
- 💰 Revenue track karo

**Abhi ka scene:**
- {len(leads_data)} leads hai, {new} new, {hot} hot 🔥
- {len([l for l in leads_data if l.get('contact',{}).get('email')])} leads ke paas email hai
- Resend: {'✅ Ready' if RESEND_API_KEY else '❌ Set karo Settings mein'}

**Bol kya karna hai?** Seedha bata — main kar dunga."""

        st.markdown(welcome)

# Chat input
if prompt := st.chat_input("Bol kya karna hai..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Soch raha hun..."):
            context = get_dashboard_context()
            ai_response = call_ai(st.session_state.messages, context)

        # Execute any actions
        action_results = execute_action(ai_response)

        # Clean action tags from display
        display_response = ai_response
        for pattern in [r'\[SCRAPE_LEADS\]', r'\[GENERATE_EMAIL\s+\S+\]', r'\[SEND_EMAIL[^\]]*\]',
                       r'\[GENERATE_CALL_SCRIPT\s+\S+\]', r'\[GENERATE_LINKEDIN_DM\s+\S+\]',
                       r'\[ADD_LEAD[^\]]*\]', r'\[UPDATE_LEAD_STATUS[^\]]*\]', r'\[DELETE_LEAD[^\]]*\]',
                       r'\[ADD_CLIENT[^\]]*\]', r'\[ADD_REVENUE[^\]]*\]', r'\[ADD_PIPELINE[^\]]*\]',
                       r'\[GENERATE_CONTENT[^\]]*\]', r'\[SHOW_TEMPLATE[^\]]*\]', r'\[TELEGRAM_BRIEF\]']:
            display_response = re.sub(pattern, '', display_response)

        st.markdown(display_response.strip())

        # Show action results
        if action_results:
            st.markdown("---")
            st.markdown("**⚡ Actions Executed:**")
            for result in action_results:
                st.markdown(f"<div class='action-result'>{result}</div>", unsafe_allow_html=True)

        # Save message
        msg = {"role": "assistant", "content": ai_response, "action_results": action_results}
        st.session_state.messages.append(msg)

    # Save history
    save_json(CHAT_HISTORY_FILE, st.session_state.messages[-50:])

# Clear chat button
if st.session_state.messages:
    if st.button("🗑 Clear Chat", key="clear_chat"):
        st.session_state.messages = []
        save_json(CHAT_HISTORY_FILE, [])
        st.rerun()
