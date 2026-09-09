@echo off
title Sistema de Inventario (MOSTRADOR - Consulta)
echo mostrador > perfil.txt
echo ========================================================
echo   INICIANDO MODO MOSTRADOR (SOLO CONSULTA)
echo ========================================================
echo.
taskkill /f /im SistemaInventario.exe >nul 2>&1
if exist SistemaInventario.exe (
    start "" SistemaInventario.exe
    timeout /t 2 /nobreak >nul
    start http://localhost:5000
) else if exist launcher.py (
    python launcher.py
) else (
    start http://localhost:5000
    python app.py
)
