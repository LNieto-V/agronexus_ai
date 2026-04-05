from pathlib import Path
from functools import lru_cache
from typing import Dict, Any
from app.core.config import settings

AI_DIR = Path(settings.BASE_DIR) / ".agent" / "skills" / "backend-fastapi-iot"

@lru_cache()
def load_prompt_file(filename: str) -> str:
    """Reads a markdown file from the ai/ directory with caching."""
    file_path = AI_DIR / filename
    if not file_path.exists():
        return ""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def build_prompt(
    message: str, 
    sensor_data: Dict[str, Any] = None, 
    history: str = None, 
    backend_state: Dict[str, Any] = None,
    chat_history: str = None
) -> str:
    """Constructs the final prompt string by concatenating modular files and data."""
    system_prompt = load_prompt_file("prompt.md")
    rules = load_prompt_file("rules.md")
    devices = load_prompt_file("devices.md")
    
    # RAG Dinámico (Carga Diferida basada en el mensaje del usuario)
    knowledge = ""
    msg_low = message.lower()
    if any(k in msg_low for k in ["tomate", "lechuga", "cultivo"]):
        knowledge += load_prompt_file("crops.md") + "\n"
    if any(k in msg_low for k in ["clima", "temperatura", "humedad", "calor", "frío"]):
        knowledge += load_prompt_file("climate.md") + "\n"
    if any(k in msg_low for k in ["suelo", "ph", "ec", "tierra"]):
        knowledge += load_prompt_file("soil.md") + "\n"
    if any(k in msg_low for k in ["riego", "agua", "bomba", "regar"]):
        knowledge += load_prompt_file("irrigation.md") + "\n"

    # Contexto de Sensores en Tiempo Real
    sensor_context = ""
    if sensor_data:
        sensor_context = "\n## DATOS DE SENSORES ACTUALES (TIEMPO REAL):\n"
        for key, value in sensor_data.items():
            sensor_context += f"- {key}: {value}\n"

    # Contexto de Historial y Tendencias (Supabase)
    history_context = f"\n## CONTEXTO HISTÓRICO (ÚLTIMAS 24H):\n{history or 'No hay datos históricos disponibles.'}\n"

    # Contexto de Estado del Backend (Variables Internas)
    state_context = ""
    if backend_state:
        state_context = "\n## ESTADO INTERNO DEL SISTEMA:\n"
        for key, value in backend_state.items():
            state_context += f"- {key}: {value}\n"

    # Contexto Conversacional (Memoria del Chat)
    chat_context = ""
    if chat_history:
        chat_context = f"\n## HISTORIAL DE LA CONVERSACIÓN RECIENTE:\n{chat_history}\n"

    # Aplicando Jerarquía estricta según rúbrica evaluadora
    final_prompt = f"""
{system_prompt}

{rules}

## ESTADO ACTUAL DEL SISTEMA Y CULTIVO:
{state_context}
{sensor_context}

## HISTORIAL Y CONTEXTO RELEVANTE:
{history_context}
{chat_context}

## KNOWLEDGE BASE (RAG DINÁMICO):
{knowledge if knowledge else "Sin artículos RAG relevantes detectados."}

## DISPOSITIVOS Y COMANDOS:
{devices}

## MENSAJE NUEVO DEL USUARIO:
{message}

Recuerda: Breve, amigable y formato JSON al final.
"""
    return final_prompt.strip()
