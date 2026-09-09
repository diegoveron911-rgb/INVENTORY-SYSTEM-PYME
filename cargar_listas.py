import os
import sqlite3
import pandas as pd
import pypdf
import re
from database import init_db, get_db_path, extraer_litros_preciso

def conectar():
    return sqlite3.connect(get_db_path())

def extraer_viscosidad(texto):
    match = re.search(r'\b(\d{1,2}W[- ]?\d{2}|SAE\s*\d{1,2}|ISO\s*\d{2,3})\b', texto, re.IGNORECASE)
    return match.group(0).upper() if match else 'N/A'

def guardar_o_actualizar_producto(conn, codigo_lista, nombre, viscosidad, presentacion, bulto, litros, precio_costo, precio_venta):
    cursor = conn.cursor()
    # Buscamos si ya existe por nombre exacto
    cursor.execute("SELECT id, codigo_barras, stock_actual FROM productos WHERE nombre = ?", (nombre,))
    row = cursor.fetchone()
    
    if row:
        # Ya existe: Actualizamos los datos clave de precios y bulto sin tocar stock ni código de barra guardado
        prod_id, current_barcode, current_stock = row
        cursor.execute("""
            UPDATE productos 
            SET presentacion = ?, bulto_unidades = ?, litros_unitarios = ?, 
                precio_costo = ?, precio_venta = ?
            WHERE id = ?
        """, (presentacion, bulto, litros, precio_costo, precio_venta, prod_id))
    else:
        # No existe: Lo insertamos de cero con stock inicial 0
        try:
            cursor.execute("""
                INSERT INTO productos 
                (codigo_barras, nombre, viscosidad, presentacion, bulto_unidades, litros_unitarios, precio_costo, precio_venta, stock_actual, stock_minimo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (codigo_lista if codigo_lista else None, nombre, viscosidad, presentacion, bulto, litros, precio_costo, precio_venta, 0, 1))
        except sqlite3.IntegrityError:
            # Si el código de barras ya existe por alguna colisión, insertamos sin código (se asignará a mano)
            cursor.execute("""
                INSERT INTO productos 
                (codigo_barras, nombre, viscosidad, presentacion, bulto_unidades, litros_unitarios, precio_costo, precio_venta, stock_actual, stock_minimo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (None, nombre, viscosidad, presentacion, bulto, litros, precio_costo, precio_venta, 0, 1))

def cargar_gulf_excel(filepath):
    print(f"[INFO] Procesando lista GULF desde {filepath}...")
    df = pd.read_excel(filepath, skiprows=5)
    conn = conectar()
    cargados = 0

    for _, row in df.dropna(how='all').iterrows():
        codigo = str(row.iloc[1]).strip()
        nombre_prod = str(row.iloc[2]).strip()
        
        try:
            bulto = int(row.iloc[3])  # Columna FC / Bulto
        except (ValueError, TypeError):
            bulto = 1

        envase = str(row.iloc[4]).strip()
        
        try:
            precio_costo_neto = float(row.iloc[7])  
            precio_venta_final = float(row.iloc[9])  
        except (ValueError, TypeError):
            continue

        if codigo and nombre_prod and nombre_prod != 'nan' and not codigo.startswith('GAMA'):
            nombre_completo = f"GULF - {nombre_prod}"
            viscosidad = extraer_viscosidad(nombre_prod)
            litros = extraer_litros_preciso(envase)

            guardar_o_actualizar_producto(conn, codigo, nombre_completo, viscosidad, envase, bulto, litros, precio_costo_neto, precio_venta_final)
            cargados += 1

    conn.commit()
    conn.close()
    print(f"[OK] {cargados} productos de GULF procesados exitosamente.")
    
def cargar_ama_pdfs():
    print("[INFO] Procesando listas de AMA desde PDFs...")
    dir_listas = 'listas'
    if not os.path.exists(dir_listas):
        os.makedirs(dir_listas)
    pdf_files = [os.path.join(dir_listas, f) for f in os.listdir(dir_listas) if f.endswith('.pdf') and 'LISTA' in f.upper()]
    conn = conectar()
    cargados = 0

    for pdf_path in pdf_files:
        reader = pypdf.PdfReader(pdf_path)
        for page in reader.pages:
            texto = page.extract_text()
            lineas = texto.split('\n')
            
            for linea in lineas:
                match = re.match(r'^(\d{2}-\d{3}-\d{2})\s+(.+)$', linea.strip())
                if match:
                    codigo = match.group(1)
                    resto = match.group(2)
                    partes = resto.split()
                    
                    if len(partes) >= 4:
                        try:
                            precio_inc_str = partes[-1].replace('.', '').replace(',', '.')
                            precio_unit_str = partes[-2].replace('.', '').replace(',', '.')
                            bulto_str = partes[-3]
                            
                            precio_venta = float(precio_inc_str)
                            precio_costo = float(precio_unit_str)
                            bulto = int(bulto_str)
                            
                            descripcion = " ".join(partes[:-3])
                            nombre_completo = f"AMA - {descripcion}"
                            viscosidad = extraer_viscosidad(descripcion)
                            litros = extraer_litros_preciso(descripcion)

                            guardar_o_actualizar_producto(conn, codigo, nombre_completo, viscosidad, f"Bulto x{bulto}", bulto, litros, precio_costo, precio_venta)
                            cargados += 1
                        except ValueError:
                            continue

    conn.commit()
    conn.close()
    print(f"[OK] {cargados} productos de AMA procesados exitosamente.")

if __name__ == '__main__':
    init_db()
    dir_listas = 'listas'
    if not os.path.exists(dir_listas):
        os.makedirs(dir_listas)
        print(f"[INFO] Carpeta '{dir_listas}' creada. Coloque alli los archivos de precios de AMA y GULF.")
    
    excel_files = [os.path.join(dir_listas, f) for f in os.listdir(dir_listas) if f.endswith('.xlsx') or f.endswith('.xls')]
    if excel_files:
        cargar_gulf_excel(excel_files[0])
    else:
        print("[WARNING] No se encontro ningun archivo de Excel de GULF en la carpeta 'listas'.")
    cargar_ama_pdfs()