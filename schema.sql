-- 🚜 AgroNexus AI: Supabase Schema Definition (AgTech Multi-Chat & IoT)
-- Este archivo define el esquema necesario para el backend asíncrono y el sistema de sesiones.

-- Opcional: Limpiar esquema previo (comentado por seguridad)
-- DROP TABLE IF EXISTS public.system_state;
-- DROP TABLE IF EXISTS public.chat_history;
-- DROP TABLE IF EXISTS public.conversations;
-- DROP TABLE IF EXISTS public.sensor_data;
-- DROP TABLE IF EXISTS public.api_keys;

-- ==========================================
-- 1. TELEMETRÍA IOT (sensor_data)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.sensor_data (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    temperature FLOAT,
    humidity FLOAT,
    light FLOAT,
    ph FLOAT,
    ec FLOAT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Índices para optimización de consultas históricas (RAG y Dashboard)
CREATE INDEX IF NOT EXISTS idx_sensor_data_user_created ON public.sensor_data(user_id, created_at DESC);

-- ==========================================
-- 2. SESIONES DE CHAT (conversations)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'Nueva conversación',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_updated ON public.conversations(user_id, updated_at DESC);

-- ==========================================
-- 3. HISTORIAL DE MENSAJES (chat_history)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.chat_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'ai')),
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chat_history_user_created ON public.chat_history(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_history_session ON public.chat_history(session_id, created_at ASC);

-- ==========================================
-- 4. HARDWARE AUTH (api_keys)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.api_keys (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    key_hash TEXT NOT NULL PRIMARY KEY,
    key_type TEXT NOT NULL CHECK (key_type IN ('read', 'write')),
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================
-- 5. ESTADO DEL SISTEMA (system_state)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.system_state (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    system_mode TEXT DEFAULT 'AUTO' CHECK (system_mode IN ('AUTO', 'MANUAL')),
    pump_health FLOAT DEFAULT 1.0,
    alerts_active JSONB DEFAULT '[]',
    last_maintenance TIMESTAMPTZ DEFAULT now(),
    maintenance_required BOOLEAN DEFAULT false,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================
-- 6. AUTOMATIZACIÓN: INICIALIZACIÓN DE USUARIO
-- ==========================================

-- Función para inicializar el estado del sistema al registrarse un nuevo usuario
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.system_state (user_id)
  VALUES (new.id);
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Disparador que se activa al insertar en auth.users
-- NOTA: Este disparador debe ser creado por un administrador de Supabase
-- o mediante el SQL Editor si se tienen los permisos necesarios.
-- DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
-- CREATE TRIGGER on_auth_user_created
--   AFTER INSERT ON auth.users
--   FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ==========================================
-- 7. SEGURIDAD (Row Level Security)
-- ==========================================

ALTER TABLE public.sensor_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.system_state ENABLE ROW LEVEL SECURITY;

-- Políticas consolidadas por usuario (auth.uid() = user_id)
-- Usamos FOR ALL para permitir CRUD completo al dueño de los datos.

CREATE POLICY "User Access Policy: sensor_data" ON public.sensor_data 
FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "User Access Policy: conversations" ON public.conversations 
FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "User Access Policy: chat_history" ON public.chat_history 
FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "User Access Policy: api_keys" ON public.api_keys 
FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "User Access Policy: system_state" ON public.system_state 
FOR ALL USING (auth.uid() = user_id);

-- Comentarios explicativos
COMMENT ON TABLE public.sensor_data IS 'Almacena lecturas de telemetría provenientes de ESP32 protegidas por usuario.';
COMMENT ON TABLE public.conversations IS 'Cabeceras de sesión para el sistema multi-chat.';
COMMENT ON TABLE public.chat_history IS 'Mensajes persistentes de usuario e IA, vinculados a una sesión específica.';
COMMENT ON TABLE public.system_state IS 'Estado global y configuración personalizada de cada invernadero inteligente.';
