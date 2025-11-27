# Termux FastAPI + SQLAlchemy + Streamlit Setup

A complete setup script for deploying a bot administration panel in Termux/Android with FastAPI, SQLAlchemy, and Streamlit.

## Features

- **FastAPI** for REST API with async support
- **SQLAlchemy** with async support for database operations
- **Streamlit** for the web-based admin interface
- **SQLite** database with aiosqlite for async operations
- **Tmux** for process management
- **Virtual environment** optimized for mobile storage
- **Idempotent script** that can be run multiple times safely

## Prerequisites

- Android device with Termux installed
- Minimum 500MB free storage space
- Minimum 1GB RAM recommended
- Python 3.11+ (will be installed if not present)

## Installation

Since the automated setup encounters Rust compilation issues with newer Python packages, we'll set up the environment manually:

1. Create the project directory structure:
   ```bash
   mkdir -p ~/bot-admin-api/app/api/v1/endpoints ~/bot-admin-api/app/core ~/bot-admin-api/app/models ~/bot-admin-api/app/services ~/bot-admin-api/alembic ~/bot-admin-api/tests ~/bot-admin-api/scripts ~/bot-admin-api/logs ~/bot-admin-api/backups
   ```

2. Create the virtual environment:
   ```bash
   python -m venv ~/bot-admin-api/venv
   source ~/bot-admin-api/venv/bin/activate
   pip install --upgrade pip
   ```

3. Install essential packages (with compatible versions that don't require Rust compilation):
   ```bash
   pip install fastapi==0.104.1 uvicorn==0.24.0 sqlalchemy==2.0.23 aiosqlite==0.19.0 python-dotenv==1.0.0 alembic==1.12.1 requests==2.31.0 pydantic==1.10.13
   ```

4. Copy the configuration files to the project directory:
   ```bash
   cp .env.template ~/bot-admin-api/.env.template
   cp .gitignore ~/bot-admin-api/.gitignore
   ```

5. Create the management scripts:
   ```bash
   # Create start script
   cat > ~/bot-admin-api/scripts/start.sh << 'EOL'
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
   EOL

   # Create stop script
   cat > ~/bot-admin-api/scripts/stop.sh << 'EOL'
   #!/bin/bash
   # Stop all services

   if tmux has-session -t "bot-admin" 2>/dev/null; then
       echo "Stopping tmux session 'bot-admin'..."
       tmux kill-session -t bot-admin
       echo "Services stopped."
   else
       echo "No tmux session 'bot-admin' found."
   fi
   EOL

   # Create status script
   cat > ~/bot-admin-api/scripts/status.sh << 'EOL'
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
   EOL

   chmod +x ~/bot-admin-api/scripts/*.sh
   ```

6. Create the application files as provided in the repository

## Project Structure

```
~/bot-admin-api/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   ├── core/
│   ├── models/
│   ├── services/
│   ├── main.py          # FastAPI application
│   └── frontend.py      # Streamlit application
├── alembic/             # Database migrations
├── tests/
├── scripts/
│   ├── start.sh         # Start all services
│   ├── stop.sh          # Stop all services
│   └── status.sh        # Check service status
├── logs/
├── backups/
├── venv/                # Virtual environment
├── requirements.txt
├── .env.template
├── .gitignore
└── README.md
```

## Configuration

1. Copy the environment template:
   ```bash
   cd ~/bot-admin-api
   cp .env.template .env
   ```

2. Edit the `.env` file with your configuration:
   ```bash
   nano .env
   ```

   - Set your Telegram bot token
   - Configure database settings
   - Update security settings

## Starting the Services

1. Activate the virtual environment:
   ```bash
   source ~/bot-admin-api/venv/bin/activate
   ```

2. Start all services using the provided script:
   ```bash
   ~/bot-admin-api/scripts/start.sh
   ```

   This creates a tmux session with:
   - Window 0: FastAPI server (port 8000)
   - Window 1: Streamlit frontend (port 8501)
   - Window 2: Service logs

3. Connect to the tmux session:
   ```bash
   tmux attach -t bot-admin
   ```

4. Access the services:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/health
   - Streamlit: http://localhost:8501

## Managing Services

- Check status: `~/bot-admin-api/scripts/status.sh`
- Stop services: `~/bot-admin-api/scripts/stop.sh`
- View logs: `tail -f ~/bot-admin-api/logs/api.log`

## Customization

### FastAPI Application

The main FastAPI app is in `~/bot-admin-api/app/main.py`. Add your endpoints in the `app/api/v1/endpoints/` directory.

### Streamlit Interface

The Streamlit frontend is in `~/bot-admin-api/app/frontend.py`. Customize the admin panel according to your needs.

### Database Models

Add your SQLAlchemy models in `~/bot-admin-api/app/models/` directory.

## Troubleshooting

### Common Issues

1. **Insufficient Storage**: Ensure you have at least 500MB free space before running the script.

2. **Permission Errors**: Run the script in your Termux home directory with proper write permissions.

3. **Python Version**: The script automatically installs Python 3.11+ if not present.

4. **Package Installation Issues**: If a package fails to install, try updating your package lists:
   ```bash
   pkg update && pkg upgrade
   ```

### Manual Steps if Setup Fails

If the script fails at any point, you can perform the steps manually:

1. Install system dependencies:
   ```bash
   pkg update
   pkg install python git tmux sqlite build-essential rust
   # Install additional packages as needed
   pkg install libffi openssl zlib libxml2 libxslt libjpeg-turbo freetype lcms2 tiff tk tcl
   ```

2. Create virtual environment:
   ```bash
   python -m venv ~/bot-admin-api/venv
   source ~/bot-admin-api/venv/bin/activate
   pip install --upgrade pip
   ```

3. Install Python packages:
   ```bash
   pip install fastapi uvicorn sqlalchemy aiosqlite asyncpg streamlit python-dotenv alembic pydantic pydantic-settings
   ```

## Architecture Details

- **FastAPI**: Built with async/await for optimal performance in resource-constrained environments
- **SQLAlchemy**: Async session handling with connection pooling (5 connections)
- **Uvicorn**: Single worker configuration optimized for mobile resources
- **Streamlit**: Lightweight web interface for admin panel
- **Tmux**: Process management without requiring systemd
- **SQLite**: Embedded database with minimal overhead

## Security Considerations

- Change the default SECRET_KEY in `.env`
- Consider using HTTPS in production
- Validate all user inputs
- Regular updates of dependencies
- Use environment variables for sensitive data

## Performance Optimization

The setup is optimized for mobile devices:
- Minimal virtual environment (no unnecessary packages)
- Limited database connection pool
- Single Uvicorn worker
- Lightweight database (SQLite)
- Efficient logging configuration