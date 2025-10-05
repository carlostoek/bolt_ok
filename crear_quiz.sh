#!/bin/bash
# Script wrapper para crear quizzes de compatibilidad
# Uso: ./crear_quiz.sh

cd "$(dirname "$0")"
python scripts/create_initial_quiz.py
