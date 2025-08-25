#!/bin/bash

# test.sh - Script para ejecutar tests con diferentes configuraciones

set -e  # Salir inmediatamente si un comando falla

# Colores para la salida
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Ejecutando tests...${NC}"

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

# Verificar si se pasó un argumento específico
if [ "$1" == "coverage" ]; then
    echo -e "${YELLOW}📊 Ejecutando tests con cobertura...${NC}"
    $PYTHON_CMD -m pytest --cov=. --cov-report=html --cov-report=term-missing
    echo -e "${GREEN}✅ Cobertura generada en htmlcov/index.html${NC}"
elif [ "$1" == "quick" ]; then
    echo -e "${YELLOW}⚡ Ejecutando tests rápidos (sin coverage)...${NC}"
    $PYTHON_CMD -m pytest -x  # Detener en el primer fallo
elif [ "$1" == "integration" ]; then
    echo -e "${YELLOW}🔄 Ejecutando solo tests de integración...${NC}"
    $PYTHON_CMD -m pytest tests/integration/ -v
elif [ "$1" == "unit" ]; then
    echo -e "${YELLOW}🔧 Ejecutando solo tests unitarios...${NC}"
    $PYTHON_CMD -m pytest tests/ -v --ignore=tests/integration/
else
    echo -e "${YELLOW}🧪 Ejecutando todos los tests...${NC}"
    $PYTHON_CMD -m pytest -v
fi

echo -e "${GREEN}✅ Tests completados${NC}"