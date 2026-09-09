# 01. Arquitectura del Sistema y Tecnologías

Este documento detalla los fundamentos informáticos, el modelo arquitectónico y las tecnologías que hacen funcionar este software de inventario y gestión comercial.

---

## 1. Modelo Arquitectónico: Cliente - Servidor Web Local (LAN)

El sistema utiliza una arquitectura **Cliente-Servidor Web Local**. 

```
┌────────────────────────────────────────────────────────┐
│                   DISPOSITIVOS CLIENTE                 │
│  (Navegador Web: Chrome, Edge, Safari, Celular)        │
│  - Renderizado HTML5 / CSS3                            │
│  - Lógica interactiva en JavaScript (Vanilla)          │
│  - Generación de tickets PDF en cliente (jsPDF)        │
└───────────────────────────▲────────────────────────────┘
                            │  Peticiones HTTP (GET / POST / AJAX JSON)
                            │  Puerto 5000 (Red Local / Wi-Fi o localhost)
┌───────────────────────────▼────────────────────────────┐
│                    SERVIDOR BACKEND                    │
│  (Python 3 + Microframework Flask)                     │
│  - Enrutamiento (Endpoints y Controladores)            │
│  - Lógica de negocio (Descuento de stock, cajas, métricas)
│  - Seguridad y roles (Sesiones de Admin y Mostrador)   │
│  - API REST interna para sincronización y reportes     │
└───────────────────────────▲────────────────────────────┘
                            │  Conexión SQLite nativa (Timeout 10s + WAL)
┌───────────────────────────▼────────────────────────────┐
│                  MOTOR DE PERSISTENCIA                 │
│  (SQLite 3 - Archivo `inventario.db`)                  │
│  - Base de datos relacional transaccional (ACID)       │
│  - Cero dependencias externas (Serverless)             │
│  - Registro WAL (-wal) y memoria compartida (-shm)     │
└────────────────────────────────────────────────────────┘
```

### ¿Por qué esta arquitectura es ideal para PyMEs?
1. **Multiplataforma sin instalaciones complejas:** El servidor corre en una PC con Windows. Las demás computadoras (mostrador, caja, celular del operario en el depósito) acceden simplemente abriendo el navegador en `http://IP_DE_LA_PC:5000`.
2. **Independencia de Internet:** Todo funciona en red local; si se corta la fibra óptica o el Wi-Fi externo, el negocio sigue despachando y facturando con total normalidad.
3. **Cero costos de infraestructura:** No requiere pagar servidores en la nube (AWS, Azure) ni bases de datos costosas.

---

## 2. Tecnologías Empleadas

### 🐍 A. Backend: Python 3 + Flask
* **Python 3:** Lenguaje de programación interpretado de alto nivel, caracterizado por su sintaxis clara, robustez y rica biblioteca estándar.
* **Flask:** Es un *microframework* web para Python. A diferencia de frameworks monolíticos y pesados como Django, Flask es minimalista, ultra veloz y te da control absoluto sobre cada consulta SQL, ruta y lógica de negocio sin imponer estructuras rígidas.
* **Librerías Python utilizadas:**
  * `sqlite3`: Controlador nativo de Python para conectarse al archivo `.db`.
  * `requests`: Para enviar la base de datos a través de Wi-Fi de una PC a otra.
  * `pandas` / `openpyxl`: Para leer y procesar listas de precios en Excel.
  * `pypdf` / `pdfplumber`: Para la extracción automatizada de tablas desde archivos PDF de proveedores.

---

