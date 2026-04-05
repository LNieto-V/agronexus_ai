-- 🚜 AgroNexus AI: Supabase Schema Definition

-- 1. Tabla para datos de sensores (Telemetría IoT)
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

-- Índices para optimización de consultas históricas
CREATE INDEX IF NOT EXISTS idx_sensor_data_user_created ON public.sensor_data(user_id, created_at DESC);

-- 2. Tabla para el historial del chat (Memoria Conversacional)
CREATE TABLE IF NOT EXISTS public.chat_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'ai')),
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Índices para el chat
CREATE INDEX IF NOT EXISTS idx_chat_history_user_created ON public.chat_history(user_id, created_at DESC);

-- 3. Tabla para la gestión de API Keys (Dispositivos IoT)
CREATE TABLE IF NOT EXISTS public.api_keys (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    key_hash TEXT NOT NULL PRIMARY KEY,
    key_type TEXT NOT NULL CHECK (key_type IN ('read', 'write')),
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. Tabla para el estado del sistema (Configuración y persistencia)
CREATE TABLE IF NOT EXISTS public.system_state (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    system_mode TEXT DEFAULT 'AUTO' CHECK (system_mode IN ('AUTO', 'MANUAL')),
    pump_health FLOAT DEFAULT 1.0,
    alerts_active JSONB DEFAULT '[]',
    last_maintenance TIMESTAMPTZ DEFAULT now(),
    maintenance_required BOOLEAN DEFAULT false,
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 5. Políticas de Seguridad (RLS) - Vital para producción
ALTER TABLE public.sensor_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.system_state ENABLE ROW LEVEL SECURITY;

-- Evitamos que usuarios no correspondientes accedan
CREATE POLICY "Users can view their own sensor data" ON public.sensor_data FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own sensor data" ON public.sensor_data FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view their own chat history" ON public.chat_history FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own chat history" ON public.chat_history FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view their own api keys" ON public.api_keys FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert their own api keys" ON public.api_keys FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can delete their own api keys" ON public.api_keys FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Users can view and edit their own system state" ON public.system_state FOR ALL USING (auth.uid() = user_id);
