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
        self._key_cooldowns: dict[int, float] = {}
        self.COOLDOWN_SECONDS = 30

        if not self.keys:
            import logging
            logging.getLogger(__name__).warning("No se configuraron API Keys para Gemini.")

    async def generate(self, prompt: str, tools: list = None) -> Any:
        if not self.keys:
            raise Exception("No hay API Keys configuradas.")

        import logging
        import time
        import asyncio
        import random

        logger = logging.getLogger(__name__)

        # Rotación inteligente
        now = time.time()
        start_idx = -1
        
        if len(self.keys) > 1:
            for _ in range(len(self.keys)):
                idx = self.current_key_idx
                self.current_key_idx = (self.current_key_idx + 1) % len(self.keys)
                
                if idx not in self._key_cooldowns or now - self._key_cooldowns[idx] > self.COOLDOWN_SECONDS:
                    if idx in self._key_cooldowns:
                        del self._key_cooldowns[idx]
                    start_idx = idx
                    break
                    
            if start_idx == -1:
                start_idx = min(self._key_cooldowns.keys(), key=lambda k: self._key_cooldowns[k])
                self.current_key_idx = (start_idx + 1) % len(self.keys)
        else:
            start_idx = 0

        logger.info(f"Balanceo de Carga: Usando llave API índice {start_idx} (Total disponibles: {len(self.keys)})")

        attempts = 0
        max_attempts = len(self.keys) * 2
        last_error = None
        current_idx = start_idx

        while attempts < max_attempts:
            client = genai.Client(api_key=self.keys[current_idx])

            try:
                config = types.GenerateContentConfig(
                    temperature=0.3, top_p=0.95, max_output_tokens=8192, tools=tools
                )
                response = await client.aio.models.generate_content(
                    model=self.model_name, contents=prompt, config=config
                )
                
                # Éxito: Limpiar cooldown si la llave arrastraba uno
                if current_idx in self._key_cooldowns:
                    del self._key_cooldowns[current_idx]
                return response

            except Exception as e:
                error_msg = str(e)
                last_error = error_msg
                attempts += 1

                transient_errors = ["503", "UNAVAILABLE", "DEADLINE_EXCEEDED"]
                quota_errors = ["429", "RESOURCE_EXHAUSTED"]

                is_transient = any(code in error_msg for code in transient_errors)
                is_quota = any(code in error_msg for code in quota_errors)

                if is_transient or is_quota:
                    if attempts < max_attempts:
                        # Registrar fallo
                        self._key_cooldowns[current_idx] = time.time()
                        
                        if is_transient:
                            # 503: Backoff y reintento con la misma llave
                            base_delay = 1.5
                            delay = base_delay * (2 ** (attempts - 1)) + random.uniform(0, 1)
                            wait_time = min(delay, 8)
                            logger.warning(
                                f"Error temporal ({error_msg}) en llave {current_idx}. "
                                f"Esperando {wait_time:.1f}s (backoff)..."
                            )
                            await asyncio.sleep(wait_time)
                        else:
                            # 429: Rotar inmediatamente
                            logger.warning(
                                f"Límite de cuota o error permanente ({error_msg}) en índice {current_idx}. Rotando..."
                            )
                            current_idx = (current_idx + 1) % len(self.keys)

                        continue
                    else:
                        raise Exception(
                            f"LIMITE_ALCANZADO: Todas las llaves fallaron o están agotadas. Último error: {error_msg}"
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
