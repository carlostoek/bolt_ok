#!/usr/bin/env python3
"""
Script para inicializar la narrativa por defecto.
"""
import asyncio
import os
import sys

# Añadir la raíz del proyecto al sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from mybot.database.setup import init_db, get_session_factory
from mybot.services.narrative_loader import NarrativeLoader

async def main():
    """Inicializar base de datos y cargar narrativa."""
    print("🔧 Inicializando base de datos...")
    await init_db()
    
    print("📚 Cargando narrativa...")
    session_factory = get_session_factory()
    async with session_factory() as session:
        loader = NarrativeLoader(session)
        
        # Cargar desde directorio de fragmentos
        await loader.load_fragments_from_directory("mybot/narrative_fragments")
        
        # Cargar narrativa por defecto si no hay fragmentos
        await loader.load_default_narrative()
    
    print("✅ Narrativa inicializada correctamente!")

if __name__ == "__main__":
    asyncio.run(main())
