import sqlite3
import os
import sys
import re

def get_base_dir():
    """Retorna la carpeta base donde reside la aplicación o el ejecutable .exe."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_db_path():
    """Retorna la ruta absoluta al archivo inventario.db para asegurar persistencia."""
    return os.path.join(get_base_dir(), 'inventario.db')

def extraer_litros_preciso(texto):
    """Extrae con precisión el volumen en litros/kg de un envase, manejando Tambores, Baldes, Bidones, Botellas, cm3/ml/cc y gramos/kg."""
    if not texto:
        return 1.0
    p = str(texto).upper().replace('³', '3').replace('²', '2')
    
    # 1. Tambores grandes (208L, 205L, 200L)
    if re.search(r'\b(?:TAMBOR|TBR)\s*(?:208|205|200)\b', p) or re.search(r'\b(?:208|205|200)\s*(?:L|LT|LTS|LITRO|LITROS)\b', p):
        if '208' in p: return 208.0
        if '205' in p: return 205.0
        return 200.0

    # 2. Tambores medianos (180KG, 100L)
    if re.search(r'\b180\s*(?:KG|KGS|K)\b', p):
        return 180.0
    if re.search(r'\b(?:TAMBOR|TBR)\s*100\b', p) or re.search(r'\b100\s*(?:L|LT|LTS|LITRO|LITROS)\b', p):
        return 100.0

    # 3. Baldes / Bidones grandes (20L, 18KG, 10L, 4KG)
    if re.search(r'\b(?:BALDE|BIDON)?\s*20\s*(?:L|LT|LTS|KG|KGS|LITRO|LITROS)\b', p):
        return 20.0
    if re.search(r'\b(?:BALDE|BIDON)?\s*18\s*(?:KG|KGS|K)\b', p):
        return 18.0
    if re.search(r'\b(?:BALDE|BIDON)?\s*10\s*(?:L|LT|LTS|LITRO|LITROS)\b', p):
        return 10.0
    if re.search(r'\b(?:BALDE|BIDON|PACK)?\s*4\s*(?:KG|KGS|K)\b', p):
        return 4.0

    # 3b. Packs NxM KG (ej: PACK 4 x 3 KG)
    m_pkg = re.search(r'\b\d+\s*[xX]\s*(\d+)\s*(?:KG|KGS|K)\b', p)
    if m_pkg:
        return float(m_pkg.group(1))

    # 4. Bidones de 5L y 4L
    if re.search(r'\b5\s*(?:L|LT|LTS|LITRO|LITROS)\b', p) or 'BIDON 5' in p or '5 LITROS' in p:
        return 5.0
    if re.search(r'(?:\b4\s*X\s*4\s*L\b|\bBIDON\s*4\s*L\b|\b4\s*(?:L|LT|LTS|LITRO|LITROS)\b)', p):
        return 4.0

    # 5. Envases en cm3 / cc / ml / aerosoles (ej: 946 ml, 500 cm3, 440 cm3, 415 cm3, 410 ml, 388 cm3, 250 cm3, 220 ml, 160 cm3, 100 ml)
    m_ml = re.search(r'(\d+)\s*(?:ML|CC|CM3|CM|C\.C\.)\b', p)
    if m_ml:
        ml_val = float(m_ml.group(1))
        if ml_val < 5000:
            return round(ml_val / 1000.0, 3)

    # 5b. Envases en gramos (GRS / GR / G / GRAMOS, ej: 900 grs, 150 grs, 400 grs)
    m_gr = re.search(r'(\d+)\s*(?:GRS|GR|G|GRAMOS)\b', p)
    if m_gr:
        gr_val = float(m_gr.group(1))
        if gr_val < 5000:
            return round(gr_val / 1000.0, 3)

    # 5c. Mención de Pote o Aerosol con número directo
    m_direct = re.search(r'(?:POTE|AEROSOL|AER)\s*(?:DE\s*)?(\d{2,4})\b', p)
    if m_direct:
        val = float(m_direct.group(1))
        if val <= 1000:
            return round(val / 1000.0, 3)

    # 6. Botellas de 1L (ej: 12x1 L, BOTELLA 1 L, 1 L, 1L)
    if re.search(r'(?:\b12\s*X\s*1\s*L\b|\bBOTELLA\s*1\s*L\b|\b1\s*(?:L|LT|LTS|LITRO|LITROS)\b)', p):
        return 1.0

    # 7. Palabras clave de fallback
    if '200' in p and 'L' in p:
        return 200.0
    if '205' in p and 'L' in p:
        return 205.0
    if 'BALDE' in p:
        return 20.0
    if 'TAMBOR' in p or 'TBR' in p:
        return 200.0
        
    return 1.0

def extraer_bulto_unidades(presentacion):
    """Extrae con precisión las unidades reales contenidas por caja o bulto."""
    if not presentacion:
        return 1
    p = str(presentacion).upper().strip()
    
    # Envases individuales grandes sin multiplicador (Tambor, Balde, etc.) -> 1 unidad
    if any(k in p for k in ['BALDE', 'TAMBOR', 'TBR', 'CONTENEDOR', 'GRANEL', 'BIB', 'BAG IN BOX']) and 'X' not in p:
        return 1
        
    # 1. Patrón NxM (ej: 4 x 4 L, 12 x 1 L, 6 x 420 ml, 16 x 800 ml, 100 x 100 ml)
    m = re.search(r'\b(\d+)\s*[xX]\s*\d+', p)
    if m:
        return int(m.group(1))
        
    # 2. Patrón Bulto xN o CAJA N o N Un
    m2 = re.search(r'(?:BULTO\s*[xX]\s*|CAJA\s*)(\d+)', p)
    if m2:
        return int(m2.group(1))
    m3 = re.search(r'\b(\d+)\s*(?:UN|UNID|UNIDADES)\b', p)
    if m3:
        return int(m3.group(1))
        
    return 1

def clasificar_tipo_producto(nombre, presentacion):
    """Clasifica con precisión si un producto es 'LIQUIDO' (aceites, refrigerantes, aerosoles) o 'GRASA' (grasas lubricantes)."""
    t = f"{nombre or ''} {presentacion or ''}".upper()
    keywords_grasa = ['GRASA', 'LITIO', 'AMPAC', 'HOTT', 'WR WHITE', 'CHASIS', 'RULEMAN', 'MULTIPURPOSE']
    if any(k in t for k in ['ACEITE', 'MOTOR', '20W', '10W', '15W', '5W', '80W', '90', '46']):
        if not any(k in t for k in ['GRASA', 'LITIO', 'AMPAC', 'HOTT', 'MULTIPURPOSE']):
            return 'LIQUIDO'
    if any(k in t for k in keywords_grasa) or 'POTE' in t:
        return 'GRASA'
    return 'LIQUIDO'

def clasificar_viscosidad_tipo(tipo_producto, viscosidad, nombre, presentacion):
    """Retorna una etiqueta limpia para la cuadrícula de viscosidad/tipo (ej: '20W-50', 'Grasa Litio EP-2', etc.) y su categoría ('LIQUIDO' o 'GRASA')."""
    if str(tipo_producto).upper() == 'GRASA':
        t = f"{nombre or ''} {presentacion or ''}".upper()
        if 'EP-2' in t or 'EP 2' in t or 'EP2' in t:
            return 'Grasa Litio EP-2', 'GRASA'
        if 'MULTIUSO' in t or 'MULTI-USO' in t:
            return 'Grasa Litio Multiuso', 'GRASA'
        if 'MULTIPURPOSE' in t:
            return 'Grasa Multipurpose', 'GRASA'
        if 'CHASIS' in t:
            return 'Grasa Chasis', 'GRASA'
        if 'RULEMAN' in t:
            return 'Grasa Rulemanes', 'GRASA'
        if 'GRAFITADA' in t:
            return 'Grasa Grafitada', 'GRASA'
        if 'AZUL' in t or 'COMPLEX' in t:
            return 'Grasa Litio Complex', 'GRASA'
        if 'LITIO' in t:
            return 'Grasa Litio', 'GRASA'
        return 'Grasa Lubricante', 'GRASA'
    
    # Líquidos:
    v = (viscosidad or '').strip().upper()
    nom = (nombre or '').upper()
    pres = (presentacion or '').upper()
    
    if v and v not in ['N/A', '-', 'NA', 'S/D', 'NULL', 'NONE']:
        v_norm = re.sub(r'(\d+W?)\s+(\d+)', r'\1-\2', v)
        return v_norm, 'LIQUIDO'
    
    if '2T' in nom or '2CR' in nom:
        return '2T (2 Tiempos)', 'LIQUIDO'
    if any(k in nom for k in ['FREEZGLICOL', 'REFRIGERANTE', 'AGUA', 'CORROCION', 'ANTICONGELANTE']):
        return 'Refrigerante / Agua', 'LIQUIDO'
    if any(a in nom or a in pres for a in ['AEROSOL', 'F-18', 'CHAIN LUBE', 'FILTER OIL', 'ARRANCA MOTOR']):
        return 'Aerosoles / Aditivos', 'LIQUIDO'
        
    return 'Otros Líquidos', 'LIQUIDO'

def init_db():
    conn = sqlite3.connect(get_db_path(), timeout=10.0)
    cursor = conn.cursor()
    # Configurar WAL (Write-Ahead Logging) para máxima velocidad de lectura/escritura y menor consumo de disco
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=5000")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_barras TEXT UNIQUE,
            nombre TEXT NOT NULL,
            viscosidad TEXT,
            presentacion TEXT,
            bulto_unidades INTEGER DEFAULT 1,
            litros_unitarios REAL DEFAULT 1.0,
            precio_costo REAL NOT NULL,        -- Precio Costo Neto (Lista)
            precio_venta REAL NOT NULL,        -- Precio Bulto Final (con IVA)
            stock_actual INTEGER DEFAULT 0,
            stock_minimo INTEGER DEFAULT 5,
            ubicacion TEXT DEFAULT 'MOSTRADOR',
            ultima_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            activo INTEGER DEFAULT 1,
            fecha_baja TIMESTAMP,
            tipo_producto TEXT DEFAULT 'LIQUIDO'
        )
    ''')

    # Migración automática para bases de datos ya creadas que no tienen la columna 'activo', 'fecha_baja' o 'tipo_producto'
    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN activo INTEGER DEFAULT 1")
        print("Columna 'activo' añadida a la tabla 'productos'.")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN fecha_baja TIMESTAMP")
        print("Columna 'fecha_baja' añadida a la tabla 'productos'.")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN tipo_producto TEXT DEFAULT 'LIQUIDO'")
        print("Columna 'tipo_producto' añadida a la tabla 'productos'.")
    except sqlite3.OperationalError:
        pass

    # Inicializar fecha_baja para productos dados de baja sin fecha registrada
    cursor.execute("UPDATE productos SET fecha_baja = CURRENT_TIMESTAMP WHERE activo = 0 AND fecha_baja IS NULL")

    # Limpieza automática: Eliminar definitivamente de la papelera productos con más de 30 días dados de baja
    cursor.execute("""
        UPDATE historial_ventas 
        SET producto_id = NULL 
        WHERE producto_id IN (SELECT id FROM productos WHERE activo = 0 AND fecha_baja IS NOT NULL AND fecha_baja <= datetime('now', '-30 days'))
    """)
    cursor.execute("""
        DELETE FROM reservas 
        WHERE producto_id IN (SELECT id FROM productos WHERE activo = 0 AND fecha_baja IS NOT NULL AND fecha_baja <= datetime('now', '-30 days'))
    """)
    cursor.execute("DELETE FROM productos WHERE activo = 0 AND fecha_baja IS NOT NULL AND fecha_baja <= datetime('now', '-30 days')")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            nombre_producto TEXT,
            marca TEXT,
            viscosidad TEXT,
            presentacion TEXT,
            cantidad INTEGER,
            litros_totales REAL,
            precio_total REAL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tipo_producto TEXT DEFAULT 'LIQUIDO',
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    ''')

    try:
        cursor.execute("ALTER TABLE historial_ventas ADD COLUMN tipo_producto TEXT DEFAULT 'LIQUIDO'")
        print("Columna 'tipo_producto' añadida a la tabla 'historial_ventas'.")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE historial_ventas ADD COLUMN nombre_producto TEXT")
        print("Columna 'nombre_producto' añadida a la tabla 'historial_ventas'.")
    except sqlite3.OperationalError:
        pass

    # Backfill automático de nombre_producto desde el catálogo
    cursor.execute("""
        UPDATE historial_ventas 
        SET nombre_producto = (SELECT nombre FROM productos WHERE productos.id = historial_ventas.producto_id)
        WHERE (nombre_producto IS NULL OR nombre_producto = '') AND producto_id IS NOT NULL
    """)

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            empleado_nombre TEXT,
            cantidad INTEGER,
            estado TEXT DEFAULT 'PENDIENTE',
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configuracion_admin (
            id INTEGER PRIMARY KEY,
            pin_admin TEXT DEFAULT '1234'
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO configuracion_admin (id, pin_admin) VALUES (1, '1234')")

    # Crear índices estratégicos para acelerar búsquedas y optimizar consultas en equipos de bajos recursos
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_productos_activo_ubicacion ON productos (activo, ubicacion)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_productos_codigo_barras ON productos (codigo_barras)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reservas_producto_estado ON reservas (producto_id, estado)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_ventas_producto ON historial_ventas (producto_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_historial_ventas_fecha ON historial_ventas (fecha)")


    # Migración automática y autocorrección de litros en productos e historial de ventas
    try:
        cursor.execute("SELECT id, nombre, presentacion, litros_unitarios FROM productos")
        prods = cursor.fetchall()
        for p in prods:
            id_p, nom, pres, lit_old = p
            lit_new = extraer_litros_preciso(str(pres or '') + ' ' + str(nom or ''))
            if lit_new != lit_old:
                cursor.execute("UPDATE productos SET litros_unitarios = ? WHERE id = ?", (lit_new, id_p))
                
        cursor.execute("""
            SELECT h.id, h.cantidad, p.litros_unitarios, h.litros_totales
            FROM historial_ventas h
            JOIN productos p ON h.producto_id = p.id
        """)
        ventas = cursor.fetchall()
        for v in ventas:
            id_v, cant, lit_unit, lit_tot_old = v
            lit_tot_new = round(cant * (lit_unit if lit_unit else 1.0), 2)
            if lit_tot_new != lit_tot_old:
                cursor.execute("UPDATE historial_ventas SET litros_totales = ? WHERE id = ?", (lit_tot_new, id_v))

        # Autocorrección de bulto_unidades (ej: CAJA 4 x 4 L son 4 unidades reales, no 16)
        cursor.execute("SELECT id, presentacion, bulto_unidades FROM productos")
        prods_bulto = cursor.fetchall()
        for pb in prods_bulto:
            id_pb, pres_b, bulto_old = pb
            bulto_new = extraer_bulto_unidades(pres_b)
            if bulto_new != bulto_old and bulto_new > 0:
                cursor.execute("UPDATE productos SET bulto_unidades = ? WHERE id = ?", (bulto_new, id_pb))

        # Migración y clasificación automática de tipo_producto (LIQUIDO vs GRASA)
        cursor.execute("SELECT id, nombre, presentacion, tipo_producto FROM productos")
        prods_tipo = cursor.fetchall()
        for pt in prods_tipo:
            id_pt, nom_pt, pres_pt, tipo_old = pt
            tipo_calc = clasificar_tipo_producto(nom_pt, pres_pt)
            if tipo_old != tipo_calc:
                cursor.execute("UPDATE productos SET tipo_producto = ? WHERE id = ?", (tipo_calc, id_pt))

        cursor.execute("""
            SELECT h.id, h.marca, h.viscosidad, h.presentacion, p.nombre, p.tipo_producto, h.tipo_producto
            FROM historial_ventas h
            LEFT JOIN productos p ON h.producto_id = p.id
        """)
        ventas_tipo = cursor.fetchall()
        for vt in ventas_tipo:
            id_vt, v_marca, v_visc, v_pres, p_nom, p_tipo, h_tipo_old = vt
            tipo_calc = p_tipo if p_tipo else clasificar_tipo_producto(f"{v_marca or ''} {v_visc or ''} {p_nom or ''}", v_pres)
            if h_tipo_old != tipo_calc:
                cursor.execute("UPDATE historial_ventas SET tipo_producto = ? WHERE id = ?", (tipo_calc, id_vt))
    except Exception as e:
        pass

    conn.commit()
    conn.close()
    print("¡Base de datos reestructurada con índices e inicializada con éxito!")

if __name__ == '__main__':
    init_db()