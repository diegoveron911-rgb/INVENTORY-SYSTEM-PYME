import sqlite3

def init_db():
    # Conecta a la base de datos (si no existe, la crea automáticamente)
    conn = sqlite3.connect('inventario.db')
    cursor = conn.cursor()

    # 1. Tabla de Productos / Lubricantes
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_barras TEXT UNIQUE,
            nombre TEXT NOT NULL,          -- Ej: Shell Helix Ultra
            viscosidad TEXT,               -- Ej: 10W-40, 5W-30
            presentacion TEXT,             -- Ej: 1L, 4L, Tambor 208L
            precio_costo REAL NOT NULL,
            precio_venta REAL NOT NULL,
            stock_actual INTEGER DEFAULT 0,
            stock_minimo INTEGER DEFAULT 5  -- Alerta de poco stock
        )
    ''')

    # 2. Tabla para el Histórico de Recuentos Físicos (Auditoría mensual)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auditorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            stock_sistema INTEGER,
            stock_real INTEGER,
            diferencia INTEGER,
            FOREIGN KEY (producto_id) REFERENCES productos (id)
        )
    ''')

    conn.commit()
    conn.close()
    print("¡Base de datos y tablas creadas exitosamente en inventario.db!")

if __name__ == '__main__':
    init_db()