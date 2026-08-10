import sqlite3

def init_db():
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()

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
            activo INTEGER DEFAULT 1
        )
    ''')

    # Migración automática para bases de datos ya creadas que no tienen la columna 'activo'
    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN activo INTEGER DEFAULT 1")
        print("Columna 'activo' añadida a la tabla 'productos'.")
    except sqlite3.OperationalError:
        # La columna ya existe en la base de datos
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            marca TEXT,
            viscosidad TEXT,
            presentacion TEXT,
            cantidad INTEGER,
            litros_totales REAL,
            precio_total REAL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    ''')

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

    conn.commit()
    conn.close()
    print("¡Base de datos reestructurada e inicializada con éxito!")

if __name__ == '__main__':
    init_db()