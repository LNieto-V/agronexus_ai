import asyncio
import httpx
import json

async def test_optimization():
    url = "http://localhost:8000/iot/telemetry"
    
    print("🧪 PRUEBA 1: Datos Normales (Debería saltar la IA)")
    normal_data = {
        "sensor_data": {"temperature": 25.0, "humidity": 60.0, "ph": 6.0}
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=normal_data)
        print(f"Respuesta Normal: {resp.json()}")
        # Se espera: {"actions": [], "alerts": []}
        
    print("\n🧪 PRUEBA 2: Datos Anómalos (Debería activar la IA)")
    anomaly_data = {
        "sensor_data": {"temperature": 45.0, "humidity": 60.0, "ph": 6.0}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=anomaly_data, timeout=30.0)
            print(f"Respuesta Anomalía: {resp.json()}")
        except Exception as e:
            print(f"Nota: Si Gemini sigue en 429, esta prueba fallará como se espera: {e}")

if __name__ == "__main__":
    asyncio.run(test_optimization())
