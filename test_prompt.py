from app.prompts import build_prompt

def test_build_prompt():
    sensor_data = {
        "temperature": 29.5,
        "humidity": 35.0,
        "light": 2500
    }
    message = "¿Qué debo hacer con mis plantas?"
    
    prompt = build_prompt(message, sensor_data)
    
    print("--- FULL PROMPT START ---")
    print(prompt)
    print("--- FULL PROMPT END ---")
    
    # Verificaciones básicas
    assert "AgroNexus AI Expert" in prompt
    assert "29.5" in prompt
    assert "FAN" in prompt
    assert "JSON" in prompt
    
    print("\n✅ Verification successful: Prompt is modular and includes sensor data.")

if __name__ == "__main__":
    test_build_prompt()
