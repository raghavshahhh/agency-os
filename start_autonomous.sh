#!/bin/bash
# RAGSPRO Autonomous Agent Launcher

cd "$(dirname "$0")"

echo "🚀 Starting RAGSPRO Autonomous Agent..."
echo "======================================"

# Check if already running
if pgrep -f "autonomous_agent.py" > /dev/null; then
    echo "⚠️  Agent already running!"
    echo "Run: pkill -f 'autonomous_agent.py' to stop"
    exit 1
fi

# Create nohup log
mkdir -p logs
LOG_FILE="logs/agent_$(date +%Y%m%d_%H%M%S).log"

# Start agent with nohup
nohup .venv/bin/python3 engine/autonomous_agent.py > "$LOG_FILE" 2>&1 &
AGENT_PID=$!

echo "✅ Agent started with PID: $AGENT_PID"
echo "📁 Log file: $LOG_FILE"
echo ""
echo "Commands:"
echo "  tail -f $LOG_FILE     # View logs"
echo "  cat data/agent_stats.json    # View stats"
echo "  pkill -f 'autonomous_agent.py'  # Stop agent"
echo ""
echo "Telegram notifications enabled"
echo "Agent will run 24/7 until stopped"

# Save PID
echo $AGENT_PID > .agent_pid
