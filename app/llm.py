from google import genai
from google.genai import types, errors
from app.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)


async def generate_raw_response(prompt: str) -> str:
    """Gets a raw text response from Gemini using the direct SDK with 429 handling."""
    try:
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                top_p=0.95,
                max_output_tokens=2048
            )
        )
        return response.text or ""
    except errors.ClientError as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            # Podríamos extraer el tiempo de espera del mensaje si es necesario
            raise Exception("CUOTA_AGOTADA: Límite de la API de Gemini alcanzado. Reintenta en unos instantes.")
        raise e
