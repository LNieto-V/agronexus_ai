# 📱 Prompt Maestro: Actualización de AgroNexus UI (Seguridad + API Keys)

Este prompt está diseñado para ser utilizado en una IA de desarrollo (como Cursor, Claude o Antigravity) para actualizar la aplicación móvil **Ionic + Vue.js** y que sea compatible con el nuevo sistema de seguridad multi-usuario.

---

### 🚀 Prompt Detallado

**Fase 1: Análisis Inicial del Repositorio**
"Antes de escribir código, realiza un análisis exhaustivo del proyecto actual para identificar:
1.  **Estado de Dependencias**: Verificar si `@supabase/supabase-js` está instalado en `package.json`.
2.  **Arquitectura de Servicios**: Localizar dónde se gestionan las llamadas a la API (usualmente en `src/services/`) para decidir dónde inyectar los interceptores de seguridad.
3.  **Estructura de Vistas**: Identificar en qué pestaña (`tab`) o sección del menú lateral es más apropiado añadir la gestión de dispositivos y API Keys.
4.  **Gestión de Estado**: Confirmar si se está usando Pinia, Vuex o un Proveedor reactivo global para centralizar la sesión de usuario de Supabase."

**Fase 2: Implementación Técnica**

1.  **Autenticación con Supabase**:
    *   Integrar `@supabase/supabase-js`.
    *   Implementar flujos de **Registro (`signUp`)** y **Login (`signInWithPassword`)**.
    *   Gestionar la sesión global del usuario (preferiblemente con **Pinia**).

2.  **Encabezados de Seguridad (JWT)**:
    *   Configurar un interceptor o wrapper de API para inyectar automáticamente el header `Authorization: Bearer <access_token>` en todas las peticiones a FastAPI (`/chat`, `/dashboard/latest`, `/dashboard/history`).
    *   Asegurar que el sistema redirija al login si el token expira (Error 401).

3.  **Gestor de API Keys (Nueva Funcionalidad)**:
    *   **Vista de Ajustes**: Crear una sección donde el usuario pueda gestionar sus llaves.
    *   **Generación Dinámica**: Implementar botones para generar 'Llave de Escritura' (`agnx_w_...`) y 'Llave de Lectura' (`agnx_r_...`) llamando a `POST /auth/keys?key_type={read|write}`.
    *   **Modal de Seguridad**: Mostrar la llave devuelta en un modal prominente. **Nota crítica**: El servidor solo entrega la llave en texto plano una vez al momento de crearla por seguridad. El usuario debe copiarla en ese instante.

4.  **Actualización de Telemetría**:
    *   Verificar que los paneles de datos sigan renderizando correctamente. El backend ahora filtra los sensores automáticamente basándose en el ID del usuario que hace la petición.

**Identidad Visual (AgTech Premium):**
- Mantener la estética **Glassmorphism** y el **Dark Mode**.
- Añadir micro-interacciones al copiar las llaves al portapapeles y transiciones elegantes entre el login y el dashboard.

---

### 🛠️ Comandos de Referencia

Para añadir las dependencias necesarias:
```bash
npm install @supabase/supabase-js
```

Para probar la conexión una vez implementado:
```typescript
// Ejemplo de llamada segura
const { data: { session } } = await supabase.auth.getSession();
const response = await fetch('http://localhost:8000/dashboard/latest', {
  headers: {
    'Authorization': `Bearer ${session?.access_token}`
  }
});
```
