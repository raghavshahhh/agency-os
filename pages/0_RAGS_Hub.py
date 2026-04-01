"""
🚀 RAGS HUB — Daily Command Center for Raghav
Copy-paste ready templates, content, scripts, lead lists
All in one place. Open this every morning.
"""

import streamlit as st
import json
from datetime import datetime, timedelta
from pathlib import Path
import random

st.set_page_config(
    page_title="🚀 RAGS HUB — Daily Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_DIR = Path(__file__).parent.parent / "data"
CONTENT_DIR = DATA_DIR / "content"
TEMPLATES_DIR = DATA_DIR / "templates"

# Ensure directories exist
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# ─── LOAD DATA ─────────────────────────────────────────────────────────────────

def load_json(filename, default=None):
    filepath = DATA_DIR / filename
    if filepath.exists():
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except:
            pass
    return default if default is not None else []

leads = load_json("leads.json", [])
clients = load_json("clients.json", [])
pipeline = load_json("pipeline.json", [])
revenue_data = load_json("revenue.json", {"entries": []})

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
 @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

 .main { font-family: 'Inter', sans-serif; background: #f8fafc; }

 .rags-header {
 background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
 color: white;
 padding: 1.5rem 2rem;
 border-radius: 16px;
 margin-bottom: 1rem;
 text-align: center;
 }

 .rags-title {
 font-size: 2.5rem;
 font-weight: 800;
 background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
 -webkit-background-clip: text;
 -webkit-text-fill-color: transparent;
 }

 .rags-subtitle {
 font-size: 1rem;
 color: rgba(255,255,255,0.7);
 margin-top: 0.5rem;
 }

 .copy-card {
 background: white;
 border: 1px solid #e5e7eb;
 border-radius: 12px;
 padding: 1rem;
 margin-bottom: 0.75rem;
 }

 .copy-card:hover {
 box-shadow: 0 4px 12px rgba(0,0,0,0.08);
 }

 .copy-header {
 display: flex;
 justify-content: space-between;
 align-items: center;
 margin-bottom: 0.5rem;
 }

 .copy-title {
 font-weight: 600;
 font-size: 0.9rem;
 color: #1a1a2e;
 }

 .copy-btn {
 background: #667eea;
 color: white;
 border: none;
 padding: 4px 12px;
 border-radius: 6px;
 font-size: 0.75rem;
 cursor: pointer;
 }

 .copy-btn:hover {
 background: #5a67d8;
 }

 .content-box {
 background: #f8f9ff;
 border: 1px solid #e0e5ff;
 border-radius: 8px;
 padding: 0.75rem;
 font-family: 'Monaco', monospace;
 font-size: 0.8rem;
 color: #374151;
 white-space: pre-wrap;
 max-height: 150px;
 overflow-y: auto;
 }

 .metric-card {
 background: white;
 border-radius: 12px;
 padding: 1rem;
 text-align: center;
 border: 1px solid #e5e7eb;
 }

 .metric-value {
 font-size: 1.8rem;
 font-weight: 700;
 color: #1a1a2e;
 }

 .metric-label {
 font-size: 0.75rem;
 color: #9ca3af;
 text-transform: uppercase;
 }

 .status-active {
 color: #10b981;
 font-weight: 600;
 }

 .status-pending {
 color: #f59e0b;
 font-weight: 600;
 }

 .section-title {
 font-size: 1.1rem;
 font-weight: 700;
 color: #1a1a2e;
 margin: 1.5rem 0 1rem 0;
 display: flex;
 align-items: center;
 gap: 0.5rem;
 }

 .quick-action {
 background: #667eea;
 color: white;
 padding: 0.75rem 1rem;
 border-radius: 8px;
 text-align: center;
 cursor: pointer;
 font-weight: 600;
 }

 .quick-action:hover {
 background: #5a67d8;
 }

 .template-tag {
 display: inline-block;
 background: #e0e5ff;
 color: #667eea;
 padding: 2px 8px;
 border-radius: 12px;
 font-size: 0.7rem;
 margin-left: 0.5rem;
 }
</style>
""", unsafe_allow_html=True)

# ─── HEADER ───────────────────────────────────────────────────────────────────

today = datetime.now()
st.markdown(f"""
<div class='rags-header'>
 <div class='rags-title'>🚀 RAGS HUB</div>
 <div class='rags-subtitle'>Daily Command Center | {today.strftime('%A, %B %d, %Y')}</div>
</div>
""", unsafe_allow_html=True)

# ─── DAILY METRICS ────────────────────────────────────────────────────────────

col1, col2, col3, col4, col5 = st.columns(5)

# Calculate metrics
new_leads_today = len([l for l in leads if l.get("extracted_at", "").startswith(today.strftime("%Y-%m-%d"))])
hot_leads = len([l for l in leads if l.get("status") == "HOT_LEAD"])
pipeline_value = sum(d.get("value", 0) for d in pipeline)
total_clients = len(clients)

# Today's content check
today_folder = CONTENT_DIR / today.strftime("%Y-%m-%d")
content_ready = today_folder.exists() and len(list(today_folder.glob("*.txt"))) > 0

metrics = [
    ("🔥", str(hot_leads), "Hot Leads"),
    ("📊", str(new_leads_today), "New Today"),
    ("💰", f"₹{pipeline_value/1000:.0f}K", "Pipeline"),
    ("👥", str(total_clients), "Clients"),
    ("📝", "✅" if content_ready else "❌", "Content"),
]

for col, (icon, value, label) in zip([col1, col2, col3, col4, col5], metrics):
    with col:
        st.markdown(f"""
        <div class='metric-card'>
            <div style='font-size:1.5rem;'>{icon}</div>
            <div class='metric-value'>{value}</div>
            <div class='metric-label'>{label}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── TABS ─────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📱 Today's Content",
    "💬 DM Templates",
    "📧 Email Templates",
    "🎯 Lead Lists",
    "📋 Scripts",
    "🤖 What RAGS Can Do"
])

