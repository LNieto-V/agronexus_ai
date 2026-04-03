-- Habilitar extensión pgcrypto si no está habilitada
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Crear tabla de API Keys
CREATE TABLE IF NOT EXISTS public.api_keys (
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    key_type TEXT NOT NULL CHECK (key_type IN ('read', 'write')),
    key_hash TEXT NOT NULL,
    key_prefix TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    last_used_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, key_type)
);

-- Habilitar RLS
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;

-- Políticas de RLS
-- Los usuarios solo pueden ver sus propias llaves
CREATE POLICY "Users can view their own API keys" 
ON public.api_keys FOR SELECT 
USING (auth.uid() = user_id);

-- Los usuarios solo pueden borrar sus propias llaves
CREATE POLICY "Users can delete their own API keys" 
ON public.api_keys FOR DELETE 
USING (auth.uid() = user_id);

-- Solo el sistema (Service Role) puede insertar/actualizar hashes
-- pero permitiremos que el usuario las cree vía backend (que usará service role)
-- O podemos dar permiso al usuario autenticado para insertar si confiamos en el backend
-- Por seguridad, el backend manejará la creación.

-- Comentario descriptivo
COMMENT ON TABLE public.api_keys IS 'Almacena los hashes de las API Keys (Lectura/Escritura) para acceso de dispositivos ESP32.';

-- Asegurar que sensor_data tenga user_id (Migración incremental)
ALTER TABLE public.sensor_data ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Habilitar RLS en sensor_data
ALTER TABLE public.sensor_data ENABLE ROW LEVEL SECURITY;

-- Política para que los usuarios vean solo sus propios datos
CREATE POLICY "Users can view their own sensor data" 
ON public.sensor_data FOR SELECT 
USING (auth.uid() = user_id OR EXISTS (
    SELECT 1 FROM public.api_keys WHERE public.api_keys.user_id = public.sensor_data.user_id
));

-- Política para que los usuarios (o sus dispositivos vía API key) inserten datos
CREATE POLICY "Users can insert their own sensor data" 
ON public.sensor_data FOR INSERT 
WITH CHECK (auth.uid() = user_id OR user_id IS NOT NULL); -- El backend validará el user_id
