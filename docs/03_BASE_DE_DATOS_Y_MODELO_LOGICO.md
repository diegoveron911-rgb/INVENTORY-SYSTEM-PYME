# 03. Base de Datos y Modelo Lógico Relacional

Este documento describe en profundidad el modelo de datos relacional del sistema (`inventario.db`), la estructura de sus tablas, las relaciones de claves foráneas, las estrategias de integridad referencial y las técnicas de prevención de bloqueos de concurrencia.

---

## 🗄️ Diagrama Entidad - Relación (ER)

```
┌───────────────────────────────────────┐
│              PRODUCTOS                │
├───────────────────────────────────────┤
│ PK  id                INTEGER         │
│     codigo_barras     TEXT (UNIQUE)   │
│     nombre            TEXT            │
│     viscosidad        TEXT            │
│     presentacion      TEXT            │
│     bulto_unidades    INTEGER         │
│     litros_unitarios  REAL            │
│     precio_costo      REAL            │
│     precio_venta      REAL            │
│     stock_actual      INTEGER         │
│     stock_minimo      INTEGER         │
│     ubicacion         TEXT            │
│     ultima_venta      TIMESTAMP       │
│     activo            INTEGER (0 ó 1) │
│     fecha_baja        TIMESTAMP       │
│     tipo_producto     TEXT            │
└───────────────────▲───────────────────┘
                    │ 1
                    │
                    │ 0..* (FK producto_id)
        ┌───────────┴───────────┐
        │                       │
┌───────┴─────────────────┐ ┌───┴─────────────────────┐
│    HISTORIAL_VENTAS     │ │        RESERVAS         │
├─────────────────────────┤ ├─────────────────────────┤
│ PK  id            INT   │ │ PK  id            INT   │
│ FK  producto_id   INT   │ │ FK  producto_id   INT   │
│     nombre_prod   TEXT  │ │     empleado_nom  TEXT  │
│     marca         TEXT  │ │     cantidad      INT   │
│     viscosidad    TEXT  │ │     estado        TEXT  │
│     presentacion  TEXT  │ │     fecha         TIME  │
│     cantidad      INT   │ └─────────────────────────┘
│     litros_totales REAL │
│     precio_total  REAL  │
│     fecha         TIME  │ (Agrupador de Remito)
│     tipo_producto TEXT  │
└─────────────────────────┘
```

---

## 📋 Diccionario de Datos: Tablas y Campos

### 1. Tabla `productos` (Catálogo Maestro)
Almacena el catálogo completo de lubricantes, aceites, grasas y refrigerantes.

| Campo | Tipo | Restricción | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Identificador numérico único de cada artículo. |
| `codigo_barras`| TEXT | UNIQUE (Opcional) | Código de barras del producto (EAN-13, SKU de fábrica). |
| `nombre` | TEXT | NOT NULL | Nombre comercial y línea (ej: `GULF - Gulf Pride 4T 20W-50`). |
| `viscosidad` | TEXT | NULLABLE | Grado de viscosidad SAE (ej: `15W-40`, `20W-50`, `N/A`). |
| `presentacion` | TEXT | NULLABLE | Tipo de envase (ej: `Bulto x12`, `Balde 20L`, `Tambor 205L`). |
| `bulto_unidades`| INTEGER | DEFAULT 1 | Cantidad de unidades sueltas que contiene una caja o bulto cerrado. |
| `litros_unitarios`| REAL | DEFAULT 1.0 | Volumen real en litros o kilos de 1 unidad individual. |
| `precio_costo` | REAL | NOT NULL | Precio de costo neto por bulto según lista del proveedor. |
| `precio_venta` | REAL | NOT NULL | Precio de venta final por bulto cerrado. |
| `stock_actual` | INTEGER | DEFAULT 0 | Cantidad de unidades sueltas disponibles en depósito/mostrador. |
| `stock_minimo` | INTEGER | DEFAULT 5 | Umbral para alertar reposición cuando el stock es bajo. |
| `ubicacion` | TEXT | DEFAULT 'MOSTRADOR'| `'MOSTRADOR'` o `'DEPOSITO_60D'` (artículos sin rotación). |
| `ultima_venta` | TIMESTAMP| DEFAULT CURRENT_TIMESTAMP | Fecha y hora de la última salida de stock. |
| `activo` | INTEGER | DEFAULT 1 | `1` = Producto activo en catálogo; `0` = En papelera de reciclaje. |
| `fecha_baja` | TIMESTAMP| NULLABLE | Momento en el que el producto fue enviado a la papelera. |
| `tipo_producto`| TEXT | DEFAULT 'LIQUIDO' | Clasificación maestra: `'LIQUIDO'` (aceites) o `'GRASA'` (grasas). |

