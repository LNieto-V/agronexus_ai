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
-- 6. PERFILES Y ROLES (profiles)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    email TEXT,
    full_name TEXT,
    role TEXT DEFAULT 'owner' CHECK (role IN ('owner', 'agronomist', 'viewer')),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================
-- 7. REGISTRO DE ACTUADORES (actuator_log)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.actuator_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    device TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT,
    triggered_by TEXT DEFAULT 'AI' CHECK (triggered_by IN ('AI', 'MANUAL')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_actuator_log_user ON public.actuator_log(user_id, created_at DESC);

-- ==========================================
-- 8. UMBRALES DE ALERTA (alert_thresholds)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.alert_thresholds (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    sensor_type TEXT NOT NULL, -- 'temperature', 'humidity', etc.
    min_value FLOAT,
    max_value FLOAT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, sensor_type)
);

-- ==========================================
-- 9. AUTOMATIZACIÓN: INICIALIZACIÓN DE USUARIO
-- ==========================================

-- Función para inicializar el estado del sistema y perfil al registrarse un nuevo usuario
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  -- Crear perfil
  INSERT INTO public.profiles (id, email)
  VALUES (new.id, new.email);
  
  -- Crear estado del sistema
  INSERT INTO public.system_state (user_id)
  VALUES (new.id);
  
  -- Umbrales por defecto
  INSERT INTO public.alert_thresholds (user_id, sensor_type, min_value, max_value)
  VALUES 
    (new.id, 'temperature', 15.0, 32.0),
    (new.id, 'humidity', 40.0, 85.0),
    (new.id, 'ph', 5.5, 7.5);

  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ==========================================
-- 10. SEGURIDAD (Row Level Security)
-- ==========================================

ALTER TABLE public.sensor_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.system_state ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.actuator_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alert_thresholds ENABLE ROW LEVEL SECURITY;

-- Políticas de usuario
CREATE POLICY "User Access Policy: sensor_data" ON public.sensor_data FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "User Access Policy: conversations" ON public.conversations FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "User Access Policy: chat_history" ON public.chat_history FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "User Access Policy: api_keys" ON public.api_keys FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "User Access Policy: system_state" ON public.system_state FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "User Access Policy: profiles" ON public.profiles FOR ALL USING (auth.uid() = id);
CREATE POLICY "User Access Policy: actuator_log" ON public.actuator_log FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "User Access Policy: alert_thresholds" ON public.alert_thresholds FOR ALL USING (auth.uid() = user_id);

-- Comentarios explicativos
COMMENT ON TABLE public.sensor_data IS 'Almacena lecturas de telemetría provenientes de ESP32 protegidas por usuario.';
COMMENT ON TABLE public.conversations IS 'Cabeceras de sesión para el sistema multi-chat.';
COMMENT ON TABLE public.chat_history IS 'Mensajes persistentes de usuario e IA, vinculados a una sesión específica.';
COMMENT ON TABLE public.system_state IS 'Estado global y configuración personalizada de cada invernadero inteligente.';
COMMENT ON TABLE public.profiles IS 'Perfiles de usuario con roles (owner, agronomist, viewer).';
COMMENT ON TABLE public.actuator_log IS 'Historial de acciones ejecutadas por actuadores.';
COMMENT ON TABLE public.alert_thresholds IS 'Configuración personalizada de umbrales para alertas.';

-- ==========================================
-- 11. ZONAS / INVERNADEROS (zones)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.zones (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL, -- Ej: "Invernadero Norte", "Zona Hidropónica 1"
    crop_type TEXT,     -- Ej: "Tomate", "Lechuga"
    status TEXT DEFAULT 'OFFLINE', -- 'ONLINE', 'OFFLINE'
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Actualizar telemetría y logs para soportar zonas
ALTER TABLE public.sensor_data ADD COLUMN IF NOT EXISTS zone_id UUID REFERENCES public.zones(id) ON DELETE SET NULL;
ALTER TABLE public.actuator_log ADD COLUMN IF NOT EXISTS zone_id UUID REFERENCES public.zones(id) ON DELETE SET NULL;
ALTER TABLE public.system_state ADD COLUMN IF NOT EXISTS zone_id UUID REFERENCES public.zones(id) ON DELETE SET NULL;

ALTER TABLE public.zones ENABLE ROW LEVEL SECURITY;
CREATE POLICY "User Access Policy: zones" ON public.zones FOR ALL USING (auth.uid() = user_id);

-- ==========================================
-- 12. MANTENIMIENTO (maintenance_log)
-- ==========================================

-- ==========================================
-- 11. MANTENIMIENTO (maintenance_log)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.maintenance_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    task TEXT NOT NULL,
    notes TEXT,
    performed_at TIMESTAMPTZ DEFAULT now()
);

ALTER TABLE public.maintenance_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "User Access Policy: maintenance_log" ON public.maintenance_log FOR ALL USING (auth.uid() = user_id);

