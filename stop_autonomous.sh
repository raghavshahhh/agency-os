#!/bin/bash
# Stop RAGSPRO Autonomous Agent

if [ -f .agent_pid ]; then
    PID=$(cat .agent_pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        echo "✅ Agent stopped (PID: $PID)"
    else
        echo "⚠️  Agent not running"
    fi
    rm .agent_pid
else
    pkill -f "autonomous_agent.py"
    echo "✅ Agent stopped"
fi
