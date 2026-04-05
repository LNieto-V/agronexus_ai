---
name: deploy-vercel-production
description: >
  Skill para el despliegue y operación de AgroNexus AI en Vercel (producción), 
  incluyendo configuración de vercel.json, variables de entorno, monitoreo 
  de logs y estrategias de troubleshooting en serverless.
version: "1.0"
compatibility:
  - claude-code
  - cursor
  - antigravity
---

# 🚀 AgroNexus AI — Deploy & Production Skill

Este skill documenta el proceso completo de despliegue del backend FastAPI 
de AgroNexus AI en Vercel como funciones serverless.

## Capacidades

### 1. Configuración de Vercel (`vercel.json`)

```json
{
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```

**Puntos clave:**
- El builder `@vercel/python` empaqueta automáticamente dependencias desde `requirements.txt`.
- Todas las rutas se redirigen al entrypoint `app/main.py` que exporta la instancia `app` de FastAPI.
- Vercel ejecuta cada request como una función serverless (cold start ~1-3s).

### 2. Variables de Entorno en Producción

Configurar en **Vercel Dashboard → Settings → Environment Variables**:

| Variable                    | Descripción                          | Obligatoria |
|-----------------------------|--------------------------------------|-------------|
| `GEMINI_API_KEY`            | API Key de Google Gemini             | ✅          |
| `SUPABASE_URL`              | URL del proyecto Supabase            | ✅          |
| `SUPABASE_KEY`              | Anon key (pública)                   | ✅          |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key (bypass RLS)        | ✅          |
| `SUPABASE_JWT_SECRET`       | Secret para verificar JWTs           | ✅          |
| `SUPABASE_JWK`              | JWK para algoritmo ES256 (opcional)  | ❌          |

### 3. Flujo de Deploy

```bash
# 1. Linkear proyecto (primera vez)
vercel link

# 2. Deploy preview (sin afectar producción)
vercel

# 3. Deploy producción
vercel --prod

# 4. Ver logs en tiempo real
vercel logs --follow
```

**Deploy automático con Git:**
- Cada push a `main` dispara un deploy a producción automáticamente.
- Cada push a otra branch genera un deploy preview con URL única.

### 4. Estructura de Archivos para Deploy

```
agronexus_ai/
├── app/
│   ├── main.py          ← Entrypoint (Vercel lo detecta)
│   ├── config.py        ← Lee variables de entorno
│   ├── routers/         ← Endpoints FastAPI
│   └── services/        ← Lógica de negocio
├── .agent/skills/       ← Skills (no se despliegan, solo docs)
├── requirements.txt     ← Dependencias (Vercel las instala)
├── vercel.json          ← Configuración de build y rutas
└── .env                 ← Variables locales (NO se despliega)
```

### 5. URLs de Producción

| Recurso           | URL                                              |
|--------------------|--------------------------------------------------|
| API Base           | `https://agronexus-ai.vercel.app`                |
| Swagger Docs       | `https://agronexus-ai.vercel.app/docs`           |
| ReDoc              | `https://agronexus-ai.vercel.app/redoc`          |
| Health Check       | `https://agronexus-ai.vercel.app/`               |
| Test Endpoint      | `POST https://agronexus-ai.vercel.app/chat/test` |

### 6. Troubleshooting Común

#### Cold Starts Lentos
- **Causa**: Vercel inicia un nuevo contenedor si la función estuvo inactiva.
- **Solución**: Mantener `requirements.txt` mínimo para reducir tiempo de boot.
- **Impacto**: Primera request ~2-3s, siguientes ~200-400ms.

#### Error 500 en `/chat`
- **Causa probable**: `GEMINI_API_KEY` no configurada o cuota agotada.
- **Diagnóstico**: `vercel logs --follow` para ver el error exacto.
- **Solución**: Verificar variables en Vercel Dashboard.

#### Error 401 en Endpoints Protegidos
- **Causa**: JWT expirado o `SUPABASE_JWT_SECRET` incorrecto.
- **Diagnóstico**: El log muestra el header del JWT y el error específico.
- **Solución**: Verificar que el secret coincida con el de Supabase Dashboard.

#### Import Errors en Vercel
- **Causa**: Dependencia faltante en `requirements.txt`.
- **Diagnóstico**: Build logs en Vercel Dashboard.
- **Solución**: Actualizar `requirements.txt` y re-deploy.

### 7. Monitoreo

```bash
# Ver últimos logs de producción
vercel logs agronexus-ai --follow

# Ver deployments recientes
vercel ls

# Ver detalles de un deployment
vercel inspect <deployment-url>
```

## Archivos Clave
- `vercel.json`: Configuración de build y routing.
- `requirements.txt`: Dependencias Python para el deploy.
- `app/main.py`: Entrypoint de la aplicación FastAPI.
- `app/config.py`: Lectura de variables de entorno.
- `.env.example`: Template de variables necesarias.

## Buenas Prácticas
1. **Nunca commitear `.env`** — usar `.gitignore` y configurar en Vercel Dashboard.
2. **Probar con `/chat/test` primero** — valida que el deploy funciona sin necesidad de JWT.
3. **Mantener `requirements.txt` sincronizado** — `uv pip freeze > requirements.txt` tras agregar dependencias.
4. **Usar deploy preview antes de producción** — `vercel` sin `--prod` genera una URL de prueba.
5. **Monitorear cold starts** — si son > 5s, optimizar imports y reducir dependencias.
