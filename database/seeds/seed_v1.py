import time
from datetime import datetime, timedelta
from app.services.supabase_service import supabase_db

def seed_data():
    print("🌱 Iniciando inserción de datos de prueba en Supabase...")
    
    # Generar 10 registros de las últimas 5 horas
    # Simulamos una caída de humedad de 80% a 45%
    base_time = datetime.now()
    
    data_points = []
    for i in range(10):
        # Cada registro 30 min atrás
        record_time = (base_time - timedelta(minutes=30 * i)).isoformat()
        
        # Humedad bajando: 45 + (i * 4) -> 81% a 45% aprox.
        humidity = 45 + (i * 4)
        temperature = 22 + (i * 0.5)
        
        data_points.append({
            "created_at": record_time,
            "temperature": temperature,
            "humidity": humidity,
            "light": 5000 if i % 2 == 0 else 4500,
            "ph": 6.0,
            "ec": 1.5
        })

    # Insertar uno por uno para asegurar que el created_at se respecte o masivamente
    success_count = 0
    for point in data_points:
        if supabase_db.insert_sensor_data(point):
            success_count += 1
    
    print(f"✅ Se insertaron {success_count} registros satisfactoriamente.")

if __name__ == "__main__":
    seed_data()
