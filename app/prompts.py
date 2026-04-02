from pathlib import Path
from functools import lru_cache
from typing import Dict, Any

AI_DIR = Path(__file__).parent.parent / "ai"

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
    backend_state: Dict[str, Any] = None
) -> str:
    """Constructs the final prompt string by concatenating modular files and data."""
    system_prompt = load_prompt_file("prompt.md")
    rules = load_prompt_file("rules.md")
    knowledge = load_prompt_file("knowledge.md")
    devices = load_prompt_file("devices.md")
    
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

    final_prompt = f"""
{system_prompt}

{knowledge}

{devices}

{rules}

{history_context}
{state_context}
{sensor_context}

## MENSAJE DEL USUARIO:
{message}

Recuerda: Proactividad, seguridad (no llaves) y formato JSON al final.
"""
    return final_prompt.strip()
