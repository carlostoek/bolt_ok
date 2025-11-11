#!/bin/bash
# Script para iniciar el frontend React del panel administrativo

echo "🚀 Iniciando Frontend React..."
echo ""

# Verificar si el puerto 3000 está disponible
if netstat -tulpn | grep :3000 > /dev/null; then
    echo "⚠️  El puerto 3000 está en uso. Matando procesos..."
    pkill -f "vite" 2>/dev/null || true
    sleep 2
fi

echo "🌐 Iniciando servidor de desarrollo React..."
echo "💻 URL local: http://localhost:3000"
echo ""
echo "📊 El frontend se conectará automáticamente al backend en puerto 8080"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo ""

# Iniciar servidor de desarrollo
cd web/frontend
npm run dev