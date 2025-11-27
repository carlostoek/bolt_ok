#!/bin/bash

# FastAPI + SQLAlchemy + Streamlit Setup for Termux/Android
# Author: DevOps Senior Engineer
# Description: Complete setup script for bot admin panel in Termux

set -e  # Exit on any error

# ANSI color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Global variables
INSTALL_DIR="$HOME/bot-admin-api"
VENV_DIR="$INSTALL_DIR/venv"
LOG_DIR="$INSTALL_DIR/logs"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check system compatibility
check_system_compatibility() {
    log_info "Checking system compatibility..."

    # Check if we're in Termux
    if [ -z "$TERMUX_VERSION" ]; then
        log_warn "This script is designed for Termux. Running on regular Linux/Unix system may not work as expected."
    fi

    # Check Python version
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')
        log_info "Python version: $PYTHON_VERSION"
        
        # Check if Python version is 3.11 or higher
        if [ "$(printf '%s\n' "3.11" "$PYTHON_VERSION" | sort -V | head -n1)" = "3.11" ]; then
            log_success "Python version is compatible (3.11+)"
        else
            log_error "Python version is too old. Required: 3.11+, Found: $PYTHON_VERSION"
            log_info "Installing Python 3.11+ via pkg..."
            pkg install python -y
        fi
    else
        log_error "Python3 not found. Installing..."
        pkg install python -y
    fi

    # Check available disk space
    AVAILABLE_SPACE=$(df "$HOME" | awk 'NR==2 {print $4}' | numfmt --to=iec)
    AVAILABLE_SPACE_KB=$(df "$HOME" | awk 'NR==2 {print $4}')
    
    log_info "Available disk space: $AVAILABLE_SPACE"
    
    if [ "$AVAILABLE_SPACE_KB" -lt 512000 ]; then  # 500MB in KB
        log_error "Insufficient disk space. Required: ~500MB, Available: $AVAILABLE_SPACE_KB KB"
        log_info "Please free up space or consider using external storage."
        exit 1
    else
        log_success "Sufficient disk space available"
    fi

    # Check available RAM
    if [ -f /proc/meminfo ]; then
        TOTAL_RAM=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        AVAILABLE_RAM=$(grep MemAvailable /proc/meminfo | awk '{print $2}')
        
        log_info "RAM - Total: $(($TOTAL_RAM / 1024))MB, Available: $(($AVAILABLE_RAM / 1024))MB"
        
        if [ "$AVAILABLE_RAM" -lt 512000 ]; then  # 500MB in KB
            log_warn "Low available RAM. System performance may be affected."
        else
            log_success "Sufficient RAM available"
        fi
    else
        log_warn "/proc/meminfo not found, skipping RAM check"
    fi

    log_success "System compatibility check completed"
}

# Function to install system dependencies
install_system_dependencies() {
    log_info "Installing system dependencies..."

    # Update package lists
    log_info "Updating package lists..."
    pkg update -y

    # Install required packages with Termux-specific names
    # Split into essential and optional packages for better error handling
    essential_packages=("python" "git" "tmux" "sqlite")

    log_info "Installing essential packages..."
    for package in "${essential_packages[@]}"; do
        if pkg list-installed 2>/dev/null | grep -q "^${package}"; then
            log_info "$package is already installed"
        else
            log_info "Installing $package..."
            if pkg install "$package" -y; then
                log_success "$package installed successfully"
            else
                log_error "Failed to install essential package $package"
                exit 1
            fi
        fi
    done

    # Install build essentials
    log_info "Installing build essentials..."
    build_packages=("build-essential" "libffi-dev" "openssl-dev")
    for package in "${build_packages[@]}"; do
        if pkg list-installed 2>/dev/null | grep -q "^${package}"; then
            log_info "$package is already installed"
        else
            log_info "Installing $package..."
            # Handle packages that might not be available in Termux
            if pkg install "$package" -y; then
                log_success "$package installed successfully"
            else
                # Handle case where -dev packages don't exist in Termux
                if [ "$package" = "libffi-dev" ]; then
                    log_warn "libffi-dev not available, trying 'libffi'"
                    if pkg install "libffi" -y; then
                        log_success "libffi installed as alternative to libffi-dev"
                    else
                        log_warn "Could not install libffi"
                    fi
                elif [ "$package" = "openssl-dev" ]; then
                    log_warn "openssl-dev not available, trying 'openssl'"
                    if pkg install "openssl" -y; then
                        log_success "openssl installed as alternative to openssl-dev"
                    else
                        log_warn "Could not install openssl"
                    fi
                else
                    log_warn "Could not install $package, continuing..."
                fi
            fi
        fi
    done

    # Install additional development packages that may be needed for Python packages
    additional_packages=("rust" "pkg-config" "zlib" "libxml2" "libxslt" "libjpeg-turbo" "freetype" "lcms2" "tiff" "tk" "tcl")
    log_info "Installing additional packages..."
    for package in "${additional_packages[@]}"; do
        if pkg list-installed 2>/dev/null | grep -q "^${package}"; then
            log_info "$package is already installed"
        else
            log_info "Installing $package..."
            if pkg install "$package" -y; then
                log_success "$package installed successfully"
            else
                log_warn "Could not install $package, continuing (this package might not be required)..."
            fi
        fi
    done

    # Check if pip is available
    if command_exists pip3; then
        log_success "pip3 is available"
    else
        log_error "pip3 not found after installation"
        exit 1
    fi

    log_success "System dependencies installation completed"
}

