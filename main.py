import sqlite3
from database import init_db

def conectar():
    return sqlite3.connect('inventario.db')

def agregar_producto():
    print("\n--- CARGAR NUEVO LUBRICANTE ---")
    codigo = input("Código de barras (o presione Enter para omitir): ")
    nombre = input("Nombre del producto (Ej: Shell Helix Ultra): ")
    viscosidad = input("Viscosidad (Ej: 10W-40): ")
    presentacion = input("Presentación (Ej: 1L, 4L, Tambor): ")
    precio_costo = float(input("Precio de costo ($): "))
    precio_venta = float(input("Precio de venta ($): "))
    stock = int(input("Stock inicial (unidades/bidones): "))
    stock_min = int(input("Stock mínimo de alerta (defecto 5): ") or 5)

    conn = conectar()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO productos (codigo_barras, nombre, viscosidad, presentacion, precio_costo, precio_venta, stock_actual, stock_minimo)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (codigo, nombre, viscosidad, presentacion, precio_costo, precio_venta, stock, stock_min))
        conn.commit()
        print("✅ ¡Producto cargado con éxito!")
    except sqlite3.IntegrityError:
        print("❌ Error: Ya existe un producto con ese código de barras.")
    finally:
        conn.close()

def listar_productos():
    print("\n--- INVENTARIO ACTUAL DE LUBRICANTES ---")
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, viscosidad, presentacion, precio_venta, stock_actual FROM productos")
    productos = cursor.fetchall()
    conn.close()

    if not productos:
        print("No hay productos registrados en el sistema.")
        return

    print(f"{'ID':<4} | {'Producto':<25} | {'Viscosidad':<10} | {'Envase':<8} | {'Precio':<10} | {'Stock':<6}")
    print("-" * 75)
    for p in productos:
        print(f"{p[0]:<4} | {p[1]:<25} | {p[2]:<10} | {p[3]:<8} | ${p[4]:<9.2f} | {p[5]:<6}")

        
def registrar_venta():
    print("\n--- REGISTRAR VENTA DE LUBRICANTE ---")
    id_producto = input("Ingrese el ID del producto vendido: ")
    cantidad = int(input("Cantidad de unidades vendidas: "))

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, stock_actual FROM productos WHERE id = ?", (id_producto,))
    producto = cursor.fetchone()

    if not producto:
        print("❌ Producto no encontrado.")
        conn.close()
        return

    nombre, stock_actual = producto

    if cantidad > stock_actual:
        print(f"❌ Stock insuficiente. Solo quedan {stock_actual} unidades de {nombre}.")
    else:
        nuevo_stock = stock_actual - cantidad
        cursor.execute("UPDATE productos SET stock_actual = ? WHERE id = ?", (nuevo_stock, id_producto))
        conn.commit()
        print(f"✅ Venta registrada: Se descontaron {cantidad} unidades. Stock restante de {nombre}: {nuevo_stock}")

    conn.close()

def menu():
    init_db()  # Se asegura de que la BD esté creada al arrancar
    while True:
        print("\n=== SISTEMA DE GESTIÓN - PYME LUBRICANTES ===")
        print("1. Cargar nuevo lubricante")
        print("2. Ver todo el inventario")
        print("3. Registrar venta (Descontar stock)")
        print("4. Salir")
        
        opcion = input("Seleccione una opción (1-4): ")

        if opcion == '1':
            agregar_producto()
        elif opcion == '2':
            listar_productos()
        elif opcion == '3' :
            registrar_venta()
        elif opcion == '4':
            print("¡Hasta luego!")
            break
        else:
            print("Opción no válida. Intente de nuevo.")

if __name__ == '__main__':
    menu()