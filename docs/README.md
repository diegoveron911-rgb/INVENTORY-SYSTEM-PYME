# 📚 Memoria Técnica y Manual de Arquitectura de Software
## Sistema de Inventario, Gestión de Stock, Ventas y Métricas para PyMEs

¡Bienvenido a la documentación técnica y memoria de ingeniería del sistema! Este conjunto de documentos fue redactado para brindarte una comprensión profunda, pedagógica y práctica de todos los componentes informáticos, lógicos y estructurales que componen este software.

Esta base te servirá tanto para dominar el mantenimiento del sistema actual de lubricantes (**Óleos Minerales**) como para utilizar este **Backend robusto como plantilla reutilizable** para adaptar el sistema a cualquier otro rubro de PyME (ferreterías, repuesteras, pinturerías, corralones, minimarkets, etc.).

---

### 🗺️ Índice de Contenidos

| Documento | Descripción |
| :--- | :--- |
| **[01. Arquitectura y Tecnologías](./01_ARQUITECTURA_Y_TECNOLOGIAS.md)** | Visión global cliente-servidor, stack tecnológico (Python, Flask, SQLite, HTML5, CSS3, JavaScript), diferencia entre Java y JS, qué es un archivo `.db`. |
| **[02. Estructura de Archivos y Código](./02_ESTRUCTURA_DE_ARCHIVOS_Y_CODIGO.md)** | Qué hace cada archivo del proyecto (`app.py`, `database.py`, `cargar_listas.py`, `launcher.py`, scripts `.bat` y `.vbs`, plantilla HTML). |
| **[03. Base de Datos y Modelo Lógico](./03_BASE_DE_DATOS_Y_MODELO_LOGICO.md)** | Tablas (`productos`, `historial_ventas`, `reservas`), claves primarias y foráneas, prevención de bloqueos con WAL y Busy Timeout. |
| **[04. Lógica de Negocio y Flujos](./04_LOGICA_DE_NEGOCIO_Y_FLUJOS.md)** | Algoritmos de descuento de stock (cajas vs botellas), métricas (Litros vs Kilos), roles (Admin vs Mostrador), lector de barras y sincronización Wi-Fi. |
| **[05. Guía de Reutilización para Otras PyMEs](./05_GUIA_DE_REUTILIZACION_PARA_OTRAS_PYMES.md)** | Manual paso a paso para clonar este Backend y crear sistemas a medida para otros comercios cambiando el Frontend. |
| **[06. Caso Real: Auditoría Forense y Conciliación](./06_CASO_REAL_AUDITORIA_Y_CONCILIACION_DE_STOCK.md)** | Caso práctico real (Sept 2026): resolución de discrepancia de 2.100 L vs Excel, corrección de bug de grasas, conciliación L/Kg y migración WAL. |

---

### 💡 Filosofía de Diseño del Sistema
1. **100% Autónomo y Offline-First:** No depende de internet ni de servidores en la nube costosos. Funciona en red local o en una sola máquina.
2. **Cero Mantenimiento Complejo:** Corre sobre SQLite y Python nativo, sin necesidad de instalar servicios pesados como MySQL, PostgreSQL o Docker en las máquinas de los clientes.
3. **Alto Rendimiento en Máquinas Antiguas:** Diseñado con algoritmos ligeros, lectura WAL de bajo consumo de CPU y RAM, e interfaces reactivas en JavaScript nativo.
