# 02. Estructura de Archivos y Organización del Código

Este documento explica qué función cumple cada archivo y carpeta dentro del proyecto, cómo interactúan entre sí y cómo está distribuida la lógica en el código.

---

## 📁 Árbol General del Proyecto

```text
INVENTORY-SYSTEM-PyME/
│
├── app.py                     # Controlador Web principal (Servidor Flask, Rutas y API)
├── database.py                # Capa de Acceso a Datos (Esquema SQL, Conexión y Heurísticas)
├── cargar_listas.py           # Pipeline ETL para ingesta y actualización de listas PDF/Excel
├── launcher.py                # Lanzador inteligente de perfiles (Administrador vs Mostrador)
│
├── inventario.db              # Base de datos relacional SQLite 3 (Todos los datos del negocio)
├── perfil.txt                 # Archivo de texto plano local que guarda el modo de la máquina
├── requirements.txt           # Dependencias y librerías externas de Python
│
├── templates/
│   └── index.html             # Vista maestra y única (Single-Page Dashboard con Jinja2)
│
├── static/
│   ├── icono_administrador.ico# Icono de escritorio para el perfil Administrador
│   ├── icono_mostrador.ico    # Icono de escritorio para el perfil Mostrador
│   └── logo_mostrador_azul.jpg# Identidad visual de la empresa para la barra lateral
│
├── docs/                      # Carpeta de documentación técnica y manuales de ingeniería
│   ├── README.md
│   ├── 01_ARQUITECTURA_Y_TECNOLOGIAS.md
│   ├── 02_ESTRUCTURA_DE_ARCHIVOS_Y_CODIGO.md
│   ├── 03_BASE_DE_DATOS_Y_MODELO_LOGICO.md
│   ├── 04_LOGICA_DE_NEGOCIO_Y_FLUJOS.md
│   └── 05_GUIA_DE_REUTILIZACION_PARA_OTRAS_PYMES.md
│
├── iniciar_administrador.bat  # Script de inicio en 1 clic para modo Administrador
├── iniciar_mostrador.bat      # Script de inicio en 1 clic para modo Mostrador
├── crear_icono_escritorio_admin.bat     # Instalador de acceso directo en escritorio
├── crear_icono_escritorio_mostrador.bat # Instalador de acceso directo en escritorio
├── crear_acceso_admin.vbs     # Script VBScript que asigna el icono .ico al acceso directo
└── crear_acceso_mostrador.vbs # Script VBScript que asigna el icono .ico al acceso directo
```

---

## 📄 Detalle Archivo por Archivo

### 1. `app.py` — El Corazón del Backend (Controlador Web)
Es el archivo más importante del backend. Contiene la aplicación Flask, el ruteo HTTP, la gestión de sesiones de usuario y los endpoints que consumen los formularios y el código JavaScript.

* **Conexión Robusta (`conectar()`):** Configura la conexión a SQLite con `timeout = 10.0` y activa claves foráneas (`PRAGMA foreign_keys = ON`) y tiempo de espera (`PRAGMA busy_timeout = 5000`).
* **Controlador Principal (`@app.route('/') -> index()`):**
  * Recupera los productos del catálogo activo y depósito.
  * Calcula las métricas de litros de aceites, kilos de grasa y facturación del mes seleccionado o histórico.
  * Agrupa las viscosidades y clasifica tipos de grasa.
  * Obtiene el listado de remitos de auditoría con sus totales.
  * Detecta productos faltantes o con stock bajo para armar la lista de reposición.
* **Control de Stock y Ventas:**
  * `@app.route('/confirmar_remito', methods=['POST'])`: Endpoint transaccional que recibe el carrito JSON, descuenta el stock de cada producto, calcula los litros vendidos y registra cada fila en `historial_ventas`.
  * `@app.route('/anular_remito', methods=['POST'])`: Permite anular un remito erróneo, devolviendo automáticamente las unidades al stock y restando el volumen de las métricas.
* **API Endpoints JSON:**
  * `/api/remito_detalle?fecha=...`: Devuelve en formato JSON la lista completa de productos despachados en un remito puntual para renderizar el modal interactivo.
  * `/api/reservas_pendientes`: Consulta rápida para actualizar la bandeja de reservas del operario sin recargar la página.
* **Sincronización en Red Wi-Fi:**
  * `/api/sync/enviar_mostrador`: Ejecuta un checkpoint de SQLite (`PRAGMA wal_checkpoint(FULL)`) y envía el archivo `inventario.db` a la IP de la máquina de Mostrador.
  * `/api/sync/recibir_db`: Recibe el archivo de base de datos con un token seguro (`X-Sync-Token`), genera un backup previo automático y reemplaza la base local.
