# Dispositivos y Actuadores en Campo

Los siguientes dispositivos están registrados en el sistema AgroNexus AI:

## Dispositivos Disponibles
- **FAN (Ventilador)**: Control de temperatura y circulación de aire.
- **LIGHT (Luces LED)**: Control de intensidad lumínica y ciclo circadiano.
- **IRRIGATION (Bomba de Riego)**: Control de hidratación del cultivo.
- **HUMIDIFIER (Humidificador)**: Control de humedad relativa ambiental.
- **HEATER (Calentador)**: Control de temperatura en climas fríos.

## Acciones de Control
- `ON`: Encendido forzado.
- `OFF`: Apagado forzado.
- `AUTO`: Delegar el control en la lógica local del controlador IoT.

## Protocolo de Decisión
- **Prioridad 1**: Seguridad. Nunca enciendas el riego si se detecta una inundación o humedad > 95%.
- **Prioridad 2**: Luz. Las luces deben estar apagadas 6-8 horas al día para el descanso del cultivo.
- **Prioridad 3**: Eficiencia energética. Prefiere ventilación natural si es posible (no disponible en este controlador, usar FAN).
