import os
from dotenv import load_dotenv
from google import genai

def verify_key():
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ Error: No se encontró GEMINI_API_KEY en el archivo .env")
        return

    print(f"🔍 Probando API Key: {api_key[:10]}...")
    client = genai.Client(api_key=api_key)

    try:
        # Intento de generación simple directamente
        print("\n🤖 Probando generación con gemini-2.5-flash...")
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Hola"
        )
        print(f"✨ Respuesta del modelo: {response.text}")

    except Exception as e:
        print(f"\n❌ Error durante la prueba: {e}")

if __name__ == "__main__":
    verify_key()
