# Referencias de Arquitectura

El diseño de este backend modular está inspirado en patrones avanzados para aplicaciones Serverless LLM.

## Enfoque Principal
- **Framework de Transporte**: FastAPI
- **Computación Serverless**: Vercel Serverless Functions (`@vercel/python`)
- **Almacenamiento Distribuido (Data Layer)**: Supabase PostgreSQL
- **Orquestación**: Patrón Repository / Services

## Patrones LLM Integrados
- Inyección de Prompt Dinámico (Dynamical Context).
- Sliding Window Memory para preservar historial evitando agotamiento de tokens.
- Respuestas estructuradas forzosas (`json`).

## Herramientas de Calidad (QA)
- `pytest -v` (con flujos asíncronos en un event loop dedicado).
