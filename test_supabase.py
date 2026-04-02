import os
from dotenv import load_dotenv
from supabase import create_client, Client

def test_supabase():
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    print(f"📡 Conectando a {url}...")
    try:
        supabase: Client = create_client(url, key)
        # Intentar obtener información de las tablas o solo un ping
        # Como no sabemos las tablas, solo intentaremos una operación nula o descriptiva
        print("✅ Cliente inicializado correctamente.")
        
        # Opcional: Listar algunas tablas si rpc está disponible o simplemente intentar un select común
        # En Supabase no hay una forma directa de 'listar tablas' vía anon key fácilmente sin rpc
        # Pero podemos intentar leer 'sensor_data' que es el estándar del proyecto
        try:
            res = supabase.table("sensor_data").select("*", count="exact").limit(1).execute()
            print(f"📊 Tabla 'sensor_data' encontrada. Filas: {res.count}")
        except Exception:
            print("❌ Tabla 'sensor_data' no encontrada o inaccesible.")

    except Exception as e:
        print(f"❌ Error conectando: {e}")

if __name__ == "__main__":
    test_supabase()
