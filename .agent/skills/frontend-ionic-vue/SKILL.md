---
name: frontend-ionic-vue
description: >
  Skill para la arquitectura y desarrollo del frontend de AgroNexus AI con 
  Ionic Framework + Vue 3 (Composition API), Pinia para estado global, 
  composables reutilizables y diseño premium "Modern AgTech SaaS".
version: "1.0"
compatibility:
  - claude-code
  - cursor
  - antigravity
---

# 📱 AgroNexus AI — Frontend Ionic/Vue Skill

Este skill define la arquitectura, patrones y estándares del frontend de AgroNexus AI,
construido como una aplicación móvil-first con Ionic Framework y Vue 3.

## Capacidades

### 1. Stack Tecnológico
- **Framework UI**: Ionic Framework 8+ (componentes nativos cross-platform).
- **Framework JS**: Vue 3 con Composition API (`<script setup lang="ts">`).
- **Estado Global**: Pinia (stores tipados con TypeScript).
- **Routing**: Vue Router con Ionic Tabs Layout.
- **Lenguaje**: TypeScript estricto para type safety.
- **API Client**: Axios/Fetch con interceptores de autenticación.

### 2. Arquitectura de Páginas (Tabs)

| Tab | Nombre            | Ruta             | Descripción                                    |
|-----|-------------------|------------------|------------------------------------------------|
| 1   | Welcome Home      | `/tabs/home`     | Dashboard principal con resumen de sensores    |
| 2   | AI Assistant      | `/tabs/chat`     | Chat conversacional con el agente Gemini       |
| 3   | System Control    | `/tabs/system`   | Panel de control de actuadores y modo del sistema |
| 4   | Telemetry         | `/tabs/telemetry`| Datos históricos y gráficos de sensores        |

### 3. Patrones de Código

#### Composables (Lógica Reutilizable)
```typescript
// composables/useApi.ts
export function useApi() {
  const baseUrl = import.meta.env.VITE_API_URL;
  
  async function authFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const token = localStorage.getItem('supabase_token');
    const res = await fetch(`${baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
    if (!res.ok) throw new Error(`API Error: ${res.status}`);
    return res.json();
  }
  
  return { authFetch };
}
```

#### Pinia Store (Estado Tipado)
```typescript
// stores/chatStore.ts
import { defineStore } from 'pinia';

interface ChatMessage {
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
}

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [] as ChatMessage[],
    isLoading: false,
  }),
  actions: {
    async sendMessage(text: string) { /* ... */ },
    async loadHistory() { /* ... */ },
  },
});
```

### 4. Diseño "Modern AgTech SaaS"

#### Paleta de Colores
```css
:root {
  /* Primarios — Verde Agrícola */
  --agro-primary: #2dd36f;
  --agro-primary-dark: #1a9e4e;
  --agro-primary-glow: rgba(45, 211, 111, 0.15);
  
  /* Fondo — Dark Mode Premium */
  --agro-bg-deep: #0a0f1a;
  --agro-bg-card: rgba(20, 30, 50, 0.85);
  --agro-bg-glass: rgba(255, 255, 255, 0.05);
  
  /* Acentos */
  --agro-accent-blue: #3dc2ff;
  --agro-accent-amber: #ffc409;
  --agro-accent-red: #eb445a;
  
  /* Texto */
  --agro-text-primary: #e8eaf6;
  --agro-text-secondary: rgba(232, 234, 246, 0.6);
}
```

#### Glassmorphism para Cards
```css
.agro-card {
  background: var(--agro-bg-card);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.agro-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(45, 211, 111, 0.1);
}
```

#### Micro-Animaciones
```css
@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 8px var(--agro-primary-glow); }
  50% { box-shadow: 0 0 20px var(--agro-primary-glow); }
}

@keyframes fade-slide-up {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

.sensor-live { animation: pulse-glow 2s ease-in-out infinite; }
.card-enter { animation: fade-slide-up 0.4s ease-out; }
```

### 5. Integración con el Backend

#### Endpoints Consumidos
| Endpoint              | Método | Auth     | Vista           |
|-----------------------|--------|----------|-----------------|
| `/chat`               | POST   | JWT      | AI Assistant    |
| `/chat/history`       | GET    | JWT      | AI Assistant    |
| `/dashboard/latest`   | GET    | JWT      | Welcome Home    |
| `/dashboard/history`  | GET    | JWT      | Telemetry       |
| `/dashboard/state`    | GET    | JWT      | System Control  |
| `/dashboard/mode`     | POST   | JWT      | System Control  |

#### Mapeo de Datos Backend → Frontend
```typescript
// Backend response (chat_history):
{ role: "user" | "ai", message: string, created_at: string }

// Frontend model (ChatMessage):
{ role: "user" | "assistant", content: string, timestamp: string }

// Transformación:
const mapped: ChatMessage = {
  role: row.role === 'ai' ? 'assistant' : 'user',
  content: row.message,
  timestamp: row.created_at,
};
```

### 6. Responsive Layout

#### Split Pane (Desktop)
- Sidebar visible en viewports ≥ 992px con navegación principal.
- Bottom tab bar en mobile (< 992px).
- Ionic `<ion-split-pane>` gestiona la transición automáticamente.

#### Mobile-First
- Todos los componentes se diseñan para mobile primero.
- Breakpoints: `sm: 576px`, `md: 768px`, `lg: 992px`, `xl: 1200px`.

## Archivos Clave (Frontend Repo Separado)
- `src/views/`: Páginas principales (Home, Chat, System, Telemetry).
- `src/stores/`: Pinia stores (chat, sensors, auth).
- `src/composables/`: Lógica reutilizable (useApi, useSensors).
- `src/theme/`: Variables CSS y design tokens de Ionic.

## Buenas Prácticas
1. **Siempre usar `<script setup lang="ts">`** — nunca Options API.
2. **Extraer lógica a composables** — los componentes deben ser presentacionales.
3. **Mapear datos en el store** — nunca transformar datos en los componentes.
4. **Dark mode por defecto** — la paleta está optimizada para fondos oscuros.
5. **Auto-scroll en chat** — siempre hacer scroll al último mensaje después de mount/send.
6. **Skeleton loaders** — mostrar placeholders animados mientras carga la data.
