# RAGSPRO Agency System

Complete automation system for RAGSPRO agency.

## Features

- **Dashboard**: Full-featured Streamlit dashboard
- **Lead Management**: Add, track, filter leads
- **Client Management**: Track clients and projects
- **AI Content Generator**: LinkedIn, Twitter, Instagram, Blog
- **Email Outreach**: Generate personalized emails with Qwen
- **Analytics**: Track performance and generate reports
- **Automation**: Daily automated tasks

## Quick Start

```bash
# Start everything
./start.sh

# Or manually:
streamlit run dashboard/app.py
```

## Structure

```
RAGSPRO_AGENCY_SYSTEM/
├── config/
│   ├── settings.py      # All API keys and config
│   └── templates/        # Email/content templates
├── dashboard/
│   └── app.py           # Main Streamlit dashboard
├── workflows/
│   └── daily_automation.py  # Daily automation script
├── data/               # SQLite database (auto-created)
├── leads/              # Lead data (auto-created)
├── content/            # Generated content (auto-created)
├── reports/            # Reports (auto-created)
├── start.sh            # Start script
└── requirements.txt    # Python dependencies
```

## API Keys (Already Configured)

- NVIDIA NIM (Qwen) - Free & Unlimited
- Telegram Bot
- Gmail SMTP
- SerpAPI
- Tavily

## n8n Workflows

Import these workflows in n8n:
1. Open http://localhost:5678
2. Go to Workflows → Import from File
3. Import files from `n8nworkflow/` folder

## Commands

| Command | Description |
|---------|-------------|
| `./start.sh` | Start dashboard |
| `streamlit run dashboard/app.py` | Start dashboard manually |
| `python3 workflows/daily_automation.py` | Run daily automation |
| `n8n start` | Start n8n |

## Dashboard Pages

1. **Dashboard** - Overview, metrics, hot leads
2. **Leads** - Lead management
3. **Clients** - Client management
4. **Content Generator** - AI-powered content
5. **Email Outreach** - Generate emails
6. **Analytics** - Reports and insights
7. **Settings** - Configuration

## Telegram Bot

Send `/start` to @Rags1bot on Telegram for notifications.

---
Built by RAGS AI | ragspro.com