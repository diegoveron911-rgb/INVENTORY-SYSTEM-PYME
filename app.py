from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import pandas as pd
import io
from datetime import datetime, timedelta
from database import init_db

app = Flask(__name__)

def conectar():
    return sqlite3.connect('inventario.db')

# Función auxiliar para calcular litros según presentación
def obtener_litros(presentacion):
    p = presentacion.upper()
    if '208L' in p or 'TAMBOR' in p:
        return 208.0
    elif '20L' in p or 'BALDE' in p:
        return 20.0
    elif '4L' in p:
        return 4.0
    elif '1L' in p:
        return 1.0
    return 1.0

@app.route('/')
def index():
    conn = conectar()
    cursor = conn.cursor()
    
    # Cargar productos activos del mostrador
    cursor.execute('''
        SELECT id, nombre, viscosidad, presentacion, precio_venta, stock_actual, ultima_venta, litros_unitarios 
        FROM productos 
        WHERE ubicacion = 'MOSTRADOR'
    ''')
    productos = cursor.fetchall()

    # Cargar productos reubicados en el Depósito 60D
    cursor.execute('''
        SELECT id, nombre, viscosidad, presentacion, precio_venta, stock_actual, ultima_venta 
        FROM productos 
        WHERE ubicacion = 'DEPOSITO_60D'
    ''')
    productos_deposito = cursor.fetchall()

    # Cálculo para la alerta de 60 días sin ventas
    hace_60_dias = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d %H:%M:%S')

    # METRICAS PARA EL PANEL DE CONTROL
    # 1. Total Litros Vendidos
    cursor.execute("SELECT SUM(litros_totales) FROM historial_ventas")
    total_litros = cursor.fetchone()[0] or 0.0

    # 2. Top Marcas vendidas
    cursor.execute('''
        SELECT marca, SUM(litros_totales) as litros 
        FROM historial_ventas 
        GROUP BY marca 
        ORDER BY litros DESC 
        LIMIT 3
    ''')
    top_marcas = cursor.fetchall()

    # 3. Top Viscosidades vendidas
    cursor.execute('''
        SELECT viscosidad, SUM(litros_totales) as litros 
        FROM historial_ventas 
        GROUP BY viscosidad 
        ORDER BY litros DESC 
        LIMIT 3
    ''')
    top_viscosidades = cursor.fetchall()

    conn.close()

    return render_template(
        'index.html', 
        productos=productos, 
        productos_deposito=productos_deposito,
        hace_60_dias=hace_60_dias,
        total_litros=total_litros,
        top_marcas=top_marcas,
        top_viscosidades=top_viscosidades
    )

@app.route('/agregar', methods=['POST'])
def agregar():
    marca = request.form['marca']
    nombre_linea = request.form['nombre']
    nombre_completo = f"{marca} - {nombre_linea}"
    viscosidad = request.form['viscosidad']
    presentacion = request.form['presentacion']
    litros = obtener_litros(presentacion)
    codigo_barras = request.form.get('codigo_barras', '')
    precio_costo = float(request.form['precio_costo'])
    precio_venta = float(request.form['precio_venta'])
    stock = int(request.form['stock'])
    stock_minimo = int(request.form['stock_minimo'])

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO productos (codigo_barras, nombre, viscosidad, presentacion, litros_unitarios, precio_costo, precio_venta, stock_actual, stock_minimo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (codigo_barras, nombre_completo, viscosidad, presentacion, litros, precio_costo, precio_venta, stock, stock_minimo))
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
        litros_vendidos = cantidad * litros_unitarios
        precio_total = cantidad * precio_venta
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Actualizar stock y fecha de última venta
        cursor.execute("UPDATE productos SET stock_actual = ?, ultima_venta = ? WHERE id = ?", (nuevo_stock, fecha_actual, id_prod))
        
        # Registrar en el historial para métricas
        cursor.execute('''
            INSERT INTO historial_ventas (producto_id, marca, viscosidad, presentacion, cantidad, litros_totales, precio_total, fecha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (id_prod, marca, viscosidad, presentacion, cantidad, litros_vendidos, precio_total, fecha_actual))

        conn.commit()
    
    conn.close()
    return redirect(url_for('index'))

# Mover producto al Depósito de 60 Días
@app.route('/mover_deposito/<int:id>')
def mover_deposito(id):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("UPDATE productos SET ubicacion = 'DEPOSITO_60D' WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# Devolver producto al Mostrador
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
    df = pd.read_sql_query("SELECT id AS ID, codigo_barras AS Codigo, nombre AS Producto, viscosidad AS Viscosidad, presentacion AS Envase, precio_costo AS Costo, precio_venta AS Venta, stock_actual AS Stock, ubicacion AS Ubicacion, ultima_venta AS Ultima_Venta FROM productos", conn)
    conn.close()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventario')
    output.seek(0)

    return send_file(output, download_name='Inventario_Oleos_Minerales.xlsx', as_attachment=True)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)