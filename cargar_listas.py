import os
import sqlite3
import pandas as pd
import pypdf
import re
from database import init_db

def conectar():
    return sqlite3.connect('inventario.db')

def extraer_litros(envase_str):
    p = str(envase_str).upper()
    if '208' in p or '205' in p or 'TAMBOR 200' in p:
        return 208.0
    elif '100' in p or 'TAMBOR 100' in p:
        return 100.0
    elif '20' in p or 'BALDE' in p:
        return 20.0
    elif '4' in p or 'BIDON 4' in p:
        return 4.0
    elif '1' in p or 'BOTELLA 1' in p:
        return 1.0
    return 1.0

def extraer_viscosidad(texto):
    match = re.search(r'\b(\d{1,2}W[- ]?\d{2}|SAE\s*\d{1,2}|ISO\s*\d{2,3})\b', texto, re.IGNORECASE)
    return match.group(0).upper() if match else 'N/A'

def cargar_gulf_excel(filepath):
    print(f"⏳ Procesando lista GULF desde {filepath}...")
    df = pd.read_excel(filepath, skiprows=5)
    conn = conectar()
    cursor = conn.cursor()
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
            # CORRECCIÓN: iloc[7] es el Precio Neto de Lista ($326.979,90)
            precio_costo_neto = float(row.iloc[7])  
            precio_venta_final = float(row.iloc[9])  # Precio Final con IVA ($395.645,68)
        except (ValueError, TypeError):
            continue

        if codigo and nombre_prod and nombre_prod != 'nan' and not codigo.startswith('GAMA'):
            nombre_completo = f"GULF - {nombre_prod}"
            viscosidad = extraer_viscosidad(nombre_prod)
            litros = extraer_litros(envase)

            cursor.execute('''
                INSERT OR REPLACE INTO productos 
                (codigo_barras, nombre, viscosidad, presentacion, bulto_unidades, litros_unitarios, precio_costo, precio_venta, stock_actual, stock_minimo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (codigo, nombre_completo, viscosidad, envase, bulto, litros, precio_costo_neto, precio_venta_final, bulto, 1))
            cargados += 1

    conn.commit()
    conn.close()
    print(f"✅ ¡{cargados} productos de GULF cargados con Precios Netos de Lista corregidos!")
    
def cargar_ama_pdfs():
    print("⏳ Procesando listas de AMA desde PDFs...")
    pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf') and 'LISTA' in f.upper()]
    conn = conectar()
    cursor = conn.cursor()
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
                            litros = extraer_litros(descripcion)

                            cursor.execute('''
                                INSERT OR REPLACE INTO productos 
                                (codigo_barras, nombre, viscosidad, presentacion, bulto_unidades, litros_unitarios, precio_costo, precio_venta, stock_actual, stock_minimo)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (codigo, nombre_completo, viscosidad, f"Bulto x{bulto}", bulto, litros, precio_costo, precio_venta, bulto, 1))
                            cargados += 1
                        except ValueError:
                            continue

    conn.commit()
    conn.close()
    print(f"✅ ¡{cargados} productos de AMA cargados con Bultos oficiales!")

if __name__ == '__main__':
    init_db()
    excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') or f.endswith('.xls')]
    if excel_files:
        cargar_gulf_excel(excel_files[0])
    cargar_ama_pdfs()