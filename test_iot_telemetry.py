import asyncio
import httpx
import json

async def simulate_esp32():
    # URL local para prueba (debe estar uvicorn corriendo)
    url = "http://localhost:8000/iot/telemetry"
    
    # Datos que enviaría una ESP32
    telemetry_data = {
        "sensor_data": {
            "temperature": 32.5,
            "humidity": 40.2, # Humedad un poco baja
            "light": 5000,
            "ph": 6.0,
            "ec": 1.4
        }
    }
    
    print(f"📡 Enviando telemetría desde ESP32 a {url}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=telemetry_data, timeout=30.0)
            
            if response.status_code == 200:
                print("✅ Recibido satisfactoriamente.")
                print(f"📦 Respuesta del servidor: {json.dumps(response.json(), indent=2)}")
            else:
                print(f"❌ Error en el servidor: {response.status_code}")
                print(response.text)
                
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("Asegúrate de que el servidor esté corriendo con 'uv run uvicorn app.main:app'")

if __name__ == "__main__":
    asyncio.run(simulate_esp32())
