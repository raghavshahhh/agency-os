#!/bin/bash
# Start n8n for Agency OS automation

echo "🚀 Starting n8n..."
echo "=================="

# Check if npx is available
if ! command -v npx &> /dev/null; then
    echo "❌ npx not found. Install Node.js first:"
    echo "   brew install node"
    exit 1
fi

# Create n8n directory
mkdir -p ~/.n8n

# Set environment variables
export N8N_BASIC_AUTH_ACTIVE=true
export N8N_BASIC_AUTH_USER=ragspro
export N8N_BASIC_AUTH_PASSWORD=ragspro2025
export N8N_PORT=5678

echo "📱 n8n will be available at: http://localhost:5678"
echo "👤 Username: ragspro"
echo "🔑 Password: ragspro2025"
echo ""
echo "Starting n8n..."
echo ""

npx n8n start
