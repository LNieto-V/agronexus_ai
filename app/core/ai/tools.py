from typing import List, Dict, Any

# Definición de herramientas (Function Calling) para Gemini 2.0/2.1
# Estas herramientas permiten a la IA actuar sobre el mundo real de forma estructurada.

IOT_TOOLS = [
    {
        "function_declarations": [
            {
                "name": "control_actuador",
                "description": "Cambia el estado de un dispositivo físico (ventilador, bomba, luz).",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "device": {
                            "type": "STRING", 
                            "description": "Nombre del dispositivo: 'FAN', 'PUMP', 'LIGHT'."
                        },
                        "action": {
                            "type": "STRING", 
                            "description": "Acción a realizar: 'ON', 'OFF'."
                        },
                        "reason": {
                            "type": "STRING", 
                            "description": "Breve explicación de por qué se toma la acción."
                        }
                    },
                    "required": ["device", "action"]
                }
            },
            {
                "name": "configurar_umbrales",
                "description": "Ajusta los límites de seguridad para un sensor específico.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "sensor_type": {
                            "type": "STRING",
                            "description": "Tipo de sensor: 'temperature', 'humidity', 'ph', 'ec'."
                        },
                        "min_value": {"type": "NUMBER"},
                        "max_value": {"type": "NUMBER"}
                    },
                    "required": ["sensor_type", "min_value", "max_value"]
                }
            },
            {
                "name": "registrar_mantenimiento",
                "description": "Registra una tarea de mantenimiento realizada en el invernadero.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "task": {"type": "STRING", "description": "Descripción de la tarea realizada."},
                        "notes": {"type": "STRING", "description": "Notas adicionales o estado del equipo."}
                    },
                    "required": ["task"]
                }
            }
        ]
    }
]