* **Manejo Global de Errores (`@app.errorhandler`):** Captura cualquier excepción de SQLite o del servidor para evitar la clásica "pantalla blanca de error 500", registrando el log y redirigiendo elegantemente al usuario.

---

### 2. `database.py` — Persistencia y Algoritmos de Clasificación
Contiene la estructura de la base de datos y los algoritmos matemáticos y lingüísticos de detección de productos.

* **`init_db()`:** Crea las tablas (`productos`, `historial_ventas`, `reservas`, `configuracion_admin`) si no existen, genera los índices para búsquedas rápidas y ejecuta migraciones automáticas (`ALTER TABLE ADD COLUMN`) si se agregan campos nuevos.
* **Algoritmo de Extracción de Litros (`extraer_litros_preciso(texto)`):**
  * Utiliza expresiones regulares (`re.search`) para inspeccionar la descripción de un producto.
  * Reconoce tambores (205 L, 200 L), baldes (20 L), bidones (4 L, 5 L), botellas (1 L), envases en centímetros cúbicos (415 cm3, 946 ml -> 0.415 L) y potes de grasa en gramos (900 grs -> 0.900 Kg, 150 grs -> 0.150 Kg).
* **Clasificador Inteligente (`clasificar_viscosidad_o_grasa(nombre, viscosidad, presentacion, tipo)`):**
  * Separa estrictamente aceites líquidos de grasas lubricantes.
  * Si es grasa, clasifica por tipo químico: *Grasa Litio EP-2*, *Grasa Litio Multiuso*, *Grasa Chasis*, *Grasa Rulemanes*, *Grasa Litio Complex*, etc.
  * Si es líquido, normaliza la viscosidad SAE (ej: `15W 40` -> `15W-40`) o clasifica como *2T (2 Tiempos)*, *Refrigerante / Agua* o *Aerosoles / Aditivos*.

---

### 3. `cargar_listas.py` — Ingesta Masiva de Listas de Precios
Es un módulo de ingeniería de datos (ETL: Extraer, Transformar, Cargar):
* Lee archivos oficiales en PDF y planillas Excel enviados por los proveedores (como Gulf Oil Argentina o AMA Lubricantes).
* Parsea códigos de artículo, descripciones, presentaciones y precios de costo.
* Realiza un `INSERT ... ON CONFLICT(codigo_barras) DO UPDATE`, actualizando precios y presentaciones de productos existentes y agregando los nuevos automáticamente sin duplicar registros.

---

### 4. `launcher.py` y Scripts de Arranque
Permiten que un usuario sin conocimientos informáticos use el sistema como si fuera un programa nativo de Windows:
* **`launcher.py`:** Detecta el archivo `perfil.txt`. Si dice `admin`, arranca con todos los permisos; si dice `mostrador`, restringe las opciones a solo lectura y ventas.
* **`iniciar_administrador.bat` / `iniciar_mostrador.bat`:** Scripts ejecutables que verifican el entorno de Python, activan el servidor en el puerto 5000 y abren el navegador predeterminado de Windows automáticamente.
* **`crear_acceso_admin.vbs`:** Script en VBScript que crea un acceso directo en el Escritorio de Windows con su respectivo icono `.ico` personalizado.

---

### 5. `templates/index.html` — La Vista Maestra (Frontend Unificado)
Toda la interfaz del usuario vive en este archivo. Utiliza el motor de plantillas **Jinja2** de Flask:
* **Estructura por Pestañas (Tabs):**
  * `#inicio`: Dashboard principal con accesos rápidos y estado del negocio.
  * `#inventario`: Catálogo del mostrador con buscador predictivo y ajuste de stock.
  * `#ventas`: Módulo de armado y confirmación de remitos / tickets.
  * `#reservas`: Bandeja de reservas remotas y lector de cámara.
  * `#metricas`: Gráficos, consumo de litros por marca, consumo de grasas en kg y resumen de cierres mensuales con descarga a Excel y PDF.
  * `#gestion_listas`: Auditoría de remitos cargados, depósito de inactivos (+60 días) y papelera de bajas con vaciado definitivo.
* **Componentes Modales:**
  * `#modal-detalle-remito`: Ventana emergente con el desglose de productos de un remito.
  * `#modal-sync`: Panel de sincronización Wi-Fi en 1 clic y respaldo para pendrive.
  * `#modal-pin-admin`: Diálogo para desbloquear el modo Administrador con contraseña.