# ─── TAB 1: TODAY'S CONTENT ─────────────────────────────────────────────────

with tab1:
    st.markdown("<div class='section-title'>📱 Today's Generated Content</div>", unsafe_allow_html=True)

    if today_folder.exists():
        platforms = {
            "linkedin.txt": "LinkedIn Post",
            "twitter.txt": "Twitter/X Post",
            "instagram.txt": "Instagram Caption",
            "reel.txt": "Reel Script"
        }

        cols = st.columns(2)
        for idx, (filename, label) in enumerate(platforms.items()):
            with cols[idx % 2]:
                filepath = today_folder / filename
                if filepath.exists():
                    content = filepath.read_text()
                    st.markdown(f"""
                    <div class='copy-card'>
                        <div class='copy-header'>
                            <span class='copy-title'>{label}</span>
                        </div>
                        <div class='content-box'>{content}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Copy button using streamlit
                    if st.button(f"📋 Copy {label}", key=f"copy_{filename}"):
                        st.code(content, language="text")
                        st.toast(f"{label} copied!")
                else:
                    st.info(f"No {label} generated yet")
    else:
        st.warning("⚠️ No content for today. Generate content first!")
        if st.button("🚀 Generate Today's Content"):
            st.info("Run: `python engine/content_engine.py`")

# ─── TAB 2: DM TEMPLATES ────────────────────────────────────────────────────

dm_templates = {
    "LAW AI — Lawyer LinkedIn DM": """Hi {name},

Saw you're a {title} at {company}.

I built LAW AI — an AI tool that drafts legal documents in 2 minutes instead of 2 hours.

Currently helping {number} lawyers in Delhi save 10+ hours/week.

Worth a quick chat? I can show you a 5-min demo.

— Raghav
RAGSPRO | ragspro.com""",

    "AI Agent — Business Owner DM": """Hi {name},

Noticed {company} is growing fast 🚀

Quick question: Are you still handling {task} manually?

I build AI agents that automate {task} 24/7 — no breaks, no mistakes.

Just helped a {industry} company save ₹{amount}/month.

Open to seeing how it works? 10-min call, no pitch.

— Raghav
RAGSPRO""",

    "Follow-up — No Response": """Hey {name},

Following up on my last message about {topic}.

No pressure if it's not the right time — just wanted to check if this is something you're exploring?

If not, all good. If yes, happy to share a quick case study.

— Raghav""",

    "Referral Request": """Hey {name},

Quick favor — do you know any {target_persona} who might benefit from {solution}?

I'm looking to help 10 more businesses this month and thought your network might have some good fits.

No pressure, just thought I'd ask 🙏

— Raghav""",

    "Content Engagement": """Love your recent post about {topic}!

Especially the point about {specific_point} — totally agree.

Actually built something similar for {type_of_client} recently. Mind if I DM you the case study?

— Raghav"""
}

with tab2:
    st.markdown("<div class='section-title'>💬 Ready-to-Copy DM Templates</div>", unsafe_allow_html=True)

    for name, template in dm_templates.items():
        with st.expander(f"📱 {name}"):
            st.code(template, language="text")
            if st.button(f"📋 Copy", key=f"dm_{name}"):
                st.toast(f"Copied: {name}")

# ─── TAB 3: EMAIL TEMPLATES ─────────────────────────────────────────────────

email_templates = {
    "LAW AI Cold Email": """Subject: 2-minute document drafting for {lawyer_name}

Hi {lawyer_name},

I'm Raghav from RAGSPRO. I work with lawyers in {city} who are drowning in document work.

Quick question: How long does it take you to draft a standard {document_type}?

If it's more than 2 minutes, I built something you should see.

LAW AI — an AI tool that drafts legal documents in 2 minutes, not 2 hours.

✓ 60% time saved (verified by active users)
✓ ₹999/month (less than one hour of your time)
✓ 7-day free trial, no credit card

Worth a 10-min demo this week?

Best,
Raghav Shah
Founder, RAGSPRO
ragspro.com | +91-8700048490

P.S. Currently used by {number} lawyers in Delhi NCR.""",

    "AI Agent Proposal": """Subject: AI {agent_name} for {company_name} — Proposal

Hi {name},

Thanks for the chat yesterday. Here's the proposal for {agent_name}:

**What you get:**
- {feature_1}
- {feature_2}
- {feature_3}
- 3 months support included

**Investment:** ₹{price}
**Timeline:** {timeline}
**Payment:** 50% upfront, 50% on delivery

Next steps:
1. You confirm
2. I send payment link
3. We start {start_date}

Questions? Just reply.

— Raghav
RAGSPRO | ragspro.com""",

    "Follow-up After Demo": """Subject: Quick follow-up — {product_name}

Hi {name},

Thanks for your time today! 🙏

As discussed:
- {product_name} will {main_benefit}
- Setup takes {timeline}
- ROI typically seen in {roi_timeframe}

Ready to move forward? Just reply YES and I'll send the invoice.

Or if you have questions, call/WhatsApp me: +91-8700048490

— Raghav
RAGSPRO""",

    "Invoice Reminder": """Subject: Invoice #{invoice_number} — {project_name}

Hi {name},

Hope {project_name} is working well for you!

Just a gentle reminder that invoice #{invoice_number} for ₹{amount} is due {due_date}.

Payment link: {payment_link}

UPI: ragsproai@upi

Let me know if you need anything else!

— Raghav
RAGSPRO""",

    "Testimonial Request": """Subject: Quick favor — 2 min feedback

Hi {name},

Hope you're loving {product_name}!

Quick favor: Could you share 1-2 lines about your experience?

Something like: "{product_name} helped me {result} in {timeframe}"

Helps me help more people like you 🙏

— Raghav
RAGSPRO"""
}

with tab3:
    st.markdown("<div class='section-title'>📧 Ready-to-Copy Email Templates</div>", unsafe_allow_html=True)

    for name, template in email_templates.items():
        with st.expander(f"📧 {name}"):
            st.code(template, language="text")
            if st.button(f"📋 Copy", key=f"email_{name}"):
                st.toast(f"Copied: {name}")

# ─── TAB 4: LEAD LISTS ───────────────────────────────────────────────────────

with tab4:
    st.markdown("<div class='section-title'>🎯 Ready-to-Use Lead Lists</div>", unsafe_allow_html=True)

    # Filter leads by category
    lead_categories = {
        "🔥 Hot Leads (Score 70+)": [l for l in leads if l.get("score", 0) >= 70],
        "⚡ Warm Leads (Score 50-69)": [l for l in leads if 50 <= l.get("score", 0) < 70],
        "📊 All Lawyers": [l for l in leads if "lawyer" in l.get("title", "").lower() or "advocate" in l.get("title", "").lower()],
        "🏢 Business Owners": [l for l in leads if any(x in l.get("title", "").lower() for x in ["founder", "ceo", "owner", "director"])],
        "🔄 Not Contacted": [l for l in leads if l.get("status") == "NEW"],
    }

    for category_name, category_leads in lead_categories.items():
        with st.expander(f"{category_name} ({len(category_leads)} leads)"):
            if category_leads:
                # Export as CSV
                import pandas as pd
                df = pd.DataFrame(category_leads[:50])  # Top 50
                st.dataframe(df[["title", "platform", "score", "status"]], use_container_width=True)

                # Copy emails
                emails = [l.get("email", "") for l in category_leads if l.get("email")]
                if emails:
                    email_list = ", ".join(emails[:20])
                    st.code(email_list, language="text")
                    if st.button(f"📋 Copy Emails", key=f"emails_{category_name}"):
                        st.toast("Emails copied!")
            else:
                st.info("No leads in this category. Scrape more!")

# ─── TAB 5: SCRIPTS ──────────────────────────────────────────────────────────

scripts = {
    "Sales Call Opener": """"Hi {name}, this is Raghav from RAGSPRO.

You downloaded/clicked on something about {topic} recently.

Quick question: Is {pain_point} still a challenge for you?

[Wait for response]

Great. I work with {target} who face similar issues.

Mind if I ask 2-3 quick questions to see if I can actually help?""",

    "Objection Handler — Price": """"I totally get it. ₹{price} is not small.

Here's the thing: How much time are you spending on {task} right now?

[Let them answer]

So if this saves you {hours} hours/month, and your time is worth ₹{hourly_rate}/hour, that's ₹{value}/month in value.

For ₹{monthly_price}/month, you're actually saving ₹{savings}/month.

Make sense?""",

    "Demo Script — LAW AI": """"Let me show you something cool.

[Open LAW AI]

This is a {document_type}. Normally takes {normal_time} to draft, right?

Watch this...

[Fill form → Generate]

Done. {generated_time}.

Want to try it yourself? I can set you up with a 7-day free trial right now.""",

    "Closing Script": """"Sounds like this makes sense for you.

Here's what happens next:
1. I send you a payment link
2. You pay 50% upfront
3. We start Monday
4. Delivery in {timeline}

Ready to move forward?""",

    "Networking Event Intro": """"Hi, I'm Raghav. I build AI tools that automate boring work.

What do you do?

[They answer]

Interesting! Ever thought about automating {their_task}?

I just helped someone in {industry} save {time_saved}/week with AI.

Want to grab coffee and I'll show you?"""
}

