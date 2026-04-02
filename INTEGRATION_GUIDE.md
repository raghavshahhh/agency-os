# Agency OS + Sales Automation — Integration Guide

## 🎯 What Was Implemented

### New Features Added:

| Feature | File | Purpose |
|---------|------|---------|
| **Apify Scraper** | `engine/apify_scraper.py` | Scrapes Google Maps + LinkedIn for real business leads |
| **Email Automation** | `engine/email_automation.py` | Day 0/3/7 email sequences automatically |
| **Scheduler V2** | `scheduler_v2.py` | Runs all automation every 4 hours |
| **n8n Workflow** | `workflows/n8n_agency_os_integration.json` | Import into n8n for visual automation |
| **Sales System Doc** | `data/AGENCY_OS_SALES_MARKETING_SYSTEM.md` | Complete strategy guide |

---

## 🔧 How It Connects

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENCY OS DASHBOARD                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐          │
│  │  Leads   │  │  Revenue │  │   Pipeline       │          │
│  │  (13k+)  │  │  Tracker │  │   (Deals)        │          │
│  └──────────┘  └──────────┘  └──────────────────┘          │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
┌───────▼──────┐ ┌─────▼──────┐ ┌──────▼──────┐
│ Apify        │ │  Email     │ │ Scheduler   │
│ Scraper      │ │  Automation│ │ V2          │
│              │ │            │ │             │
│ • Google     │ │ • Day 0   │ │ • Every 4h  │
│   Maps       │ │ • Day 3   │ │ • Telegram  │
│ • LinkedIn   │ │ • Day 7   │ │ • Reports   │
└───────┬──────┘ └─────┬──────┘ └─────────────┘
        │              │
        └──────────────┴───────────────────┐
                                           │
                              ┌────────────▼────────────┐
                              │        n8n              │
                              │  (localhost:5678)       │
                              │  - Visual workflows     │
                              │  - Webhook triggers     │
                              └─────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd ~/Desktop/Agency\ OS
pip install schedule
```

### 2. Set API Keys

Add to your `.env` file:

```bash
# Apify (for Google Maps scraping)
APIFY_TOKEN=your_apify_token_here

# Resend (for email sending) - Already set
RESEND_API_KEY=your_resend_key

# Telegram - Already set
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id

# n8n (optional)
N8N_URL=http://localhost:5678
N8N_API_KEY=your_n8n_key
```

### 3. Test Scraper

```bash
# Test Apify scraper
python3 engine/apify_scraper.py

# Test email automation
python3 engine/email_automation.py
```

### 4. Start Full Automation

```bash
# Option 1: Scheduler (runs every 4 hours)
python3 scheduler_v2.py

# Option 2: Run once immediately
python3 scheduler_v2.py --scrape-now
python3 scheduler_v2.py --email-now
```

### 5. (Optional) Start n8n

```bash
# Start n8n
./start_n8n.sh

# Open http://localhost:5678
# Import workflow: workflows/n8n_agency_os_integration.json
```

---

## 📊 What Happens Automatically

### Every 4 Hours:
1. **Scrape Reddit** → Gets [HIRING] posts
2. **Scrape Google Maps** → Gets software companies in Delhi/Mumbai/Bangalore
3. **Scrape LinkedIn Jobs** → Gets AI/automation job postings
4. **Add to leads.json** → Deduplicates and saves
5. **Telegram notification** → "📊 Scraped 45 new leads"

### Daily at 9 AM:
1. **Check lead status** → Finds NEW leads
2. **Send Day 0 email** → Initial cold email
3. **Check existing leads** → Sends Day 3/7 follow-ups
4. **Log everything** → email_automation_log.json
5. **Telegram report** → Summary of emails sent

### Daily at 8 AM:
1. **Morning brief** → Lead count, deal status
2. **Motivation** → "Let's crush it! 💪"

---

## 📧 Email Templates

### Day 0 (Initial)
```
Subject: quick question

Hi {first_name},

Saw {company} - congrats on the recent growth.

Quick question: Are you still handling {pain_point} manually?

We just helped a similar {industry} company automate their lead
generation and they saw 40% more qualified leads in 30 days.

Worth a quick look?

Raghav
```

### Day 3 (Follow-up)
```
Subject: Re: quick question

Hey {first_name},

In case this got buried - wanted to share exactly how we helped
a similar company...

[Case study + results]

Raghav
```

### Day 7 (Break-up)
```
Subject: should I close the loop?

{first_name},

No worries if timing's off - should I close this out for now?

Or if {pain_point} is still a thing, here's a 5-min Loom...

Raghav
```

---

## 📈 Revenue Tracking

### What Gets Tracked:
- Monthly revenue (₹50k goal)
- Deal pipeline stages
- Lead sources
- Email open/reply rates (future)

### Pipeline Stages:
1. **NEW** → Just scraped
2. **CONTACTED** → Day 0 email sent
3. **REPLIED** → Lead responded
4. **HOT_LEAD** → Interested
5. **PROPOSAL_SENT** → Proposal delivered
6. **CLOSED_WON** → Deal done! 💰
7. **CLOSED_LOST** → Didn't work out

---

## 🔌 Integration with Existing Agency OS

### Your Existing Files Still Work:
- `app.py` → Dashboard (unchanged)
- `pages/2_Leads.py` → Lead management (unchanged)
- `engine/lead_scraper.py` → Reddit scraper (unchanged)
- `engine/crm_system.py` → CRM (unchanged)
- `scheduler.py` → Old scheduler (keep for backup)

### New Files Add Power:
- `scheduler_v2.py` → New automation (use this)
- `engine/apify_scraper.py` → Google Maps/LinkedIn
- `engine/email_automation.py` → Email sequences

---

## 🐛 Troubleshooting

### "APIFY_TOKEN not set"
```bash
export APIFY_TOKEN=your_token_here
# Or add to ~/.zshrc
```

### "n8n not reachable"
```bash
# Start n8n
npx n8n start
# Then open http://localhost:5678
```

### "No emails sending"
- Check RESEND_API_KEY in `.env`
- Check GMAIL_USER and GMAIL_APP_PASSWORD
- Look at `data/email_automation_log.json` for errors

### "Telegram not working"
- Verify TELEGRAM_BOT_TOKEN
- Make sure you sent `/start` to @Rags1bot
- Check TELEGRAM_CHAT_ID is correct

---

## 💡 Pro Tips

1. **Start small**: Run `python3 scheduler_v2.py --test` first
2. **Monitor logs**: Check `data/email_automation_log.json`
3. **Update templates**: Edit `engine/email_automation.py` lines 18-60
4. **Add more cities**: Edit `apify_scraper.py` line 150-160
5. **Customize delays**: Change Day 3/7 in `email_automation.py` line 180

---

## 📞 Support

If something breaks:
1. Check logs in terminal
2. Look at JSON files in `data/` folder
3. Run with `--test` flag
4. Telegram me: @Rags1bot

---

**Built by RAGS** | ragspro.com | Last updated: 2026-04-02
