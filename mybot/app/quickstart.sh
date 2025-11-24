#!/bin/bash

# Quick Start Script para el Panel de Administración
# Este script configura e inicia la aplicación FastAPI

set -e

echo "🚀 Iniciando Panel de Administración del Bot..."
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py no encontrado. Ejecuta este script desde app/"
    exit 1
fi

# Instalar dependencias
echo "📦 Instalando dependencias..."
pip install -r requirements.txt

echo ""
echo "✅ Dependencias instaladas"
echo ""

# Verificar archivo .env
if [ ! -f "../.env" ]; then
    echo "⚠️  Advertencia: No se encontró archivo .env"
    echo "   Creando .env con valores por defecto..."
    cat > ../.env << EOF
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/botdb

# API
API_V1_PREFIX=/api/v1
PROJECT_NAME=Bot Admin Panel
DEBUG=true

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]

# Security
SECRET_KEY=development-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# SQLAlchemy
POOL_SIZE=5
MAX_OVERFLOW=10
ECHO_SQL=true
EOF
    echo "   ✅ .env creado (revisa y ajusta DATABASE_URL)"
fi

echo ""
echo "🎯 Iniciando servidor FastAPI..."
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   Health: http://localhost:8000/health"
echo ""

# Iniciar con uvicorn
python main.py
