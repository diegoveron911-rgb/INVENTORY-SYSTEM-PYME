from flask import Flask, render_template, request, redirect, url_for
import sqlite3

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

if __name__ == '__main__':
    # host='0.0.0.0' permite que otras compus o la máquina virtual accedan
    app.run(host='0.0.0.0', port=5000, debug=True)