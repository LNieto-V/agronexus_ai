import asyncio
from .base import BaseRepository, logger


class ChatRepository(BaseRepository):

    # ==========================================
    # SESIONES / CONVERSACIONES
    # ==========================================

    async def create_conversation(self, user_id: str, title: str = "Nueva conversación") -> dict:
        """
        Crea una nueva sesión de chat.
        Usa .insert().execute() y devuelve el primer elemento de .data.
        """
        if not self.client:
            return {}
        try:
            loop = asyncio.get_event_loop()
            # Patrón sugerido para evitar SyncQueryRequestBuilder issues
            payload = {"user_id": user_id, "title": title}
            response = await loop.run_in_executor(
                None,
                lambda: self.client.table("conversations").insert(payload).execute()
            )
            if response.data:
                logger.info(f"Conversación creada: {response.data[0].get('id')} para user {user_id}")
                return response.data[0]
            return {}
        except Exception as e:
            logger.error(f"Error en ChatRepository.create_conversation: {e}")
            return {}

    async def get_conversations(self, user_id: str) -> list:
        """Lista todas las sesiones del usuario, ordenadas por updated_at DESC."""
        if not self.client:
            return []
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.table("conversations")
                            .select("*")
                            .eq("user_id", user_id)
                            .order("updated_at", desc=True)
                            .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Error en ChatRepository.get_conversations: {e}")
            return []

    async def rename_conversation(self, session_id: str, user_id: str, title: str) -> bool:
        """Renombra el título de una sesión."""
        if not self.client:
            return False
        try:
            from datetime import datetime, timezone
            now_iso = datetime.now(timezone.utc).isoformat()
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.table("conversations")
                            .update({"title": title, "updated_at": now_iso})
                            .eq("id", session_id)
                            .eq("user_id", user_id)
                            .execute()
            )
            return True
        except Exception as e:
            logger.error(f"Error en ChatRepository.rename_conversation: {e}")
            return False

    async def delete_conversation(self, session_id: str, user_id: str) -> bool:
        """Elimina una sesión y su historial completo (CASCADE en BD)."""
        if not self.client:
            return False
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.client.table("conversations")
                            .delete()
                            .eq("id", session_id)
                            .eq("user_id", user_id)
                            .execute()
            )
            return True
        except Exception as e:
            logger.error(f"Error en ChatRepository.delete_conversation: {e}")
            return False

    # ==========================================
    # MENSAJES (con soporte de session_id)
    # ==========================================

    async def save_chat_message(self, user_id: str, role: str, message: str, session_id: str | None = None) -> None:
        """
        Guarda un mensaje y actualiza el timestamp de la conversación.
        """
        if not self.client:
            return
        try:
            loop = asyncio.get_event_loop()
            from datetime import datetime, timezone
            now_iso = datetime.now(timezone.utc).isoformat()

            # 1. Insertar el mensaje
            payload = {
                "user_id": user_id,
                "role": role,
                "message": message,
                "session_id": session_id
            }
            
            await loop.run_in_executor(
                None,
                lambda: self.client.table("chat_history").insert(payload).execute()
            )

            # 2. Actualizar updated_at de la conversación si aplica
            if session_id:
                await loop.run_in_executor(
                    None,
                    lambda: self.client.table("conversations")
                                .update({"updated_at": now_iso})
                                .eq("id", session_id)
                                .eq("user_id", user_id)
                                .execute()
                )
            
            logger.info(f"Mensaje persistido | role: {role} | session: {session_id or 'global'}")
        except Exception as e:
            logger.error(f"Error en ChatRepository.save_chat_message: {e}")

    async def get_chat_history(self, user_id: str, limit: int = 6, session_id: str | None = None) -> str:
        """Devuelve el historial como string formateado para el prompt del LLM."""
        if not self.client:
            return ""
        try:
            loop = asyncio.get_event_loop()

            def _query():
                q = self.client.table("chat_history").select("*").eq("user_id", user_id)
                if session_id:
                    q = q.eq("session_id", session_id)
                else:
                    q = q.is_("session_id", "null")
                return q.order("created_at", desc=True).limit(limit).execute()

            response = await loop.run_in_executor(None, _query)
            if not response.data:
                return ""
            history_lines = []
            for row in reversed(response.data):
                role_label = "USUARIO" if row["role"] == "user" else "AGRONEXUS"
                history_lines.append(f"{role_label}: {row['message']}")
            return "\n".join(history_lines)
        except Exception as e:
            logger.error(f"Error en ChatRepository.get_chat_history: {e}")
            return ""

    async def get_chat_history_raw(self, user_id: str, limit: int = 100, session_id: str | None = None) -> list:
        """
        Devuelve el historial como lista de dicts.
        Si session_id es None, busca mensajes 'globales' (sin sesión).
        """
        if not self.client:
            return []
        try:
            loop = asyncio.get_event_loop()

            def _query():
                # Siempre aplicar .select() inmediatamente después de .table()
                q = self.client.table("chat_history").select("*").eq("user_id", user_id)
                if session_id:
                    q = q.eq("session_id", session_id)
                else:
                    q = q.is_("session_id", "null")
                return q.order("created_at", desc=False).limit(limit).execute()

            response = await loop.run_in_executor(None, _query)
            return response.data or []
        except Exception as e:
            logger.error(f"Error en ChatRepository.get_chat_history_raw: {e}")
            return []
