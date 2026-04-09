-- 🚜 AgroNexus AI: DATABASE CLEANUP & RESET
-- ADVERTENCIA: Este script ELIMINARÁ todos los datos y el esquema actual para un reinicio limpio.
-- Úsalo solo si quieres empezar desde cero.

-- ==========================================
-- 1. LIMPIEZA DE OBJETOS EXISTENTES
-- ==========================================

-- Eliminar Triggers
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

-- Eliminar Funciones
DROP FUNCTION IF EXISTS public.handle_new_user() CASCADE;

-- Eliminar Tablas (con CASCADE para limpiar políticas y dependencias asociadas)
DROP TABLE IF EXISTS public.maintenance_log CASCADE;
DROP TABLE IF EXISTS public.actuator_log CASCADE;
DROP TABLE IF EXISTS public.alert_thresholds CASCADE;
DROP TABLE IF EXISTS public.system_state CASCADE;
DROP TABLE IF EXISTS public.chat_history CASCADE;
DROP TABLE IF EXISTS public.conversations CASCADE;
DROP TABLE IF EXISTS public.sensor_data CASCADE;
DROP TABLE IF EXISTS public.api_keys CASCADE;
DROP TABLE IF EXISTS public.profiles CASCADE;
DROP TABLE IF EXISTS public.zones CASCADE;

-- ==========================================
-- 2. RE-CREACIÓN DEL ESQUEMA
-- ==========================================

-- [Aquí pegas el resto de tu schema_v1.sql o ejecutas el script principal]
-- He actualizado schema_v1.sql para que sea idempotente (pueda ejecutarse varias veces).
