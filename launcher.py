import os
import sys
import socket
import threading
import time
import webbrowser
from database import init_db, get_db_path, get_base_dir
from app import app
from waitress import serve

def obtener_ip_local():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def abrir_navegador():
    time.sleep(1.2)
    webbrowser.open('http://localhost:5000')

def main():
    print('=' * 65)
    print('    INICIANDO SISTEMA DE GESTION E INVENTARIO PYME')
    print('=' * 65)
    
    base_dir = get_base_dir()
    db_path = get_db_path()
    print('Directorio base: ' + str(base_dir))
    print('Base de datos:   ' + str(db_path))
    init_db()
    print('Base de datos verificada y lista.')
    
    ip_local = obtener_ip_local()
    print('\n' + '-' * 65)
    print('  ACCESOS AL SISTEMA:')
    print('  En esta computadora:  http://localhost:5000')
    print('  Desde celulares/red:  http://' + str(ip_local) + ':5000')
    print('-' * 65)
    print('Minimiza esta ventana mientras uses el sistema. Para salir, cerrala.\n')
    
    threading.Thread(target=abrir_navegador, daemon=True).start()
    
    try:
        serve(app, host='0.0.0.0', port=5000, threads=8, _quiet=True)
    except KeyboardInterrupt:
        print('\nSistema detenido correctamente. Hasta pronto!')

if __name__ == '__main__':
    main()
