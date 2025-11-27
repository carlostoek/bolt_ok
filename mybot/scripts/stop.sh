#!/bin/bash
# Stop all services

if tmux has-session -t "bot-admin" 2>/dev/null; then
    echo "Stopping tmux session 'bot-admin'..."
    tmux kill-session -t bot-admin
    echo "Services stopped."
else
    echo "No tmux session 'bot-admin' found."
fi