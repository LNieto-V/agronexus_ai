from abc import ABC, abstractmethod
import os
from google import genai
from google.genai import types
from app.core.config import settings

# ---------------------------------------------------------
# PATRÓN ESTRATEGIA: Interfaz Base para cualquier IA
# ---------------------------------------------------------
class AIEngineStrategy(ABC):
    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Genera una respuesta en texto desde el modelo subyacente."""
        pass

# ---------------------------------------------------------
# Estrategia 1: Google Gemini (Actual y por Defecto)
# ---------------------------------------------------------
class GeminiEngine(AIEngineStrategy):
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-2.5-flash"
        
    async def generate(self, prompt: str) -> str:
        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    top_p=0.95,
                    max_output_tokens=4096
                )
            )
            return response.text or ""
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                raise Exception("CUOTA_AGOTADA: Límite de la API de Gemini alcanzado. Reintenta en unos instantes.")
            raise Exception(f"Fallo inesperado del LLM Gemini: {str(e)}")

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

async def generate_raw_response(prompt: str) -> str:
    """Función envoltoria para compatibilidad estricta con funciones sin inyección AI."""
    return await current_engine.generate(prompt)
