# Getting Started with Bot Admin Panel

## Environment Setup

Your environment is already set up with the following:

### Core Technologies
- Python 3.12.12 
- FastAPI 0.104.1
- SQLAlchemy 2.0.23 (async)
- Aiosqlite 0.19.0
- Uvicorn 0.24.0
- Pydantic 1.10.24
- Alembic 1.12.1

### Directory Structure
```
$HOME/bot-admin-api/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   ├── core/
│   ├── models/
│   ├── services/
│   ├── main.py          # Main API server
│   └── frontend.py      # Basic HTML frontend
├── alembic/             # Database migrations
├── tests/
├── scripts/
│   ├── start.sh         # Start services in tmux
│   ├── stop.sh          # Stop services
│   └── status.sh        # Check service status
├── logs/
├── backups/
├── venv/                # Virtual environment
├── .env.template        # Environment variables template
└── README.md
```

## Usage

### 1. Activate the environment
```bash
source $HOME/bot-admin-api/venv/bin/activate
```

### 2. Configure environment variables
```bash
cd $HOME/bot-admin-api
cp .env.template .env
# Edit .env with your values
nano .env  # or use your preferred editor
```

### 3. Run the API server directly
```bash
cd $HOME/bot-admin-api/app
uvicorn main:app --reload
```

### 4. Run the frontend directly
```bash
cd $HOME/bot-admin-api/app
uvicorn frontend:app --reload --port 8001
```

### 5. Use management scripts (recommended)
```bash
# Start all services in tmux
$HOME/bot-admin-api/scripts/start.sh

# Check status
$HOME/bot-admin-api/scripts/status.sh

# Connect to tmux session to view logs
tmux attach -t bot-admin

# Stop all services
$HOME/bot-admin-api/scripts/stop.sh
```

## Available Endpoints

### API Server (port 8000)
- `GET /` - Main API endpoint
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

### Frontend Server (port 8001)
- `GET /` - Basic HTML admin panel
- `GET /health` - Health check

## Adding More Functionality

### Add Database Models
Create new files in `$HOME/bot-admin-api/app/models/`:

```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
```

### Add API Endpoints
Create new files in `$HOME/bot-admin-api/app/api/v1/endpoints/` and import them in your main.py.

## Troubleshooting

### If you get import errors
Make sure you've activated the virtual environment:
```bash
source $HOME/bot-admin-api/venv/bin/activate
```

### If services won't start
Check that tmux is installed:
```bash
pkg install tmux
```

### For database migrations
```bash
cd $HOME/bot-admin-api
source venv/bin/activate
# Create migration
alembic revision --autogenerate -m "Migration message"
# Apply migration
alembic upgrade head
```

## Important Notes

- This setup uses SQLite as the default database (file-based)
- For production, consider PostgreSQL with asyncpg
- The current setup avoids packages requiring Rust compilation for compatibility
- Streamlit was excluded due to compilation requirements in Termux
- The basic HTML frontend can be replaced with a more sophisticated front-end later