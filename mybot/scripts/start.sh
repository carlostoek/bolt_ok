#!/bin/bash
# Start all services in tmux sessions

# Check if virtual environment exists
if [ ! -d "$HOME/bot-admin-api/venv" ]; then
    echo "Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source $HOME/bot-admin-api/venv/bin/activate

# Create tmux session if it doesn't exist
if ! tmux has-session -t "bot-admin" 2>/dev/null; then
    echo "Creating tmux session for bot-admin services..."
    
    # Create new session in detached mode
    tmux new-session -d -s bot-admin
    
    # Create a window for the API server
    tmux send-keys -t bot-admin 'cd $HOME/bot-admin-api/app && python -m uvicorn main:app --host 0.0.0.0 --port 8000' C-m
    
    # Create a new window for the frontend (if we add one later)
    tmux new-window -t bot-admin
    tmux send-keys -t bot-admin:1 'cd $HOME/bot-admin-api/app && python -m uvicorn frontend:app --host 0.0.0.0 --port 8001' C-m
    
    # Create a new window for logs
    tmux new-window -t bot-admin
    tmux send-keys -t bot-admin:2 'tail -f $HOME/bot-admin-api/logs/api.log' C-m
    
    echo "Services started in tmux session 'bot-admin'"
    echo "Connect with: tmux attach -t bot-admin"
else
    echo "Tmux session 'bot-admin' already exists. Attach with: tmux attach -t bot-admin"
fi