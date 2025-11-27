from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="Bot Admin Panel")

# Simple HTML response for the admin panel
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bot Admin Panel</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .card { border: 1px solid #ddd; padding: 20px; margin: 10px 0; border-radius: 5px; }
            .metric { font-size: 24px; font-weight: bold; color: #007bff; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Bot Admin Panel</h1>
            <div class="card">
                <h2>System Status</h2>
                <div class="metric">API Status: ✅ Healthy</div>
                <div class="metric">Database: SQLite</div>
            </div>
            <div class="card">
                <h2>Quick Actions</h2>
                <p><a href="/docs">API Documentation</a></p>
                <p><a href="/health">Health Check</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)