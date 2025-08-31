#!/bin/bash

echo "Starting BabyCareBot API..."
echo ""
echo "Make sure you have installed dependencies:"
echo "pip install -r api_requirements.txt"
echo ""
echo "API will be available at: http://localhost:5000"
echo ""

# Проверяем, установлен ли Python
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "Error: Python is not installed"
        exit 1
    else
        python api.py
    fi
else
    python3 api.py
fi
