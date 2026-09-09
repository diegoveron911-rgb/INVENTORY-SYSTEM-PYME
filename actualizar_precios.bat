@echo off
title Actualizar Precios - Oleos Minerales SRL
echo ========================================================
echo   ACTUALIZADOR DE PRECIOS Y PRODUCTOS (AMA / GULF)
echo ========================================================
echo.
echo Buscando y procesando nuevos archivos en la carpeta...
python cargar_listas.py
echo.
echo ========================================================
echo þACTUALIZACION COMPLETADA CON EXITO!
echo.
pause
