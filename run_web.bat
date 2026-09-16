@echo off
title Compresor Inteligente - Servidor Web Localhost
echo =======================================================
echo    Iniciando Servidor Web en http://localhost:5000
echo =======================================================

python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Instalando librerias necesarias...
    pip install -r requirements.txt
)

echo [*] Abriendo http://localhost:5000 en tu navegador...
python web_app.py
pause
