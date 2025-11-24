"""
FastAPI Application - Bot Admin Panel

Punto de entrada principal de la aplicación.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import init_db, close_db
from app.api.v1.endpoints import narrative

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestión del ciclo de vida de la aplicación.

    Ejecuta código al iniciar y cerrar la aplicación:
    - Startup: Inicializa la base de datos
    - Shutdown: Cierra conexiones de BD
    """
    # Startup
    logger.info("🚀 Iniciando aplicación Bot Admin Panel...")
    logger.info(f"Versión: {settings.VERSION}")
    logger.info(f"Modo Debug: {settings.DEBUG}")
    await init_db()
    logger.info("✅ Base de datos inicializada")

    yield

    # Shutdown
    logger.info("🛑 Cerrando aplicación...")
    await close_db()
    logger.info("✅ Conexiones cerradas")


# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    description="""
    Panel de Administración para Bot de Telegram.

    ## Características

    - ✅ Atomic Nested Creation - Crea múltiples entidades relacionadas en una sola petición
    - ✅ Gestión de fragmentos narrativos con decisiones
    - ✅ Sistema de tienda con productos que desbloquean contenido
    - ✅ Transacciones atómicas - Todo se crea o nada
    - ✅ Sin necesidad de copy-paste de IDs entre entidades

    ## Documentación Técnica

    - [OpenAPI Docs](/docs)
    - [ReDoc](/redoc)
    """
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
    return {
        "status": "healthy",
        "service": "Bot Admin Panel",
        "version": settings.VERSION
    }


# ============================================================================
# INCLUIR ROUTERS DE ENDPOINTS
# ============================================================================

# Router de Narrativa - Sistema de fragmentos y decisiones
app.include_router(
    narrative.router,
    prefix=f"{settings.API_V1_PREFIX}/narrative",
    tags=["Narrative"],
    responses={
        404: {"description": "Fragmento no encontrado"},
        409: {"description": "Key duplicada"},
        500: {"description": "Error interno del servidor"}
    }
)

logger.info("✅ Router de Narrativa registrado en /api/v1/narrative")

# Router de Tienda
from app.api.v1.endpoints import shop
app.include_router(
    shop.router,
    prefix=f"{settings.API_V1_PREFIX}/shop",
    tags=["Shop"]
)

# Router de Automatización
from app.api.v1.endpoints import automation
app.include_router(
    automation.router,
    prefix=f"{settings.API_V1_PREFIX}/automation",
    tags=["Automation"]
)

# Router de Usuarios
from app.api.v1.endpoints import users
app.include_router(
    users.router,
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["Users"]
)

# Router de Lore
from app.api.v1.endpoints import lore
app.include_router(
    lore.router,
    prefix=f"{settings.API_V1_PREFIX}/lore",
    tags=["Lore"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
