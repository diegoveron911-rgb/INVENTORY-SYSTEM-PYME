from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import pandas as pd
import io
from database import init_db

app = Flask(__name__)

def conectar():
    return sqlite3.connect('inventario.db')

@app.route('/')
def index():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, viscosidad, presentacion, precio_venta, stock_actual FROM productos")
    productos = cursor.fetchall()
    conn.close()
    return render_template('index.html', productos=productos)

@app.route('/agregar', methods=['POST'])
def agregar():
    marca = request.form['marca']
    nombre_linea = request.form['nombre']
    nombre_completo = f"{marca} - {nombre_linea}"
    viscosidad = request.form['viscosidad']
    presentacion = request.form['presentacion']
    codigo_barras = request.form.get('codigo_barras', '')
    precio_costo = float(request.form['precio_costo'])
    precio_venta = float(request.form['precio_venta'])
    stock = int(request.form['stock'])
    stock_minimo = int(request.form['stock_minimo'])

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO productos (codigo_barras, nombre, viscosidad, presentacion, precio_costo, precio_venta, stock_actual, stock_minimo)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (codigo_barras, nombre_completo, viscosidad, presentacion, precio_costo, precio_venta, stock, stock_minimo))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/vender', methods=['POST'])
def vender():
    id_prod = request.form['id_producto']
    cantidad = int(request.form['cantidad'])
    
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT stock_actual FROM productos WHERE id = ?", (id_prod,))
    res = cursor.fetchone()
    
    if res and res[0] >= cantidad:
        nuevo_stock = res[0] - cantidad
        cursor.execute("UPDATE productos SET stock_actual = ? WHERE id = ?", (nuevo_stock, id_prod))
        conn.commit()
    
    conn.close()
    return redirect(url_for('index'))

# --- NUEVA FUNCIÓN: EXPORTAR INVENTARIO A EXCEL ---
@app.route('/exportar')
def exportar():
    conn = conectar()
    df = pd.read_sql_query("SELECT id AS ID, codigo_barras AS Codigo, nombre AS Producto, viscosidad AS Viscosidad, presentacion AS Envase, precio_costo AS Costo, precio_venta AS Venta, stock_actual AS Stock FROM productos", conn)
    conn.close()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Inventario')
    output.seek(0)

    return send_file(output, download_name='Inventario_Oleos_Minerales.xlsx', as_attachment=True)

# --- NUEVA FUNCIÓN: IMPORTAR LISTADO DESDE EXCEL ---
@app.route('/importar', methods=['POST'])
def importar():
    file = request.files['file']
    if file:
        df = pd.read_excel(file)
        conn = conectar()
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute('''
                INSERT INTO productos (codigo_barras, nombre, viscosidad, presentacion, precio_costo, precio_venta, stock_actual, stock_minimo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(row.get('Codigo', '')),
                str(row.get('Producto', '')),
                str(row.get('Viscosidad', '')),
                str(row.get('Envase', '')),
                float(row.get('Costo', 0)),
                float(row.get('Venta', 0)),
                int(row.get('Stock', 0)),
                5
            ))
        conn.commit()
        conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)