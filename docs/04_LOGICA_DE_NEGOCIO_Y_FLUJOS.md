# 04. Lógica de Negocio y Flujos Operativos

Este documento explica las matemáticas comerciales, las reglas de negocio y los flujos lógicos implementados en el software.

---

## 1. Venta Dual: Cajas Cerradas vs Unidades Sueltas

En negocios mayoristas y distribuidores de lubricantes, ferreterías o repuesteras, los productos se compran en bultos cerrados pero pueden venderse tanto por caja como por unidad individual (suelta).

### A. Matemática de Precios
* Un bulto tiene `bulto_unidades` (ej: una caja de aceite 15W-40 trae 12 botellas).
* **Precio Venta Bulto:** `$36.000` (el precio de la caja entera).
* **Precio Unitario (calculado en tiempo real):**
  $$\text{Precio Unitario} = \frac{\text{Precio Venta Bulto}}{\text{bulto\_unidades}} = \frac{\$36.000}{12} = \$3.000$$

### B. Descuento de Stock en Depósito
El campo `stock_actual` en la base de datos **siempre almacena unidades sueltas mínimas** (botellas, potes o litros).
* Si el vendedor vende **2 cajas cerradas**:
  $$\text{Descuento} = 2 \times 12 = 24 \text{ unidades descontadas de stock}.$$
* Si el vendedor vende **3 botellas sueltas**:
  $$\text{Descuento} = 3 \text{ unidades descontadas de stock}.$$

### C. Sistema de Bonificación / Regalo (Promociones Proveedor)
En muchas ventas a talleres o clientes grandes, se aplican promociones (ej: *"Comprás 10 cajas y te regalo 1"*).
* El sistema permite ingresar:
  * **Cantidad a Cobrar:** 10 cajas.
  * **Cantidad Bonificada (Regalo):** 1 caja.
* **Resultado Contable:**
  * **Facturación / Total a Pagar:** $10 \times \text{Precio}$. (No cobra la caja de regalo).
  * **Stock Descontado:** $10 + 1 = 11 \text{ cajas}$. (El depósito queda 100% cuadrado sin faltantes inexplicables).

---

## 2. Métricas de Volumen: Aceites (Litros) vs Grasas (Kilos)

Los lubricantes líquidos se miden en **Litros (Lts)**, mientras que las grasas lubricantes se comercializan y miden en **Kilogramos (Kg)**.

### A. Detección Inteligente por Expresiones Regulares
El sistema inspecciona automáticamente el nombre y presentación del producto mediante expresiones regulares (`re.search`):
* Si encuentra `4 KGS`, `18 KG`, `900 GRS`, `150 GR`, detecta que es **Grasa** y convierte el volumen a Kilos:
  $$900 \text{ grs} \longrightarrow 0.90 \text{ Kg}$$
  $$150 \text{ grs} \longrightarrow 0.15 \text{ Kg}$$
* Si encuentra `205 L`, `20 L`, `5 L`, `1 L`, `415 CM3`, detecta que es **Líquido** y convierte a Litros:
  $$415 \text{ cm}^3 \longrightarrow 0.415 \text{ Litros}$$

### B. Segregación en Métricas y Cierres
En la pestaña de **Métricas** y en los **Cierres Mensuales**, el software no mezcla "peras con manzanas":
* Presenta una tarjeta con **💧 Aceites y Líquidos (Litros)**.
* Presenta una tarjeta con **🧈 Grasas Lubricantes (Kilogramos)**.
* Presenta la tabla de consumo clasificada por tipo químico de grasa (*Litio EP-2*, *Multiuso*, *Complex*, *Chasis*) y por viscosidad SAE (*15W-40*, *20W-50*).

---

## 3. Modelo de Seguridad y Roles: Administrador vs Mostrador

El software cuenta con dos modos de operación optimizados para cada puesto de trabajo:

```
                  ┌───────────────────────────────┐
                  │    INICIO DE LA APLICACIÓN    │
                  └───────────────┬───────────────┘
                                  │
                   ¿Qué dice 'perfil.txt' local?
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
          [ perfil: mostrador ]         [ perfil: admin ]
          ┌───────────────────┐         ┌───────────────────┐
          │   MODO MOSTRADOR  │         │ MODO ADMINISTRADOR│
          ├───────────────────┤         ├───────────────────┤
          │ - Solo Consulta   │         │ - Control total   │
          │ - Ventas y Remitos│         │ - Ajuste de Stock │
          │ - Solicitar Reserv│         │ - Edición Precios │
          │ - Oculta Costos   │         │ - Métricas y Cierr│
          │ - Oculta Ajustes  │         │ - Auditoría y Baja│
          │ - Oculta Métricas │         │ - Sincronización  │
          └─────────┬─────────┘         └───────────────────┘
                    │
                    ▼ (Si el usuario necesita editar)
          [ 🔑 Ingresar Contraseña PIN ]
                    │
                    ▼
          Desbloquea sesión Admin en esta PC
```

---

## 4. Flujo de Sincronización en Red Local Wi-Fi

Para conectar la computadora de administración (ej: la oficina de Ramiro) con la computadora del mostrador sin cables:

```
   COMPUTADORA ADMIN (Oficina)              COMPUTADORA MOSTRADOR (Local)
   IP: 192.168.1.100                        IP: 192.168.1.50
┌───────────────────────────────┐        ┌───────────────────────────────┐
│ 1. Ramiro actualiza precios   │        │                               │
│ 2. Clic en "Sincronizar"      │        │                               │
│ 3. PRAGMA wal_checkpoint(FULL)│        │                               │
│    (Vuelca la RAM al disco)   │        │                               │
│ 4. POST /api/sync/recibir_db ──┼───────►│ 5. Valida X-Sync-Token        │
│    (Envía archivo .db vía LAN)│        │ 6. Crea copia de respaldo     │
│                               │        │    inventario.db.backup_fecha │
│                               │        │ 7. Guarda nuevo inventario.db │
│                               │        │ 8. Ejecuta init_db()          │
│ 9. Recibe 'OK Sincronizado'  ◄┼────────┤    (Listo en 1 segundo)       │
└───────────────────────────────┘        └───────────────────────────────┘
```

* **Seguridad:** La comunicación requiere el encabezado HTTP `X-Sync-Token: OLEOS_MINERALES_SYNC_SECURE_TOKEN_2026` para impedir que personas no autorizadas conectadas al Wi-Fi sobreescriban la base de datos.

---

## 5. Integración con Lectores de Códigos de Barras

El sistema soporta dos métodos de lectura física de artículos:
1. **Pistola Lectora USB Física:** Los lectores de código de barras USB emulan un teclado rápido y envían un carácter `Enter` al final. El código JavaScript captura este evento:
   ```javascript
   inputScanner.addEventListener("keypress", function(e) {
       if (e.key === "Enter") {
           e.preventDefault();
           buscarProductoPorCodigo(this.value); // Agrega o abre el producto en el acto
       }
   });
   ```
2. **Cámara de Celular / Tablet (Html5-QRCode):** En dispositivos móviles, activa la cámara trasera. Se incorporó una corrección visual con CSS (`scale(1.35)`) que obliga al operario a alejar el celular unos 20-30 cm del código de barras, facilitando que la lente del teléfono logre el autofoco macro automáticamente.