### 🌐 B. Frontend: HTML5 + CSS3 + JavaScript (Vanilla)
* **HTML5:** Es el lenguaje de marcado que estructura toda la información visible en la pantalla (tablas, formularios, botones, tarjetas de métricas, ventanas modales).
* **CSS3:** Es el lenguaje de estilos que define la apariencia visual del sistema:
  * **Tema Oscuro Premium (Dark Theme):** Fondo `#161922`, tarjetas `#202430`, acentos verdes `#2ecc71` y acentos azules `#3498db`, diseñado para no cansar la vista en jornadas de 8 a 10 horas frente a la pantalla.
  * **Flexbox y CSS Grid:** Para que la interfaz se reorganice armónicamente en monitores anchos de PC o pantallas táctiles de celulares.
  * **Diseño Responsivo:** En modo Mostrador, la barra lateral se adapta horizontalmente para optimizar el 100% del espacio útil.
* **JavaScript (Vanilla / ES6+):** Es el lenguaje de programación que se ejecuta dentro del navegador del usuario. Es el motor interactivo que:
  * Controla el carrito de ventas en tiempo real sin recargar la página.
  * Filtra tablas al instante mientras el usuario escribe en el buscador.
  * Abre y cierra las ventanas modales de edición y detalles de remito.
  * Comunica el navegador con el backend mediante `fetch()` (llamadas AJAX asíncronas).

---

### 💡 Nota Pedagógica Crucial: ¿Java y JavaScript son lo mismo?
**NO, son dos tecnologías completamente distintas.** 
* **Java:** Es un lenguaje compilado de propósito general creado por Sun Microsystems (hoy Oracle). Requiere la máquina virtual JVM, es muy estructurado y suele usarse en grandes sistemas bancarios o aplicaciones Android nativas.
* **JavaScript (JS):** Es el lenguaje dinámico que entienden todos los navegadores web del mundo. Su nombre fue una estrategia de marketing en los años 90, pero **no tiene ninguna relación con Java**.
* **En este sistema se usa JavaScript (JS)** en el navegador, **NO Java**.

---

### 📦 C. Librerías Frontend Integradas
Para mantener el sistema ultra liviano, no se usan frameworks pesados (como React o Angular), sino librerías especializadas:
1. **TomSelect.js:** Convierte los `<select>` estándar en buscadores predictivos rápidos donde podés tipear "15w40" y encontrar el lubricante entre cientos en milisegundos.
2. **Html5-QRCode:** Motor en JavaScript que activa la cámara web o la cámara trasera del celular para escanear códigos de barras físicos (EAN-13, Code 128) sin comprar pistolas lectoras caras.
3. **jsPDF:** Biblioteca que genera documentos PDF directamente dentro de la memoria RAM del navegador. Gracias a esto, los tickets de remito y cierres de caja en 80 mm se crean al instante sin sobrecargar el procesador del servidor.

---

### 🗄️ D. Base de Datos: ¿Qué es un archivo `.db` (SQLite 3)?
El archivo **`inventario.db`** es una base de datos relacional completa contenida en un **único archivo físico binario**.

* **¿Por qué SQLite?** 
  * Es el motor de base de datos más utilizado del mundo (está en todos los teléfonos iPhone, Android, aviones y navegadores).
  * Es **Serverless (sin servidor):** No hay un proceso demonio (como `mysqld` o `postgres`) corriendo en segundo plano que consuma memoria RAM cuando nadie lo usa. El motor está embebido directamente dentro de Python.
  * **Portabilidad extrema:** Para hacer un respaldo del negocio completo, solo hay que copiar el archivo `inventario.db` a un pendrive.
* **Modo WAL (Write-Ahead Logging):**
  * Por defecto, SQLite bloquea todo el archivo cuando alguien escribe. En este sistema activamos `PRAGMA journal_mode = WAL`.
  * En modo WAL, las lecturas no bloquean a las escrituras y las escrituras no bloquean a las lecturas. Esto permite que el operario esté consultando precios en el mostrador mientras el administrador actualiza stock simultáneamente.
* **Tolerancia a Concurrencia (`busy_timeout = 5000`):**
  * Si dos procesos intentan escribir en el mismo milisegundo, en lugar de tirar el error `database is locked`, SQLite espera pacientemente hasta 5 segundos para que la otra transacción termine.
