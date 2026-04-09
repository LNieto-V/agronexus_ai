from abc import ABC, abstractmethod
import os
from typing import Any
from google import genai
from google.genai import types
from app.core.config import settings


# ---------------------------------------------------------
# PATRÓN ESTRATEGIA: Interfaz Base para cualquier IA
# ---------------------------------------------------------
class AIEngineStrategy(ABC):
    @abstractmethod
    async def generate(self, prompt: str, tools: list = None) -> Any:
        """Genera una respuesta o llamadas a funciones."""
        pass


# ---------------------------------------------------------
# Estrategia 1: Google Gemini (Actual y por Defecto)
# ---------------------------------------------------------
class GeminiEngine(AIEngineStrategy):
    def __init__(self):
        keys_str = settings.GEMINI_API_KEYS or settings.GEMINI_API_KEY
        self.keys = (
            [k.strip() for k in keys_str.split(",") if k.strip()] if keys_str else []
        )
        self.current_key_idx = 0
        self.model_name = "gemini-2.5-flash"

        if not self.keys:
            import logging

            logging.getLogger(__name__).warning(
                "No se configuraron API Keys para Gemini."
            )
            self.client = None
        else:
            self.client = genai.Client(api_key=self.keys[self.current_key_idx])

    def _rotate_key(self) -> bool:
        """Cambia a la siguiente API Key configurada."""
        if len(self.keys) <= 1:
            return False
        self.current_key_idx = (self.current_key_idx + 1) % len(self.keys)
        self.client = genai.Client(api_key=self.keys[self.current_key_idx])
        return True

    async def generate(self, prompt: str, tools: list = None) -> Any:
        if not self.client:
            raise Exception("No hay API Keys configuradas.")

        # 🔄 Rotación proactiva para balanceo de carga (Round Robin)
        if len(self.keys) > 1:
            self._rotate_key()
            import logging

            logging.getLogger(__name__).info(
                f"Balanceo de Carga: Usando llave API índice {self.current_key_idx}"
            )

        attempts = 0
        max_attempts = len(self.keys)
        last_error = None

        while attempts < max_attempts:
            try:
                config = types.GenerateContentConfig(
                    temperature=0.3, top_p=0.95, max_output_tokens=4096, tools=tools
                )
                response = await self.client.aio.models.generate_content(
                    model=self.model_name, contents=prompt, config=config
                )
                return response
            except Exception as e:
                error_msg = str(e)
                last_error = error_msg

                # Manejar códigos 429 explícitos o strings de mensaje de Google GenAI
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    import logging

                    logger = logging.getLogger(__name__)
                    attempts += 1

                    if attempts < max_attempts:
                        logger.warning(
                            f"Llave actual agotada (Índice {self.current_key_idx}). Rotando llave..."
                        )
                        self._rotate_key()
                    else:
                        raise Exception(
                            "CUOTA_AGOTADA: Límite de todas las APIs de Gemini alcanzado. Reintenta más tarde."
                        )
                else:
                    raise Exception(f"Fallo inesperado del LLM Gemini: {error_msg}")

        raise Exception(f"Fallo tras reintentos: {last_error}")


# ---------------------------------------------------------
# Estrategia 2: Anthropic Claude (Mock Futuro)
# ---------------------------------------------------------
class ClaudeEngine(AIEngineStrategy):
    def __init__(self):
        pass

    async def generate(self, prompt: str) -> str:
        # En el futuro aquí iría la lógica del SDK de anthropic
        return '{"action": "MOCK_CLAUDE", "response": "Modo Claude activado", "alerts": []}'


# ---------------------------------------------------------
# Factoría de Estrategias y Exposición Asíncrona
# ---------------------------------------------------------
def get_ai_engine() -> AIEngineStrategy:
    provider = os.getenv("AI_PROVIDER", "gemini").lower()
    if provider == "claude":
        return ClaudeEngine()
    return GeminiEngine()


# Instancia global (Singleton liviano) para uso rápido, o puede ser inyectado
current_engine = get_ai_engine()


async def generate_raw_response(prompt: str, tools: list = None) -> Any:
    """Función envoltoria para compatibilidad estricta con funciones sin inyección AI."""
    res = await current_engine.generate(prompt, tools=tools)
    if hasattr(res, "text") and res.text:
        return res.text
    return res
