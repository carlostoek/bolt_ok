"""
FastAPI Application - Bot Admin Panel

Punto de entrada principal de la aplicación.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación.

    Ejecuta código al iniciar y cerrar la aplicación:
    - Startup: Inicializa la base de datos
    - Shutdown: Cierra conexiones de BD
    """
    # Startup
    print("🚀 Iniciando aplicación...")
    await init_db()
    print("✅ Base de datos inicializada")

    yield

    # Shutdown
    print("🛑 Cerrando aplicación...")
    await close_db()
    print("✅ Conexiones cerradas")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Endpoint raíz - Health check."""
    return {
        "message": "Bot Admin Panel API",
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Endpoint de health check."""
    return {"status": "healthy"}


# Los routers se agregarán aquí cuando se implementen los endpoints
# Ejemplo:
# from app.api.v1.endpoints import narrative, shop
# app.include_router(narrative.router, prefix=settings.API_V1_PREFIX, tags=["narrative"])
# app.include_router(shop.router, prefix=settings.API_V1_PREFIX, tags=["shop"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
