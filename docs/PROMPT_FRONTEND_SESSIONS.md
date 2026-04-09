# 💬 Prompt Maestro: Sincronización Total del Frontend AgroNexus (UI + Auth + Multi-Chat)

Este prompt maestro está diseñado para instruir a una IA de desarrollo (Claude, Cursor, Antigravity) para llevar a cabo la actualización integral de la aplicación frontend **Ionic + Vue.js (Composition API)**. El objetivo es acoplar la UI con la reciente arquitectura modernizada del backend (Supabase Auth, Autenticación IoT, Sistema RAG por Sesiones y Refactor de Telemetría).

---

## 🗄️ Contexto del Backend (Cambios Críticos Ya Aplicados)

El backend de AgroNexus AI ha sido migrado a un modelo asíncrono y de persistencia cloud con Supabase. Debes consumir los siguientes flujos modernizados:

1. **Supabase JWT Authorization**: Todos los endpoints a nivel humano (`/chat`, `/conversations`, `/dashboard/*`) ahora validan el header `Authorization: Bearer <jwt>`.
2. **API Keys de Hardware**: Endpoint `/auth/keys` para expedir llaves. **Importante**: Las llaves de tipo `write` requieren obligatoriamente un `zone_id` para restringir el control de hardware a un invernadero específico.
3. **Conversaciones Aisladas**: En vez de un solo chat global infinito, el backend expone rutas CRUD completas para soportar múltiples discusiones. (`/conversations`).
4. **Perfil de Usuario**: Endpoint `PATCH /auth/profile` para actualizar datos como `full_name` y `role`.

---

## 🚀 Fases de Implementación en el Frontend

### Fase 1 — Análisis Base e Ingesta de Supabase
Analiza todo el proyecto e identifica y ajusta lo siguiente:
1.  **SDK**: Asegura e instala `@supabase/supabase-js`.
2.  **Pinia Central Auth**: Implementa un store global que escuche los cambios de sesión (`onAuthStateChange` de Supabase) para mantener token en memoria.
3.  **Interceptor de API (Fundamental)**: Localiza el `useApi.ts` o el helper HTTP central para inyectar automáticamente el Bearer token (JWT) de la store a *todas* las cabeceras. Agrega ruteo automático al Login en caso de HTTP 401.

### Fase 2 — Sistema de Sub-Chats (La Barra Lateral Mágica)
Usa los componentes nativos `IonSplitPane` y `IonMenu` de Ionic para dividir el Chat en una experiencia Desktop / Mobile:
-   **Store `conversationsStore.ts`**: Crea métodos asíncronos para `fetchConversations`, `selectConversation`, `createConversation`, `renameConversation` y `deleteConversation`.
-   **Sidebar Responsiva**: A la izquierda (visible en tablet/desktop, por drawer-menu en móvil) lista las conversaciones (`GET /conversations`).
-   **Acción Rápida UX Contextual**: Para cada hilo de chat agrega un botón a la derecha (tres puntos verticales) utilizando `IonActionSheet` que ofrezca "Renombrar" o "Eliminar".
-   **Auto-Generación Inteligente**: Si un usuario envía un mensaje de chat desde el estado global (cuando `session_id` está vacío), dispara previamente la creación de una nueva sesión utilizando los primeros 30 caracteres del mensaje como título inicial.

// Un mensaje de chat
interface ChatMessage {
  id: string;
  role: 'user' | 'ai';
  message: string;
  created_at: string;
  session_id: string | null;
}

### Fase 3 — Panel de API Keys para Invernaderos Inteligentes
En la pestaña de Configuración o Control (`TabSystem.vue`):
-   Integra una sección llamada "Gestión de Hardware" o "Credenciales de Campo".
-   Coloca botones prominentes para **Generar Key para Dispositivo** (POST `/auth/keys`).
-   **Seguridad**: Al generar una llave de `write`, solicita al usuario seleccionar primero la **Zona/Invernadero** a la que pertenecerá el dispositivo. No permitas generar llaves de escritura globales.
-   **Feedback Visual**: Cuando el backend devuelva la clave, muéstrala en un `IonAlert` o un modal especializado indicando al usuario: *"Esta es la única vez que verás esta llave maestra, asegúrate de copiarla y quemarla en tu ESP32"* además de ofrecer un botón de *"Copiar al portapapeles"*.
-   **Gestión de Perfil**: Agrega campos en la pestaña de ajustes para que el usuario pueda actualizar su `full_name` y ver su `role` (PATCH `/auth/profile`).

### Fase 4 — Telemetría Activa
Verificar los paneles visuales que reportan el clima y el estado actual al frontend, para asegurar que el sistema esté trayendo la métrica filtrada. Supabase ahora usa RLS (Row Level Security), por ende, no se alteran los endpoints, pero los tiempos de carga en el frontend requieren mejor manejo visuales (agregando `ion-skeleton-text` como preloaders si hace falta).

---

## 🎨 Identidad Visual (AgTech Premium)
*   **Tema Dark Obligatorio**: Esta UI está planificada para el campo o para granjeros; usar el estilo "Dark Mode Glassmorphism" para destacar modernidad sin cansar la vista en monitores de control oscuro.
*   **Micro-Animaciones**: Implementar animaciones a nivel de CSS o de Ionic Native Transitions al cambiar entre diferentes conversaciones de la sidebar para que no brinde la sensación de corte tosco.
*   **Diseño de la Sesión Activa**: Resalta claramente cuál chat en el Sidebar la persona tiene abierto inyectando un margen izquierdo iluminado de color `--agro-primary`.

---

## 🛠️ Comandos de Apoyo para la IA
```bash
# Integración a ejecutar si falta el cliente Supabase
npm install @supabase/supabase-js

# Modificación estructural de la jerarquía (referencia para la IA)
src/stores/authStore.ts            # <- NUEVO O MODIFICAR
src/stores/conversationsStore.ts   # <- NUEVO
src/views/TabChat.vue              # <- MODIFICAR (Insertar Split-Pane y Sidebar)
src/views/TabSystem.vue            # <- MODIFICAR (Gestión API Keys)
```

## ✅ Checklist Strict
- [ ] Todo fetch() maneja interceptor con credencial Supabase y lanza al login con 401.
- [ ] La UI en móviles soporta ver el sidebar mediante menú hamburguesa `IonMenuButton`.
- [ ] Funciona enviar mensajes en hilo y eliminar/renombrar hilos desde el sidebar.
- [ ] Existe generador de llaves y el usuario puede copiar la llave efímera.
- [ ] La interfaz se ve fluida, "AgTech Premium" y utiliza las herramientas de Ionic.
