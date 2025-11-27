#!/bin/bash
# Check service status

if tmux has-session -t "bot-admin" 2>/dev/null; then
    echo "Services are running in tmux session 'bot-admin':"
    tmux ls -f '#{session_attached} #{session_name}' | grep -q 'bot-admin' && echo "  - Session is attached" || echo "  - Session is detached"
    echo "To view: tmux attach -t bot-admin"
    echo "To stop: ./scripts/stop.sh"
else
    echo "No services are currently running."
    echo "Start with: ./scripts/start.sh"
fi