from app.core.ai.prompts import build_prompt

def test_rag_dynamic_injection_crops():
    prompt = build_prompt("Cómo está el tomate", sensor_data=None, history=None, backend_state=None, chat_history=None)
    assert "Tomate Tropical" in prompt
    assert "Conductividad Eléctrica" not in prompt # El de soil no debería inyectarse si no se pide

def test_rag_dynamic_injection_climate():
    prompt = build_prompt("Dime si la temperatura es mucha", sensor_data=None, history=None, backend_state=None, chat_history=None)
    assert "Más de 33°C" in prompt
    assert "Rango ideal 24°C - 30°C" not in prompt # El RAG de crops no debería cargarse

def test_rag_dynamic_injection_multiple():
    # El usuario pide clima y humedad, y pregunta por riego del tomate
    prompt = build_prompt("Cómo está el riego del tomate con el clima", sensor_data=None, history=None, backend_state=None, chat_history=None)
    assert "Tomate Tropical" in prompt
    assert "Más de 33°C" in prompt
    assert "Evapotranspiración Activa" in prompt
