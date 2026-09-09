# 05. Guía de Reutilización del Backend para Otras PyMEs

Este documento es una guía práctica para vos como desarrollador: explica cómo tomar este backend probado y robusto como base y adaptarlo rápidamente a cualquier otro rubro comercial (ferreterías, pinturerías, repuesteras automotor, corralones, minimarkets, etc.) modificando el modelo de datos y personalizando la interfaz.

---

## 🎯 ¿Por qué este Backend es una "Planta Motriz" perfecta para PyMEs?

Ya tenés resueltos y testeados los problemas más difíciles de la gestión comercial en pequeñas y medianas empresas:
1. **Motor de Stock Atómico y Seguro:** No hay descuadres de inventario; el descuento se ejecuta con transacciones SQL estrictas.
2. **Auditoría Permanente y Anulación:** Cada salida queda registrada y se puede anular devolviendo el stock automáticamente.
3. **Roles y Seguridad (Admin vs Mostrador):** Interfaz restringida para empleados y desbloqueo por PIN para los dueños.
4. **Offline-First y Sincronización en Red:** Funciona sin internet y se sincroniza por Wi-Fi o pendrive.
5. **Generación de Comprobantes:** Motor de tickets PDF en 80 mm y exportación de reportes a Excel.
6. **Integración con Hardware:** Pistolas lectoras de código de barras USB y cámaras de celulares.

---

## 🛠️ Paso a Paso: Cómo adaptar el sistema a un nuevo cliente

### PASO 1: Adaptar la tabla `productos` en `database.py`

Según el rubro de la PyME, los productos tienen distintas características:

```
RUBRO LUBRICANTES (Actual):   [ Marca | Viscosidad | Presentación | Bulto | Litros ]
RUBRO FERRETERÍA:             [ Marca | Rubro/Familia | Medida/Pulgadas | Stock Mínimo ]
RUBRO PINTURERÍA:             [ Marca | Color | Acabado (Mate/Satinado) | Litros (1, 4, 10, 20L) ]
RUBRO REPUESTERA AUTOMOTOR:   [ Fabricante | Número de Pieza | Modelo/Vehículo | Lado/Posición ]
RUBRO ALMACÉN / MINIMARKET:   [ Marca | Categoría | Fecha Vencimiento | Código EAN-13 ]
```

#### ¿Cómo modificar `database.py`?
En la función `init_db()`, simplemente cambiás o agregás los campos en el `CREATE TABLE productos`:
```python
# Ejemplo para una Ferretería o Repuestera:
cursor.execute('''
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_barras TEXT UNIQUE,
        nombre TEXT NOT NULL,
        rubro TEXT,                -- Ej: Tornillería, Herramientas, Electricidad
        marca TEXT,                -- Ej: Stanley, Bosch, DeWalt
        medida TEXT,               -- Ej: 1/2 pulgada, 8mm, 100mm
        precio_costo REAL NOT NULL,
        precio_venta REAL NOT NULL,
        stock_actual INTEGER DEFAULT 0,
        stock_minimo INTEGER DEFAULT 5,
        activo INTEGER DEFAULT 1,
        ultima_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
```

---

### PASO 2: Adaptar las Métricas y Unidades en `app.py`

En el negocio actual medimos **Litros y Kilos de grasa**. En otros negocios podés medir:
* **Ferretería / Corralón:** Metros de cable, kilos de clavos, unidades.
* **Pinturería:** Litros totales de pintura vendida.
* **Repuestos o Indumentaria:** Cantidad de piezas por categoría (ej: Motor, Frenos, Suspensión).

Solo cambiás la consulta SQL en la función `index()` de `app.py`:
```python
# En lugar de sumar litros, agrupás por categoría o rubro:
cursor.execute('''
    SELECT 
        rubro, 
        SUM(cantidad) as unidades_vendidas, 
        SUM(precio_total) as facturacion
    FROM historial_ventas 
    WHERE strftime('%Y-%m', fecha) = ?
    GROUP BY rubro 
    ORDER BY facturacion DESC
''', (mes_seleccionado,))
metricas_rubro = cursor.fetchall()
```

---

### PASO 3: Cambiar el Frontend (`templates/index.html`)

El frontend está centralizado en un único archivo HTML con CSS embebido, lo que hace que cambiar la estética o la identidad de marca sea cuestión de minutos:

#### A. Cambiar la paleta de colores de la empresa
En el bloque `<style>` al principio de `index.html`:
* **Ferretería / Construcción:** Reemplazás `#2ecc71` (verde) por `#e67e22` (naranja industrial) o `#f39c12` (amarillo Caterpillar).
* **Repuestera / Taller:** Reemplazás `#2ecc71` por `#e74c3c` (rojo competición) y fondo `#121212`.
* **Farmacia / Dietética:** Reemplazás `#2ecc71` por `#00b894` (verde menta) y `#0984e3` (azul médico).

#### B. Cambiar el nombre y logo de los tickets PDF
En la función JavaScript `descargarRemitoTicketPDF()` y `descargarTicketRemitoHistoricoPDF()`:
```javascript
// Cambiar el encabezado del ticket impreso:
doc.text("FERRETERÍA INDUSTRIAL SUR SRL", 40, y, { align: "center" });
doc.text("CUIT: 30-12345678-9 | Tel: 11-4567-8900", 40, y + 4, { align: "center" });
```

---

## 🚀 Checklist Comercial: Instalación en una nueva PyME en 10 minutos

Cuando vayas a instalarle el sistema a un cliente nuevo:

1. **Crear una carpeta limpia** en la computadora del cliente (ej: `C:\SistemaComercial`).
2. **Copiar los archivos base:** `app.py`, `database.py`, `launcher.py`, carpeta `templates/`, carpeta `static/` y los ejecutables `.bat`.
3. **Inicializar la base de datos limpia:**
   * Borrás el archivo `inventario.db` anterior.
   * Al hacer doble clic en `iniciar_administrador.bat`, el sistema detecta que no hay base de datos y crea un archivo `inventario.db` **completamente virgen y listo para cargar**.
4. **Cargar el catálogo inicial del cliente:**
   * Podés usar la pantalla de carga manual (`➕ Cargar Nuevo Producto`) o importar su catálogo desde un Excel usando un script similar a `cargar_listas.py`.
5. **Configurar el acceso directo:**
   * Ejecutás `crear_icono_escritorio_admin.bat` o `crear_icono_escritorio_mostrador.bat` y le dejás el ícono listo en el escritorio del cliente.
6. **Definir la contraseña del dueño:**
   * En la pestaña **Gestión**, cambiás la clave de acceso de administrador (ej: el nombre del negocio o del dueño).

¡Con esta estructura tenés una fábrica de software para comercializar soluciones a medida a decenas de comercios de tu zona con mínimo esfuerzo de desarrollo!
