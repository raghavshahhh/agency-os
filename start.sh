#!/bin/bash
# RAGSPRO Agency System - Start Script

echo "🚀 Starting RAGSPRO Agency System..."

cd "$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python."
    exit 1
fi

# Check Streamlit
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "📦 Installing Streamlit..."
    pip3 install streamlit pandas requests --break-system-packages
fi

# Create data directory
mkdir -p data leads content reports config/templates

# Load API keys from .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo ""
echo "${GREEN}✅ RAGSPRO Agency System Ready!${NC}"
echo ""
echo "📋 Commands:"
echo "  1) Dashboard:   ${BLUE}streamlit run dashboard/app.py${NC}"
echo "  2) Automation:  ${BLUE}python3 workflows/daily_automation.py${NC}"
echo "  3) n8n:         ${BLUE}n8n start${NC}"
echo ""
echo "🌐 Opening Dashboard..."
echo ""

# Start Streamlit dashboard
streamlit run dashboard/app.py --server.port 8501