# Function to create directory structure
create_directory_structure() {
    log_info "Creating directory structure..."
    
    # Create main directories
    mkdir -p "$INSTALL_DIR"/{app,alembic,tests,scripts,logs,backups}
    mkdir -p "$INSTALL_DIR"/app/{api,core,models,services}
    mkdir -p "$INSTALL_DIR"/app/api/v1/{endpoints,models,schemas}
    mkdir -p "$LOG_DIR"
    
    log_success "Directory structure created at $INSTALL_DIR"
}

# Function to set up virtual environment
setup_virtual_environment() {
    log_info "Setting up virtual environment..."
    
    # Create virtual environment (optimized for space)
    python3 -m venv "$VENV_DIR" --without-pip
    log_info "Virtual environment created at $VENV_DIR (without pip to save space)"
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Install pip in the virtual environment
    log_info "Installing pip in virtual environment..."
    curl https://bootstrap.pypa.io/get-pip.py | python3
    
    # Verify pip installation
    if command_exists pip; then
        log_success "pip installed in virtual environment"
    else
        log_error "Failed to install pip in virtual environment"
        exit 1
    fi
    
    # Upgrade pip
    pip install --upgrade pip
    
    log_success "Virtual environment setup completed"
}

# Function to install Python packages
install_python_packages() {
    log_info "Installing Python packages..."
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Create requirements.txt content with legacy versions that have pre-compiled wheels
    cat > "$INSTALL_DIR/requirements.txt" << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
aiosqlite==0.19.0
python-multipart==0.0.6
python-dotenv==1.0.0
alembic==1.12.1
pydantic==1.10.13
requests==2.31.0
EOF

    # Install packages
    if pip install -r "$INSTALL_DIR/requirements.txt"; then
        log_success "Python packages installed successfully"
    else
        log_error "Failed to install Python packages"
        exit 1
    fi
    
    # Create a basic FastAPI app template
    cat > "$INSTALL_DIR/app/main.py" << 'EOF'
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Database setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="Bot Admin Panel API",
    description="API for managing bot administration",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {"message": "Bot Admin Panel API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
EOF

    # Create config file
    mkdir -p "$INSTALL_DIR/app/core"
    cat > "$INSTALL_DIR/app/core/config.py" << 'EOF'
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./bot_database.db"
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    telegram_bot_token: Optional[str] = None

    class Config:
        env_file = ".env"

settings = Settings()
EOF

    log_success "Basic FastAPI app structure created"
}

# Function to create configuration files
create_configuration_files() {
    log_info "Creating configuration files..."
    
    # Create .env.template
    cat > "$INSTALL_DIR/.env.template" << 'EOF'
# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./bot_database.db
# Alternative: DATABASE_URL=postgresql+asyncpg://user:password@localhost/dbname

# API Configuration
HOST=127.0.0.1
PORT=8000

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Security Configuration
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Configuration
DEBUG=false
LOG_LEVEL=info
EOF

    # Create .gitignore
    cat > "$INSTALL_DIR/.gitignore" << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Environment
.env
.env.local
.env.production
.env.development

# Database
*.db
*.db-journal

# OS
.DS_Store
Thumbs.db

# Streamlit
.streamlit/
EOF

    # Create basic README
    cat > "$INSTALL_DIR/README.md" << 'EOF'
# Bot Admin Panel API

A FastAPI + SQLAlchemy + Streamlit administration panel for Telegram bot management.

## Setup

1. Copy `.env.template` to `.env` and update with your configuration:
   ```bash
   cp .env.template .env
   # Edit .env with your values
   ```

2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

3. Run the API server:
   ```bash
   cd app
   uvicorn main:app --reload
   ```

4. Run the Streamlit frontend:
   ```bash
   cd app
   streamlit run frontend.py
   ```

## Architecture

- FastAPI backend on port 8000
- Streamlit frontend on port 8501
- SQLite database by default
- Async SQLAlchemy for database operations

## Management

- Check logs: `tail -f logs/api.log`
- Restart services: `tmux kill-server && ./scripts/start.sh`
EOF

    # Create basic Streamlit app
    cat > "$INSTALL_DIR/app/frontend.py" << 'EOF'
import streamlit as st

st.set_page_config(
    page_title="Bot Admin Panel",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Bot Admin Panel")
st.markdown("### Administration Dashboard for Telegram Bot")

col1, col2 = st.columns(2)

with col1:
    st.header("Bot Status")
    st.metric(label="Active Users", value="1,234", delta="+12")
    st.metric(label="Messages Processed", value="5,678", delta="+45")

with col2:
    st.header("System Status")
    st.metric(label="API Status", value="✅ Healthy")
    st.metric(label="Database", value="SQLite", delta="Connected")

st.header("Recent Activities")
st.write("No activities to display yet.")
EOF

    # Create management scripts
    mkdir -p "$INSTALL_DIR/scripts"
    
    cat > "$INSTALL_DIR/scripts/start.sh" << 'EOF'
#!/bin/bash
# Start all services in tmux sessions

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Create tmux session if it doesn't exist
if ! tmux has-session -t "bot-admin" 2>/dev/null; then
    echo "Creating tmux session for bot-admin services..."
    
    # Create new session in detached mode
    tmux new-session -d -s bot-admin
    
    # Create a window for the API server
    tmux send-keys -t bot-admin 'cd app && uvicorn main:app --host 0.0.0.0 --port 8000' C-m
    
    # Create a new window for Streamlit
    tmux new-window -t bot-admin
    tmux send-keys -t bot-admin:1 'cd app && streamlit run frontend.py --server.address 0.0.0.0 --server.port 8501' C-m
    
    # Create a new window for logs
    tmux new-window -t bot-admin
    tmux send-keys -t bot-admin:2 'tail -f logs/api.log' C-m
    
    echo "Services started in tmux session 'bot-admin'"
    echo "Connect with: tmux attach -t bot-admin"
else
    echo "Tmux session 'bot-admin' already exists. Attach with: tmux attach -t bot-admin"
fi
EOF

    cat > "$INSTALL_DIR/scripts/stop.sh" << 'EOF'
#!/bin/bash
# Stop all services

if tmux has-session -t "bot-admin" 2>/dev/null; then
    echo "Stopping tmux session 'bot-admin'..."
    tmux kill-session -t bot-admin
    echo "Services stopped."
else
    echo "No tmux session 'bot-admin' found."
fi
EOF

    cat > "$INSTALL_DIR/scripts/status.sh" << 'EOF'
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
EOF

    # Make scripts executable
    chmod +x "$INSTALL_DIR/scripts/start.sh"
    chmod +x "$INSTALL_DIR/scripts/stop.sh" 
    chmod +x "$INSTALL_DIR/scripts/status.sh"

    log_success "Configuration files created"
}

# Function to calculate installation size
calculate_installation_size() {
    log_info "Calculating installation size..."
    
    if command_exists du; then
        SIZE=$(du -sh "$INSTALL_DIR" 2>/dev/null | cut -f1)
        log_info "Installation size: $SIZE"
    else
        log_warn "du command not available, skipping size calculation"
    fi
}

# Main execution function
main() {
    log_info "Starting FastAPI + SQLAlchemy + Streamlit setup for Termux..."
    log_info "Target directory: $INSTALL_DIR"
    
    # Create the installation directory if it doesn't exist
    mkdir -p "$INSTALL_DIR"
    
    # Execute setup steps
    check_system_compatibility
    install_system_dependencies
    create_directory_structure
    setup_virtual_environment
    install_python_packages
    create_configuration_files
    calculate_installation_size
    
    log_success "Setup completed successfully!"
    log_info "Installation directory: $INSTALL_DIR"
    log_info "Virtual environment: $VENV_DIR" 
    log_info ""
    log_info "Next steps:"
    log_info "1. cd $INSTALL_DIR"
    log_info "2. cp .env.template .env"
    log_info "3. Edit .env with your configuration"
    log_info "4. source $VENV_DIR/bin/activate"
    log_info "5. Run services with: ./scripts/start.sh"
    log_info ""
    log_info "For more information, check the README.md file."
}

# Run main function
main "$@"