@echo off
title Compresor Inteligente de Imagenes por Lotes
echo =======================================================
echo    Iniciando Compresor Inteligente de Imagenes
echo =======================================================

python -c "import PIL" >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Instalando libreria Pillow...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [!] Error al instalar las dependencias con pip.
        pause
        exit /b %errorlevel%
    )
)

echo [*] Abriendo aplicacion...
python app.py
pause
