-- Crear tabla para la memoria conversacional
CREATE TABLE IF NOT EXISTS public.chat_history (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'ai')),
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Habilitar RLS en chat_history
ALTER TABLE public.chat_history ENABLE ROW LEVEL SECURITY;

-- Política para que los usuarios vean su propio chat
CREATE POLICY "Users can view their own chat history" 
ON public.chat_history FOR SELECT 
USING (auth.uid() = user_id);

-- Política para que los usuarios (o el backend) inserten mensajes
CREATE POLICY "Users can insert their own chat messages" 
ON public.chat_history FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- Crear índice para ordenamiento rápido
CREATE INDEX IF NOT EXISTS idx_chat_history_user_created ON public.chat_history(user_id, created_at DESC);