---

### 2. Tabla `historial_ventas` (Auditoría de Salidas y Remitos)
Registra cada ítem vendido. Esta tabla es el **libro diario contable de auditoría**.

* **Agrupación de Remitos:** Múltiples registros con la **misma `fecha` (timestamp)** componen un único remito o ticket. Si un cliente compra 7 productos en un solo remito, se insertan 7 filas con idéntica marca de tiempo.
* **Preservación Inmune (`nombre_producto`):** Se almacena el nombre completo del producto al momento de la venta. Si el producto se modifica o borra en el catálogo dentro de 3 años, el remito histórico conservará intacto su nombre exacto.
* **Desvinculación Segura (`producto_id` opcional):** `producto_id` es una clave foránea (FK) hacia `productos(id)`. Si un producto dado de baja en la papelera se elimina definitivamente, se ejecuta `SET producto_id = NULL`. De esta forma, **no se borra la venta, ni los litros, ni la facturación**, y nunca salta el error de `FOREIGN KEY constraint failed`.

---

### 3. Tabla `reservas` (Solicitudes Remotas)
Gestiona los pedidos solicitados por operarios desde el celular o desde el mostrador antes de confirmar el remito.

| Estado | Significado |
| :--- | :--- |
| `PENDIENTE` | La reserva fue enviada y está a la espera de aprobación del Administrador. |
| `APROBADO` | El Administrador validó la reserva y el stock queda apartado. |
| `RECHAZADO` | La solicitud fue cancelada y el stock se restituye automáticamente. |

---

### 4. Tabla `configuracion_admin`
Almacena el PIN / contraseña de acceso de administrador en texto para permitir el desbloqueo rápido desde equipos clientes.

---

## 🛡️ Técnicas Avanzadas de Integridad y Concurrencia

### 1. El ciclo de vida de un producto: Baja Lógica vs Borrado Físico
* **Baja Lógica (Soft Delete - Enviar a Papelera):**
  * No borra el registro de la base. Ejecuta:
    ```sql
    UPDATE productos SET activo = 0, fecha_baja = CURRENT_TIMESTAMP WHERE id = ?;
    ```
  * El producto desaparece inmediatamente del mostrador y del buscador para no molestar en la venta diaria, pero se puede restaurar en cualquier momento con un clic.
* **Borrado Físico Definitivo (Vaciar Papelera):**
  * Para vaciar la papelera sin romper la integridad referencial de SQLite:
    1. **Desvinculación:** Se desvinculan las ventas históricas (`UPDATE historial_ventas SET producto_id = NULL WHERE producto_id IN (...)`).
    2. **Limpieza de reservas:** Se borran solicitudes de reserva huérfanas de esos productos inactivos.
    3. **Purga física:** Se borran los productos inactivos de `productos`.
    4. **Compactación:** Se ejecuta `VACUUM` para liberar el espacio en el disco físico.

### 2. Prevención de Bloqueos (`database is locked`)
En entornos donde varias PCs consultan SQLite simultáneamente, aplicamos tres mecanismos de ingeniería:
1. **Modo WAL (`PRAGMA journal_mode=WAL`):** Escribe los cambios en un archivo de log separado (`inventario.db-wal`), permitiendo que múltiples usuarios lean la base de datos mientras otro está guardando una venta.
2. **Busy Timeout (`PRAGMA busy_timeout=5000`):** En lugar de rechazar una consulta si la base está escribiendo, SQLite reintenta automáticamente durante hasta 5000 milisegundos.
3. **Manejo Estricto de Conexiones:** Cada función en Python utiliza el patrón:
   ```python
   conn = conectar()
   try:
       # Operaciones SQL
       conn.commit()
   except Exception:
       conn.rollback()  # Revierte la transacción para no dejar bloqueos abiertos
       raise
   finally:
       conn.close()     # Garantiza que el archivo se cierre SIEMPRE
   ```

### 3. Índices Estratégicos de Velocidad
Se crearon índices (`CREATE INDEX`) en las columnas más consultadas:
* `idx_productos_activo_ubicacion`: Filtra en microsegundos los productos activos en mostrador vs depósito.
* `idx_productos_codigo_barras`: Búsqueda instantánea con la pistola lectora o cámara.
* `idx_historial_ventas_fecha`: Agrupa y filtra miles de remitos por mes en menos de 2 milisegundos.
