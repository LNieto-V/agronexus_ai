import asyncio
import os
from dotenv import load_dotenv
from app.llm import generate_response

async def test_llm():
    load_dotenv()
    print(f"API Key found: {os.getenv('GEMINI_API_KEY')[:10]}...")
    try:
        response = await generate_response("Hola, eres un experto en IoT agrícola. Responde con un saludo corto.")
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm())
