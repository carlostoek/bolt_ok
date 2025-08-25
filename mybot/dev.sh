#!/bin/bash

# dev.sh - Script para desarrollo local con hot-reload

set -e  # Salir inmediatamente si un comando falla

# Colores para la salida
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Iniciando entorno de desarrollo...${NC}"

# Determinar qué comando Python usar
if command -v poetry &> /dev/null && [ -f "pyproject.toml" ]; then
    PYTHON_CMD="poetry run python"
else
    # Verificar si hay un entorno virtual activo
    if [ -d "venv" ] && [ -f "venv/bin/python" ]; then
        PYTHON_CMD="venv/bin/python"
    else
        PYTHON_CMD="python"
    fi
fi

# Verificar si se pasó un argumento para modo debug
if [ "$1" == "debug" ]; then
    echo -e "${YELLOW}🐛 Iniciando en modo debug...${NC}"
    $PYTHON_CMD -m debugpy --listen 5678 --wait-for-client bot.py
elif [ "$1" == "test" ]; then
    echo -e "${YELLOW}🧪 Iniciando watcher de tests...${NC}"
    # Ejecutar tests cuando cambian los archivos
    # Verificar si inotifywait está disponible
    if command -v inotifywait &> /dev/null; then
        while true; do
            inotifywait -r -e modify,create,delete ./tests ./services ./handlers ./database
            echo -e "${YELLOW}🔄 Cambios detectados, ejecutando tests...${NC}"
            $PYTHON_CMD -m pytest -x
        done
    else
        echo -e "${RED}Error: inotifywait no está instalado. Instalarlo con 'apt-get install inotify-tools' en Debian/Ubuntu o el equivalente en tu sistema.${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}🤖 Iniciando bot en modo desarrollo...${NC}"
    $PYTHON_CMD bot.py
fi

echo -e "${GREEN}✅ Entorno de desarrollo iniciado${NC}"