# Blueprint de Sincronización Frontend: AgroNexus AI

Este documento detalla los cambios técnicos necesarios para alinear el Frontend (Ionic + Vue 3) con la nueva arquitectura modular **DDD-Lite** del Backend.

## 🏗️ 1. Cambio de Paradigma: Backend como Mediador
El Frontend ya **no debe comunicarse directamente con Supabase SDK** para Auth o DB. Ahora todas las interacciones deben pasar por la API del Backend para asegurar la trazabilidad y auditoría.

### 🔑 Autenticación (AuthStore)
- **Antiguo**: `supabase.auth.signInWithPassword(...)`
- **Nuevo**: `POST /api/auth/login` con body `{ email, password }`.
- **Acción**: El Store debe capturar el `access_token` retornado y guardarlo en el almacenamiento local.

## 📡 2. Endpoints y Mapeo de Dominios

| Dominio | Endpoint API | Funcionalidad | Pinia Store |
| :--- | :--- | :--- | :--- |
| **Identity** | `/api/auth/profile` | Actualización de perfil (nombre, rol) | `authStore` |
| **Zones** | `/api/zones` | Gestión CRUD de invernaderos | `iotStore` |
| **IoT** | `/api/dashboard/latest` | Último estado de sensores | `iotStore` |
| **IoT** | `/api/dashboard/history` | Gráficas de tendencias | `iotStore` |
| **IoT** | `/api/iot/stream` | Telemetría SSE (Real-time) | `iotStore` |
| **Chat** | `/api/chat` | Orquestador de IA | `chatStore` |
| **Chat** | `/api/conversations` | CRUD de sesiones de chat | `chatStore` |
| **IoT** | `/api/dashboard/actuator-log`| Logs de bombas/luces | `iotStore` (Paginado) |
| **Chat** | `/api/chat/history` | Mensajes anteriores | `chatStore` (Paginado) |

## 🔢 3. Manejo de Paginación (Limit & Offset)
Para los endpoints marcados como **Paginados**, la API espera:
- `limit`: Cantidad de registros por página (ej: 50).
- `offset`: Número de registros a saltar (ej: `page_number * limit`).

**Recomendación UX**: Implementar "Infinite Scroll" en los logs de actuadores y el historial de chat para una sensación premium y fluida.
El endpoint `/api/chat` ahora devuelve un objeto enriquecido. El frontend debe estar preparado para parsear y actuar:

```typescript
interface ChatResponse {
  response: string;   // Texto del agrónomo IA
  actions: {          // Comandos para actuadores
    device: string;   // "BOMBA", "VENTILADOR"
    action: string;   // "ON", "OFF"
    reason: string;
  }[];
  alerts: string[];   // Mensajes de advertencia
}
```

**Lógica de ejecución visual:**
- Si `actions.length > 0`, disparar una notificación Toast o cambiar el icono del actuador en el dashboard a estado "Ejecutando...".

## 🛠️ 4. Configuración del Cliente API (useApi.ts)
Implementar un interceptor de Axios/Fetch que:
1.  Inyecte `Authorization: Bearer <JWT>`.
2.  Maneje el error `HTTP 429` (Quota de Gemini agotada) con un mensaje amigable: *"La IA está descansando, reintenta en un minuto"*.
3.  Configure el `Content-Type: application/json`.

## 🎨 5. Diseño y UX
- **Micro-interacciones**: Al recibir una acción de IA, el componente del dashboard correspondiente debe resaltar brevemente (ej: pulso verde si se enciende la bomba).
- **Zonas de Cultivo**: Usar el endpoint `/api/zones` para permitir al usuario filtrar el dashboard por invernadero.

---

> [!IMPORTANT]
> **Prompt para el Asistente:**
> "Refactoriza los stores de Pinia y los componentes de UI siguiendo estrictamente las definiciones en `docs/FRONTEND_SYNC_PLAN.md`. Prioriza la migración de Supabase SDK a llamadas API nativas y asegura que el sistema de Chat procese el array de 'actions' correctamente."
