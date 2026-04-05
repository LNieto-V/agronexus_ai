---
name: supabase-auth-database
description: >
  Skill para la integración completa con Supabase: autenticación JWT, 
  esquema de base de datos PostgreSQL, políticas de Row Level Security (RLS), 
  y persistencia de datos de sensores y chat para AgroNexus AI.
version: "1.0"
compatibility:
  - claude-code
  - cursor
  - antigravity
---

# 🗄️ AgroNexus AI — Supabase Auth & Database Skill

Este skill documenta la capa de persistencia y seguridad del ecosistema AgroNexus,
construida sobre Supabase (PostgreSQL gestionado + Auth + RLS).

## Capacidades

### 1. Autenticación Dual

#### JWT (Usuarios Finales — Web/Móvil)
- Supabase Auth genera tokens JWT al hacer login.
- El backend valida los tokens en `app/services/security.py` → `get_current_user()`.
- Algoritmos soportados: `HS256`, `HS384`, `HS512`, `ES256`.
- El campo `sub` del JWT contiene el `user_id` para filtrar datos por usuario.
- Variable de entorno requerida: `SUPABASE_JWT_SECRET` o `SUPABASE_JWK`.

#### API Keys (Dispositivos Embebidos — ESP32)
- Se generan con `generate_api_key()` (prefijo `agnx_` + 32 bytes aleatorios).
- Se almacenan como hash SHA-256 en la tabla `api_keys`.
- Permisos granulares: `read` (solo lectura) y `write` (telemetría + control).
- Un key de tipo `write` hereda permisos de `read` (jerarquía de permisos).
- Se registra `last_used_at` en cada uso para auditoría.

### 2. Esquema de Base de Datos

#### `sensor_data` — Telemetría IoT
| Columna       | Tipo          | Descripción                        |
|---------------|---------------|------------------------------------|
| `id`          | UUID (PK)     | Identificador único auto-generado  |
| `user_id`     | UUID (FK)     | Referencia a `auth.users(id)`      |
| `temperature` | FLOAT         | Temperatura en °C                  |
| `humidity`    | FLOAT         | Humedad relativa en %              |
| `light`       | FLOAT         | Intensidad lumínica (lux)          |
| `ph`          | FLOAT         | pH del sustrato                    |
| `ec`          | FLOAT         | Conductividad eléctrica (mS/cm)   |
| `created_at`  | TIMESTAMPTZ   | Timestamp del registro             |

**Índice optimizado**: `idx_sensor_data_user_created` sobre `(user_id, created_at DESC)`
para consultas históricas eficientes.

#### `chat_history` — Memoria Conversacional
| Columna      | Tipo         | Descripción                         |
|--------------|--------------|-------------------------------------|
| `id`         | UUID (PK)    | Identificador único auto-generado   |
| `user_id`    | UUID (FK)    | Referencia a `auth.users(id)`       |
| `role`       | TEXT         | `user` o `ai` (CHECK constraint)   |
| `message`    | TEXT         | Contenido del mensaje               |
| `created_at` | TIMESTAMPTZ  | Timestamp del mensaje               |

#### `api_keys` — Gestión de Dispositivos IoT
| Columna       | Tipo         | Descripción                       |
|---------------|--------------|-----------------------------------|
| `user_id`     | UUID (FK)    | Propietario de la key             |
| `key_hash`    | TEXT (PK)    | Hash SHA-256 de la API key        |
| `key_type`    | TEXT         | `read` o `write` (CHECK)         |
| `last_used_at`| TIMESTAMPTZ  | Último uso registrado             |
| `created_at`  | TIMESTAMPTZ  | Fecha de creación                 |

### 3. Row Level Security (RLS)
- **Habilitado** en las tres tablas (`sensor_data`, `chat_history`, `api_keys`).
- **Política**: Cada usuario solo puede ver sus propios datos (`auth.uid() = user_id`).
- **Bypass**: El backend usa `SUPABASE_SERVICE_ROLE_KEY` para operaciones administrativas
  que requieren acceso cross-user.

### 4. Servicio de Persistencia (`SupabaseService`)
Clase singleton en `app/services/supabase_service.py` con los siguientes métodos:

| Método                     | Descripción                                      |
|----------------------------|--------------------------------------------------|
| `get_sensor_history()`     | Últimos 20 registros de sensores del usuario      |
| `get_latest_sensors()`     | Último registro de sensores (para RAG en tiempo real) |
| `insert_sensor_data()`     | Inserta telemetría asociada al `user_id`          |
| `save_chat_message()`      | Persiste un mensaje de chat (user o ai)           |
| `get_chat_history()`       | Últimos 6 mensajes formateados para inyección en prompt |

## Archivos Clave
- `supabase_schema.sql`: Definición completa de tablas, índices y políticas RLS.
- `app/services/supabase_service.py`: Cliente singleton con métodos CRUD.
- `app/services/security.py`: Validación JWT y API Keys.
- `app/routers/auth.py`: Endpoints HTTP para gestión de keys.
- `app/config.py`: Variables de entorno (`SUPABASE_URL`, `SUPABASE_KEY`, etc.).

## Buenas Prácticas
1. **Siempre filtrar por `user_id`** en todas las consultas para respetar el aislamiento de datos.
2. **Usar `service_role_key`** solo en el backend, nunca exponerla al frontend.
3. **Nunca almacenar API keys en texto plano** — siempre hashear con SHA-256.
4. **Índices DESC en `created_at`** para optimizar consultas de "último dato" y "historial reciente".
5. **Graceful degradation**: Si Supabase no está configurado, el servicio retorna datos vacíos sin crashear.
