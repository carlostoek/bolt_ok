"""
Utilidades para optimizar SQLite en entornos Termux

Funciones para:
- Habilitar WAL mode para mejor concurrencia
- Configurar PRAGMA para mejor rendimiento
- Función de vacuum automático
- Función de análisis de integridad
"""

import asyncio
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def enable_wal_mode(engine: AsyncEngine) -> bool:
    """
    Habilita el modo WAL (Write-Ahead Logging) para SQLite.
    Esto mejora significativamente la concurrencia permitiendo lecturas simultáneas
    mientras se realizan escrituras.
    
    Args:
        engine: Motor SQLAlchemy async
        
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        async with engine.connect() as conn:
            # Enable WAL mode
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            await conn.commit()
            logger.info("WAL mode enabled successfully")
            return True
    except Exception as e:
        logger.error(f"Failed to enable WAL mode: {e}")
        return False


async def optimize_sqlite_pragmas(engine: AsyncEngine, 
                                 cache_size: int = 2000,
                                 synchronous: str = "NORMAL",
                                 temp_store: str = "MEMORY",
                                 mmap_size: int = 268435456) -> bool:
    """
    Optimiza las configuraciones PRAGMA de SQLite para mejor rendimiento.
    
    Args:
        engine: Motor SQLAlchemy async
        cache_size: Tamaño del cache en páginas (4KB cada una por defecto)
        synchronous: Nivel de sincronización ('OFF', 'NORMAL', 'FULL')
        temp_store: Dónde almacenar archivos temporales ('MEMORY', 'FILE')
        mmap_size: Tamaño máximo para memory-mapped I/O en bytes
        
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        async with engine.connect() as conn:
            # Set cache size (default 2000 pages of 4KB each = 8MB)
            await conn.execute(text(f"PRAGMA cache_size={cache_size}"))
            
            # Set synchronous level (better performance with NORMAL vs FULL)
            await conn.execute(text(f"PRAGMA synchronous={synchronous}"))
            
            # Store temporary tables in memory
            await conn.execute(text(f"PRAGMA temp_store={temp_store}"))
            
            # Enable memory-mapped I/O
            await conn.execute(text(f"PRAGMA mmap_size={mmap_size}"))
            
            # Enable foreign key constraints
            await conn.execute(text("PRAGMA foreign_keys=ON"))
            
            # Set page size (can improve performance)
            await conn.execute(text("PRAGMA page_size=4096"))
            
            await conn.commit()
            logger.info("SQLite PRAGMAs optimized successfully")
            return True
    except Exception as e:
        logger.error(f"Failed to optimize SQLite pragmas: {e}")
        return False


async def auto_vacuum_database(engine: AsyncEngine, 
                              enable_auto_vacuum: bool = True) -> bool:
    """
    Configura o ejecuta la función VACUUM de SQLite.
    
    Args:
        engine: Motor SQLAlchemy async
        enable_auto_vacuum: Si True, activa auto_vacuum; si False, ejecuta VACUUM completo
        
    Returns:
        bool: True si la operación fue exitosa, False en caso contrario
    """
    try:
        async with engine.connect() as conn:
            if enable_auto_vacuum:
                # Enable auto-vacuum (INCREMENTAL is more efficient than FULL)
                await conn.execute(text("PRAGMA auto_vacuum=INCREMENTAL"))
                await conn.commit()
                logger.info("Auto-vacuum enabled")
            else:
                # Perform a full VACUUM operation
                await conn.execute(text("VACUUM"))
                await conn.commit()
                logger.info("Database vacuumed successfully")
            return True
    except Exception as e:
        logger.error(f"Failed to vacuum database: {e}")
        return False


async def integrity_check(engine: AsyncEngine) -> Optional[bool]:
    """
    Realiza una verificación de integridad de la base de datos SQLite.
    
    Args:
        engine: Motor SQLAlchemy async
        
    Returns:
        bool: True si la integridad es correcta, False si hay errores, None si hubo error en la operación
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("PRAGMA integrity_check"))
            integrity_result = result.fetchone()  # Remove await, fetchone() is sync in this context
            
            if integrity_result and integrity_result[0] == "ok":
                logger.info("Database integrity check passed")
                return True
            else:
                logger.warning(f"Database integrity check failed: {integrity_result[0] if integrity_result else 'Unknown error'}")
                return False
    except Exception as e:
        logger.error(f"Failed to perform integrity check: {e}")
        return None


async def optimize_sqlite_for_termux(engine: AsyncEngine) -> bool:
    """
    Aplica todas las optimizaciones recomendadas para SQLite en entornos Termux.
    
    Args:
        engine: Motor SQLAlchemy async
        
    Returns:
        bool: True si todas las optimizaciones se aplicaron correctamente, False en caso contrario
    """
    logger.info("Starting SQLite optimizations for Termux...")
    
    # Enable WAL mode
    wal_success = await enable_wal_mode(engine)
    if not wal_success:
        logger.error("Failed to enable WAL mode")
        return False
    
    # Optimize PRAGMAs
    pragmas_success = await optimize_sqlite_pragmas(engine)
    if not pragmas_success:
        logger.error("Failed to optimize PRAGMAs")
        return False
    
    # Enable auto-vacuum
    vacuum_success = await auto_vacuum_database(engine, enable_auto_vacuum=True)
    if not vacuum_success:
        logger.error("Failed to enable auto-vacuum")
        return False
    
    # Perform integrity check
    integrity_result = await integrity_check(engine)
    if integrity_result is False:
        logger.error("Database integrity check failed")
        return False
    
    logger.info("SQLite optimizations for Termux completed successfully")
    return True


async def cleanup_sqlite_logs(engine: AsyncEngine) -> bool:
    """
    Limpia logs y archivos temporales de SQLite que pueden acumularse.
    
    Args:
        engine: Motor SQLAlchemy async
        
    Returns:
        bool: True si la limpieza se realizó correctamente, False en caso contrario
    """
    try:
        async with engine.connect() as conn:
            # Clean up SQLite internal logs
            await conn.execute(text("PRAGMA shrink_memory"))  # Release unused memory
            await conn.commit()
            
            logger.info("SQLite memory cleaned up")
            return True
    except Exception as e:
        logger.error(f"Failed to clean up SQLite logs: {e}")
        return False


# Import text function for use in queries
from sqlalchemy import text