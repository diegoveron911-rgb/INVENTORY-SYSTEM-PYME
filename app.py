from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import pandas as pd
import io
from datetime import datetime, timedelta
from database import init_db

app = Flask(__name__)

def conectar():
    return sqlite3.connect('inventario.db')

@app.route('/')
def index():
    conn = conectar()
    cursor = conn.cursor()
    
    # 1. Cargar productos activos del mostrador junto con la suma de reservas pendientes
    cursor.execute('''
        SELECT 
            p.id, 
            p.codigo_barras, 
            p.nombre, 
            p.viscosidad, 
            p.presentacion, 
            p.bulto_unidades, 
            p.precio_costo, 
            p.precio_venta, 
            p.stock_actual, 
            p.ultima_venta,
            COALESCE(SUM(CASE WHEN r.estado = 'PENDIENTE' THEN r.cantidad ELSE 0 END), 0) AS reservado_pendiente
        FROM productos p
        LEFT JOIN reservas r ON p.id = r.producto_id
        WHERE p.ubicacion = 'MOSTRADOR' AND (p.activo = 1 OR p.activo IS NULL)
        GROUP BY p.id
    ''')
    productos = cursor.fetchall()

    # 2. Productos en Depósito 60D
    cursor.execute('''
        SELECT id, nombre, viscosidad, presentacion, bulto_unidades, precio_costo, precio_venta, stock_actual, ultima_venta 
        FROM productos 
        WHERE ubicacion = 'DEPOSITO_60D' AND (activo = 1 OR activo IS NULL)
    ''')
    productos_deposito = cursor.fetchall()

    # 3. Productos dados de baja (Papelera / Archivados)
    cursor.execute("SELECT id, codigo_barras, nombre, viscosidad FROM productos WHERE activo = 0")
    productos_archivados = cursor.fetchall()

    # 4. Reservas pendientes
    cursor.execute('''
        SELECT r.id, p.nombre, p.viscosidad, p.presentacion, r.empleado_nombre, r.cantidad, r.estado, r.fecha, p.stock_actual
        FROM reservas r
        JOIN productos p ON r.producto_id = p.id
        WHERE r.estado = 'PENDIENTE'
        ORDER BY r.fecha DESC
    ''')
    reservas_pendientes = cursor.fetchall()

    hace_60_dias = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d %H:%M:%S')

    # 5. MÉTRICAS COMPLETA DE VENTAS (Totales, Marca, Viscosidad y Resumen Mensual)
    cursor.execute("SELECT SUM(litros_totales) FROM historial_ventas")
    total_litros = cursor.fetchone()[0] or 0.0

    cursor.execute('''
        SELECT marca, SUM(litros_totales) as litros, SUM(precio_total) as facturacion 
        FROM historial_ventas 
        GROUP BY marca 
        ORDER BY litros DESC
    ''')
    metricas_marca = cursor.fetchall()

    cursor.execute('''
        SELECT viscosidad, SUM(litros_totales) as litros, SUM(cantidad) as unidades 
        FROM historial_ventas 
        GROUP BY viscosidad 
        ORDER BY litros DESC
    ''')
    metricas_viscosidad = cursor.fetchall()

    cursor.execute('''
        SELECT 
            strftime('%Y-%m', fecha) as mes,
            COUNT(id) as operaciones,
            SUM(litros_totales) as litros,
            SUM(precio_total) as facturacion
        FROM historial_ventas
        GROUP BY strftime('%Y-%m', fecha)
        ORDER BY mes DESC
    ''')
    resumen_mensual = cursor.fetchall()

    # 6. CÁLCULO INTELIGENTE DE STOCK BAJO Y AGOTADOS
    stock_bajo_count = 0
    agotados_count = 0

    for p in productos:
        stock = p[8]  # stock_actual
        presentacion = str(p[4]).upper() if p[4] else ""

        if stock is None or stock == 0:
            agotados_count += 1
        else:
            if any(x in presentacion for x in ['20', '204', 'TAMBOR', 'BALDE']):
                if stock == 0:
                    stock_bajo_count += 1
            else:
                if 1 <= stock <= 3:
                    stock_bajo_count += 1

    conn.close()

    return render_template(
        'index.html', 
        productos=productos, 
        productos_deposito=productos_deposito,
        productos_archivados=productos_archivados,
        reservas_pendientes=reservas_pendientes,
        hace_60_dias=hace_60_dias,
        total_litros=total_litros,
        metricas_marca=metricas_marca,
        metricas_viscosidad=metricas_viscosidad,
        resumen_mensual=resumen_mensual,
        stock_bajo_count=stock_bajo_count,
        agotados_count=agotados_count
    )

