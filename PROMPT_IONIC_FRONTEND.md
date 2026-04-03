# 📱 Prompt Maestro: Desarrollo de AgroNexus AI Frontend (Ionic + Vue/Vanilla)

Este prompt está diseñado para generar una aplicación móvil de alto impacto utilizando **Ionic con Vue.js** (o Vanilla JS) que consuma el backend de AgroNexus AI.

---

### 🚀 Prompt Detallado

**Contexto del Sistema:**
"Estamos desarrollando **AgroNexus AI**, un ecosistema AgTech para monitoreo hidropónico proactivo. El backend (FastAPI) ya está operativo con endpoints de telemetría, historial y un chat experto. Necesito construir la aplicación móvil con **Ionic + Vue.js (Composition API)** con un enfoque en **Experiencia de Usuario Premium y Visualización de Datos Dinámica**."

**Especificaciones Técnicas del Frontend:**
1.  **Arquitectura de Datos**: implementar un Store (Pinia/Vuex) o un servicio reactivo que gestione la telemetría en tiempo real consultando `http://localhost:8000/dashboard/latest`.
2.  **Dashboard Visual**:
    *   Tarjetas dinámicas para **Temperatura, Humedad, pH y EC**.
    *   Uso de indicadores de color (Verde = OK, Rojo = Alerta) basados en los rangos del sistema.
    *   Sección de 'Salud del Sistema' basada en `GET /dashboard/state`.
3.  **Analítica e Historial**: Consumir `GET /dashboard/history` y usar **Chart.js** para renderizar gráficos de líneas que muestren la tendencia de las últimas 5 horas.
4. **Chat Experto Interactivo**: 
    *   **Vista de Mensajes**: Implementar scroll automático, burbujas diferenciadas (Usuario vs IA) y renderizado de **Markdown** para las respuestas detalladas del asistente.
    *   **Tarjetas de Acción IoT**: Si la respuesta de la IA incluye el objeto `actions`, el chat debe renderizar automáticamente una **tarjeta de acción interactiva** (ej: un cuadro con icono de ventilador y estado 'Encendiendo...') debajo del mensaje de texto.
    *   **Estados de Carga**: Añadir un componente de 'El asistente está analizando los sensores...' mientras se espera el `POST /chat`.
5.  **Control de Modo**: Un switch táctil para cambiar entre `AUTO` y `MANUAL` mediante `POST /dashboard/mode`.

**Identidad Visual (AgTech Premium):**
- **Tema**: Modo Oscuro (Dark Mode) con contrastes en **verde neón (#2ecc71)** y **azul cobalto**.
- **Estética**: Glassmorphism (paneles translúcidos) y tipografía moderna (Inter o Outfit).
- **UX**: Micro-interacciones al recibir datos y transiciones elegantes entre el Dashboard y el Chat.

**Instrucción Final para la IA:**
"Genera el código base del componente principal (`App.vue`), el servicio de API (`api.js/ts`) y la vista del Dashboard, asegurando que la estructura sea escalable y el diseño sea visualmente impactante, digno de una solución de inteligencia artificial de vanguardia."

---

### 🛠️ Comandos de Inicio Sugeridos

Si usas **Vue.js** (Sugerido por Ionic):
```bash
ionic start agronexus-ui tabs --type=vue --capacitor
```

Si prefieres **Vanilla JS**:
```bash
# Nota: Ionic Vanilla usa Web Components directamente
ionic start agronexus-ui tabs --type=custom
```
