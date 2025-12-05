#!/data/data/com.termux/files/usr/bin/bash

# Script para iniciar el panel de administración

echo "🚀 Iniciando Panel de Administración..."

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✓ Entorno virtual activado"
fi

# Verificar que estamos en la raíz del proyecto
if [ ! -d "admin_panel" ]; then
    echo "❌ Error: Ejecuta este script desde la raíz del proyecto (telegram-bot/)"
    exit 1
fi

# Cargar variables de entorno
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✓ Variables de entorno cargadas"
else
    echo "⚠️  Advertencia: Archivo .env no encontrado, usando valores por defecto"
fi

# Iniciar Flask
export FLASK_APP=admin_panel/app.py
export FLASK_ENV=development

echo ""
echo "📍 Panel disponible en: http://127.0.0.1:5000"
echo "🛑 Presiona Ctrl+C para detener"
echo ""

python -m flask run --host=127.0.0.1 --port=5000