@app.route('/crear_reserva', methods=['POST'])
def crear_reserva():
    id_prod = request.form['id_producto']
    vendedor = request.form['vendedor']
    cantidad = int(request.form['cantidad'])

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT stock_actual FROM productos WHERE id = ?", (id_prod,))
    prod = cursor.fetchone()

    if prod and prod[0] >= cantidad:
        cursor.execute('''
            INSERT INTO reservas (producto_id, empleado_nombre, cantidad, estado)
            VALUES (?, ?, ?, 'PENDIENTE')
        ''', (id_prod, vendedor, cantidad))
        conn.commit()

    conn.close()
    return redirect(url_for('index'))

@app.route('/aprobar_reserva/<int:id>')
def aprobar_reserva(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT producto_id, cantidad FROM reservas WHERE id = ?", (id,))
    res = cursor.fetchone()
    
    if res:
        id_prod, cantidad = res
        cursor.execute("SELECT nombre, viscosidad, presentacion, precio_venta, stock_actual, litros_unitarios FROM productos WHERE id = ?", (id_prod,))
        prod = cursor.fetchone()
        
        if prod and prod[4] >= cantidad:
            nombre, viscosidad, presentacion, precio_venta, stock_actual, litros_unitarios = prod
            marca = nombre.split(' - ')[0] if ' - ' in nombre else 'OTRA'
            nuevo_stock = stock_actual - cantidad
            litros_vendidos = cantidad * (litros_unitarios or 1.0)
            precio_total = cantidad * precio_venta
            fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute("UPDATE productos SET stock_actual = ?, ultima_venta = ? WHERE id = ?", (nuevo_stock, fecha_actual, id_prod))
            cursor.execute("UPDATE reservas SET estado = 'APROBADO' WHERE id = ?", (id,))
            cursor.execute('''
                INSERT INTO historial_ventas (producto_id, marca, viscosidad, presentacion, cantidad, litros_totales, precio_total, fecha)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (id_prod, marca, viscosidad, presentacion, cantidad, litros_vendidos, precio_total, fecha_actual))

            conn.commit()

    conn.close()
    return redirect(url_for('index'))

@app.route('/rechazar_reserva/<int:id>')
def rechazar_reserva(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE reservas SET estado = 'RECHAZADO' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/editar_stock', methods=['POST'])
def editar_stock():
    id_prod = request.form['id_producto']
    nuevo_stock = int(request.form['nuevo_stock'])
    
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE productos SET stock_actual = ? WHERE id = ?", (nuevo_stock, id_prod))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/agregar', methods=['POST'])
def agregar():
    marca = request.form['marca']
    nombre_linea = request.form['nombre']
    nombre_completo = f"{marca} - {nombre_linea}"
    viscosidad = request.form['viscosidad']
    presentacion = request.form['presentacion']
    bulto = int(request.form.get('bulto', 1))
    codigo_barras = request.form.get('codigo_barras', '')
    precio_costo = float(request.form['precio_costo'])
    precio_venta = float(request.form['precio_venta'])
    stock = int(request.form['stock'])

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO productos (codigo_barras, nombre, viscosidad, presentacion, bulto_unidades, precio_costo, precio_venta, stock_actual, ubicacion, activo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'MOSTRADOR', 1)
    ''', (codigo_barras, nombre_completo, viscosidad, presentacion, bulto, precio_costo, precio_venta, stock))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/vender', methods=['POST'])
def vender():
    id_prod = request.form['id_producto']
    cantidad = int(request.form['cantidad'])
    
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, viscosidad, presentacion, precio_venta, stock_actual, litros_unitarios FROM productos WHERE id = ?", (id_prod,))
    prod = cursor.fetchone()
    
    if prod and prod[4] >= cantidad:
        nombre, viscosidad, presentacion, precio_venta, stock_actual, litros_unitarios = prod
        marca = nombre.split(' - ')[0] if ' - ' in nombre else 'OTRA'
        
        nuevo_stock = stock_actual - cantidad
        litros_vendidos = cantidad * (litros_unitarios or 1.0)
        precio_total = cantidad * precio_venta
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("UPDATE productos SET stock_actual = ?, ultima_venta = ? WHERE id = ?", (nuevo_stock, fecha_actual, id_prod))
        cursor.execute('''
            INSERT INTO historial_ventas (producto_id, marca, viscosidad, presentacion, cantidad, litros_totales, precio_total, fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (id_prod, marca, viscosidad, presentacion, cantidad, litros_vendidos, precio_total, fecha_actual))

        conn.commit()
    
    conn.close()
    return redirect(url_for('index'))

@app.route('/mover_deposito/<int:id>')
def mover_deposito(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE productos SET ubicacion = 'DEPOSITO_60D' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/mover_mostrador/<int:id>')
def mover_mostrador(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE productos SET ubicacion = 'MOSTRADOR', ultima_venta = CURRENT_TIMESTAMP WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/exportar')
def exportar():
    conn = conectar()
    df = pd.read_sql_query("SELECT id AS ID, codigo_barras AS Codigo, nombre AS Producto, viscosidad AS Viscosidad, presentacion AS Envase, bulto_unidades AS Bulto_Unidades, precio_costo AS Costo_Neto, precio_venta AS Venta_Final, stock_actual AS Stock FROM productos WHERE activo = 1 OR activo IS NULL", conn)
    conn.close()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventario')
    output.seek(0)

    return send_file(output, download_name='Inventario_Oleos_Minerales.xlsx', as_attachment=True)

@app.route('/iniciar_inventario_auditoria', methods=['POST'])
def iniciar_inventario_auditoria():
    conn = conectar()
    cursor = conn.cursor()
    
    # 1. Crear tabla de auditoría si no existe
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auditoria_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            id_producto INTEGER,
            stock_teorico INTEGER,
            stock_contado INTEGER DEFAULT 0
        )
    ''')
    
    # 2. Guardar foto del stock teórico antes del blanqueo
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("SELECT id, stock_actual FROM productos WHERE activo = 1 OR activo IS NULL")
    productos = cursor.fetchall()
    
    for p in productos:
        cursor.execute("""
            INSERT INTO auditoria_stock (fecha, id_producto, stock_teorico, stock_contado)
            VALUES (?, ?, ?, 0)
        """, (fecha_actual, p[0], p[1]))
    
    # 3. Blanquear stock a cero
    cursor.execute("UPDATE productos SET stock_actual = 0 WHERE activo = 1 OR activo IS NULL")
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

@app.route('/importar_lista', methods=['POST'])
def importar_lista():
    if 'archivo_lista' not in request.files:
        return redirect(url_for('index'))
    file = request.files['archivo_lista']
    if file.filename == '':
        return redirect(url_for('index'))
    
    if file:
        try:
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)

            conn = conectar()
            cursor = conn.cursor()

            # Iterar sobre las filas importadas
            for _, row in df.iterrows():
                codigo = str(row.get('Codigo', '') if pd.notna(row.get('Codigo')) else '')
                nombre = str(row.get('Producto', ''))
                viscosidad = str(row.get('Viscosidad', ''))
                presentacion = str(row.get('Envase', ''))
                bulto = int(row.get('Bulto_Unidades', 1))
                costo = float(row.get('Costo_Neto', 0.0))
                venta = float(row.get('Venta_Final', 0.0))
                stock = int(row.get('Stock', 0))

                cursor.execute('''
                    INSERT INTO productos (codigo_barras, nombre, viscosidad, presentacion, bulto_unidades, precio_costo, precio_venta, stock_actual, ubicacion, activo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'MOSTRADOR', 1)
                ''', (codigo, nombre, viscosidad, presentacion, bulto, costo, venta, stock))

            conn.commit()
            conn.close()
        except Exception as e:
            print("Error al importar la lista:", e)

    return redirect(url_for('index'))

@app.route('/dar_de_baja/<int:id>', methods=['POST'])
def dar_de_baja(id):
    conn = conectar()
    cursor = conn.cursor()
    # Pasa el producto a estado Inactivo/Archivado (Baja Lógica)
    cursor.execute("UPDATE productos SET activo = 0 WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/restaurar_producto/<int:id>', methods=['POST'])
def restaurar_producto(id):
    conn = conectar()
    cursor = conn.cursor()
    # Devuelve el producto al Mostrador activo
    cursor.execute("UPDATE productos SET activo = 1 WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/eliminar_definitivo/<int:id>', methods=['POST'])
def eliminar_definitivo(id):
    conn = conectar()
    cursor = conn.cursor()
    # Elimina el registro por completo de la base de datos
    cursor.execute("DELETE FROM productos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)