#!/bin/bash

# setup.sh - Script de configuración inicial del entorno de desarrollo

set -e  # Salir inmediatamente si un comando falla

echo "🚀 Iniciando configuración del entorno de desarrollo..."

# Verificar si estamos en Termux (Android)
if [ -d "/data/data/com.termux/files/usr" ]; then
    echo "📱 Detectado entorno Termux (Android)"
    # Actualizar paquetes en Termux
    pkg update -y
    # Instalar dependencias del sistema necesarias
    pkg install -y python python-pip git
fi

# Verificar si poetry está instalado
if ! command -v poetry &> /dev/null
then
    echo "📦 Instalando Poetry..."
    pip install poetry
else
    echo "✅ Poetry ya está instalado"
fi

# Instalar dependencias con Poetry
echo "🔧 Instalando dependencias del proyecto..."
poetry install

# Crear base de datos si no existe
echo "🗄️ Configurando base de datos..."
# Esto creará la base de datos cuando se inicie la aplicación

# Ejecutar migraciones si existen
# Si tienes migraciones, descomenta la siguiente línea:
# poetry run alembic upgrade head

echo "🧪 Verificando configuración de tests..."
poetry run pytest --version

# Crear un archivo .env con la configuración básica si no existe
if [ ! -f ".env" ]; then
    echo "Creando archivo .env..."
    cat > .env << EOF
# Configuración básica para desarrollo
PYTHONPATH=$(pwd)
DATABASE_URL=sqlite+aiosqlite:///telegram_bot.db
TEST_DATABASE_URL=sqlite+aiosqlite:///:memory:
TESTING=True
DEBUG=True
EOF
    echo "Archivo .env creado con configuración básica."
fi

echo "✅ Configuración completada exitosamente!"

echo "
📝 Instrucciones:
- Para activar el entorno: poetry shell
- Para ejecutar tests: ./test.sh
- Para ejecutar tests de narrativa: ./run_narrative_admin_tests.py
- Para ejecutar el bot: ./dev.sh
"