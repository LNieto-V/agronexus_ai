-- 🚜 AgroNexus AI: Supabase Schema Definition (AgTech Multi-Chat & IoT)
-- Versión Idempotente (Replicable en múltiples ejecuciones)

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
    sensor_type TEXT NOT NULL,
    min_value FLOAT,
    max_value FLOAT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, sensor_type)
);

-- ==========================================
-- 9. ZONAS / INVERNADEROS (zones)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.zones (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    crop_type TEXT,
    status TEXT DEFAULT 'OFFLINE',
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Migración idempotente de columnas para zonas
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='sensor_data' AND column_name='zone_id') THEN
        ALTER TABLE public.sensor_data ADD COLUMN zone_id UUID REFERENCES public.zones(id) ON DELETE SET NULL;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='actuator_log' AND column_name='zone_id') THEN
        ALTER TABLE public.actuator_log ADD COLUMN zone_id UUID REFERENCES public.zones(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='system_state' AND column_name='zone_id') THEN
        ALTER TABLE public.system_state ADD COLUMN zone_id UUID REFERENCES public.zones(id) ON DELETE SET NULL;
    END IF;
END $$;

-- ==========================================
-- 10. MANTENIMIENTO (maintenance_log)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.maintenance_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    task TEXT NOT NULL,
    notes TEXT,
    performed_at TIMESTAMPTZ DEFAULT now()
);

-- ==========================================
-- 11. AUTOMATIZACIÓN: INICIALIZACIÓN DE USUARIO
-- ==========================================
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.profiles (id, email)
  VALUES (new.id, new.email)
  ON CONFLICT (id) DO NOTHING;
  
  INSERT INTO public.system_state (user_id)
  VALUES (new.id)
  ON CONFLICT (user_id) DO NOTHING;
  
  INSERT INTO public.alert_thresholds (user_id, sensor_type, min_value, max_value)
  VALUES 
    (new.id, 'temperature', 15.0, 32.0),
    (new.id, 'humidity', 40.0, 85.0),
    (new.id, 'ph', 5.5, 7.5)
  ON CONFLICT (user_id, sensor_type) DO NOTHING;

  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ==========================================
-- 12. SEGURIDAD (Row Level Security) - IDEMPOTENTE
-- ==========================================

-- Función auxiliar para habilitar RLS y crear políticas sin errores
DO $$
DECLARE
    t text;
BEGIN
    FOR t IN SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    END LOOP;
END $$;

-- Políticas con limpieza previa para evitar "Policy already exists"
DO $$
BEGIN
    -- sensor_data
    DROP POLICY IF EXISTS "User Access Policy: sensor_data" ON public.sensor_data;
    CREATE POLICY "User Access Policy: sensor_data" ON public.sensor_data FOR ALL USING (auth.uid() = user_id);

    -- conversations
    DROP POLICY IF EXISTS "User Access Policy: conversations" ON public.conversations;
    CREATE POLICY "User Access Policy: conversations" ON public.conversations FOR ALL USING (auth.uid() = user_id);

    -- chat_history
    DROP POLICY IF EXISTS "User Access Policy: chat_history" ON public.chat_history;
    CREATE POLICY "User Access Policy: chat_history" ON public.chat_history FOR ALL USING (auth.uid() = user_id);

    -- api_keys
    DROP POLICY IF EXISTS "User Access Policy: api_keys" ON public.api_keys;
    CREATE POLICY "User Access Policy: api_keys" ON public.api_keys FOR ALL USING (auth.uid() = user_id);

    -- system_state
    DROP POLICY IF EXISTS "User Access Policy: system_state" ON public.system_state;
    CREATE POLICY "User Access Policy: system_state" ON public.system_state FOR ALL USING (auth.uid() = user_id);

    -- profiles
    DROP POLICY IF EXISTS "User Access Policy: profiles" ON public.profiles;
    CREATE POLICY "User Access Policy: profiles" ON public.profiles FOR ALL USING (auth.uid() = id);

    -- actuator_log
    DROP POLICY IF EXISTS "User Access Policy: actuator_log" ON public.actuator_log;
    CREATE POLICY "User Access Policy: actuator_log" ON public.actuator_log FOR ALL USING (auth.uid() = user_id);

    -- alert_thresholds
    DROP POLICY IF EXISTS "User Access Policy: alert_thresholds" ON public.alert_thresholds;
    CREATE POLICY "User Access Policy: alert_thresholds" ON public.alert_thresholds FOR ALL USING (auth.uid() = user_id);

    -- zones
    DROP POLICY IF EXISTS "User Access Policy: zones" ON public.zones;
    CREATE POLICY "User Access Policy: zones" ON public.zones FOR ALL USING (auth.uid() = user_id);

    -- maintenance_log
    DROP POLICY IF EXISTS "User Access Policy: maintenance_log" ON public.maintenance_log;
    CREATE POLICY "User Access Policy: maintenance_log" ON public.maintenance_log FOR ALL USING (auth.uid() = user_id);
END $$;

-- ==========================================
-- 13. COMENTARIOS
-- ==========================================
COMMENT ON TABLE public.sensor_data IS 'Almacena lecturas de telemetría provenientes de ESP32 protegidas por usuario.';
COMMENT ON TABLE public.conversations IS 'Cabeceras de sesión para el sistema multi-chat.';
COMMENT ON TABLE public.chat_history IS 'Mensajes persistentes de usuario e IA, vinculados a una sesión específica.';
COMMENT ON TABLE public.system_state IS 'Estado global y configuración personalizada de cada invernadero inteligente.';
COMMENT ON TABLE public.profiles IS 'Perfiles de usuario con roles (owner, agronomist, viewer).';
COMMENT ON TABLE public.actuator_log IS 'Historial de acciones ejecutadas por actuadores.';
COMMENT ON TABLE public.alert_thresholds IS 'Configuración personalizada de umbrales para alertas.';
COMMENT ON TABLE public.zones IS 'Gestión física de invernaderos o áreas de cultivo.';