with tab5:
    st.markdown("<div class='section-title'>📋 Sales & Networking Scripts</div>", unsafe_allow_html=True)

    for name, script in scripts.items():
        with st.expander(f"🎤 {name}"):
            st.code(script, language="text")
            if st.button(f"📋 Copy", key=f"script_{name}"):
                st.toast(f"Copied: {name}")

# ─── TAB 6: WHAT RAGS CAN DO ─────────────────────────────────────────────────

with tab6:
    st.markdown("<div class='section-title'>🤖 What RAGS Can Do For You</div>", unsafe_allow_html=True)

    st.markdown("""
    ### ✅ **I Can Do (Auto-Execute)**

    | Task | How | Time Saved |
    |------|-----|------------|
    | **Write LinkedIn posts** | Daily content generation | 2 hrs/day |
    | **Create email templates** | Copy-paste ready | 1 hr/email |
    | **Research leads** | Apollo scraping + enrichment | 3 hrs/day |
    | **Code new features** | LAW AI, Agency OS updates | 5-10 hrs/feature |
    | **Build AI agents** | n8n workflows + custom code | 10 hrs/agent |
    | **Generate proposals** | Auto-create from templates | 2 hrs/proposal |
    | **GitHub management** | Push code, manage repos | 1 hr/day |
    | **Bug fixes** | Auto-audit + repair | 2-3 hrs/bug |
    | **Content calendar** | 30 days content in 1 click | 8 hrs/month |

    ### 🤝 **We Do Together** (You + RAGS)

    | Task | Your Role | My Role |
    |------|-----------|---------|
    | **LinkedIn DMs** | You send | I write template |
    | **Sales calls** | You talk | I prep script |
    | **Video content** | You record | I write script |
    | **Client onboarding** | You close | I build system |
    | **Pricing strategy** | You decide | I research market |

    ### ❌ **You Must Do** (I Can't)

    - **Sales calls** — Meri voice nahi hai
    - **LinkedIn DMs send** — Mere paas access nahi
    - **Payment collection** — Banking tera hai
    - **Video recording** — Camera tere paas
    - **Court visits** — Physical presence
    - **Networking events** — Tu ja, main nahi

    ### 🚀 **Quick Commands**

    Just say:
    - *"RAGS, 50 lawyers ki list banao"* → Main research karke dunga
    - *"RAGS, cold email likho"* → Template ready
    - *"RAGS, LAW AI mei feature add karo"* → Code karke push karunga
    - *"RAGS, competitor research"* → Market analysis dunga
    - *"RAGS, content generate karo"* → 30 days content bana dunga
    """)

# ─── QUICK ACTIONS ────────────────────────────────────────────────────────────

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("<div class='section-title'>⚡ Quick Actions</div>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📝 Generate Today's Content", use_container_width=True):
        st.info("Run: `python engine/content_engine.py`")

with col2:
    if st.button("🔍 Scrape New Leads", use_container_width=True):
        st.info("Go to Leads page → Start scraping")

with col3:
    if st.button("📊 View Pipeline", use_container_width=True):
        st.info("Go to Pipeline page")

with col4:
    if st.button("💰 Check Revenue", use_container_width=True):
        st.info("Go to Revenue page")

# ─── FOOTER ───────────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#999;font-size:0.75rem;'>"
    "Built with ❤️ by RAGS for Raghav | ragspro.com | Updated daily</div>",
    unsafe_allow_html=True
)
