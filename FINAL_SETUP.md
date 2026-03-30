# Agency OS - Final Setup Guide

## ✅ Already Completed (All Phases)

### Phase 1-4: Core Features
- ✅ Lead scraper fixed - only [HIRING] posts
- ✅ Telegram bot configured (Chat ID: 1451671418)
- ✅ Resend email API working
- ✅ Pagination (25 leads/page)
- ✅ Password protection: `ragspro2025`
- ✅ Advanced email templates (AIDA framework)
- ✅ 183 real leads in database
- ✅ Bulk email sender added
- ✅ Auto-scheduler created
- ✅ n8n connector ready
- ✅ LinkedIn scraper ready

---

## 🚀 Step-by-Step: Start Everything

### Step 1: Start Dashboard (Terminal 1)
```bash
cd ~/Desktop/Agency\ OS
streamlit run app.py
```
- Open: http://localhost:8501
- Password: `ragspro2025`

### Step 2: Test Bulk Email
1. Go to **Leads** page
2. Expand **"📤 Bulk Email Actions"**
3. Click **"🚀 Generate & Send to X Leads"**
4. Emails will auto-send to new leads

### Step 3: Start n8n (Terminal 2)
```bash
# Option A: Using npx
npx n8n start

# Option B: Using Docker
docker run -it --rm --name n8n -p 5678:5678 -v ~/.n8n:/home/node/.n8n n8nio/n8n
```
- Open: http://localhost:5678
- Login: `ragspro` / `ragspro2025`

### Step 4: Import Workflows (in n8n)
1. Settings → Import Workflow
2. Upload: `workflows/n8n_lead_scraper.json`
3. Activate workflow

### Step 5: Start Auto-Scheduler (Terminal 3)
```bash
cd ~/Desktop/Agency\ OS
python3 scheduler.py
```
- Scrapes every 6 hours
- Sends daily report at 9 AM

---

## 📊 Current Status

| Feature | Status | Location |
|---------|--------|----------|
| Dashboard | ✅ Ready | localhost:8501 |
| Leads | ✅ 183 real | data/leads.json |
| Email | ✅ Working | Test in Leads page |
| Telegram | ✅ Configured | Chat ID: 1451671418 |
| n8n | ⏳ Needs start | localhost:5678 |
| Scheduler | ⏳ Needs start | scheduler.py |

---

## 🎯 Quick Commands

```bash
# Start everything
alias agos="cd ~/Desktop/Agency\ OS && streamlit run app.py"

# Scrape leads manually
python3 engine/lead_scraper.py

# Test email
python3 test_email.py

# Test telegram
python3 test_telegram.py

# Get chat ID
python3 get_telegram_chat_id.py

# Start scheduler
python3 scheduler.py
```

---

## 🆘 Troubleshooting

### n8n not starting?
```bash
# Install n8n first
npm install -g n8n

# Or use Docker
docker run -p 5678:5678 n8nio/n8n
```

### Bulk email not working?
1. Check Leads page has "NEW" leads with emails
2. Verify Resend API key in `.env`
3. Check `test_email.py` works first

### No Telegram notifications?
1. Message @ragspro_bot first
2. Run `python3 get_telegram_chat_id.py`
3. Verify `.env` has TELEGRAM_CHAT_ID=1451671418

---

## ✅ Test Checklist

- [ ] Dashboard opens with password `ragspro2025`
- [ ] Leads page shows 183 leads
- [ ] Bulk email sends to test leads
- [ ] n8n starts at localhost:5678
- [ ] Telegram bot sends test message
- [ ] Scheduler runs without errors

**Sab kuch ready hai!**
