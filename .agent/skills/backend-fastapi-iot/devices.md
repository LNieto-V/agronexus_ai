# Dispositivos, Actuadores y Trazabilidad

Los siguientes dispositivos residen en las **Zonas de Cultivo** de AgroNexus AI y su estado se sincroniza en tiempo real vía SSE.

## Dispositivos Disponibles
- **FAN (Ventilador)**: Control de temperatura, humedad y ajuste de VPD.
- **LIGHT (Luces LED)**: Control de fotoperíodo.
- **IRRIGATION (Bomba de Riego)**: Hidratación del sustrato.
- **HUMIDIFIER (Humidificador)**: Aumento de humedad relativa.
- **HEATER (Calentador)**: Climas fríos o control nocturno.

## Acciones de Control
- `ON`: Encendido forzado.
- `OFF`: Apagado forzado.
- `AUTO`: Delegar en la lógica local del controlador IoT (Umbrales automáticos).

## Trazabilidad y Registro (Actuator Log)
Cada vez que emitas un comando o el sistema automático actúe, se generará una entrada en el **actuator_log**. Esto permite al usuario auditar:
- Quién ejecutó la acción (IA, Usuario o Sistema).
- El motivo (`reason`) de la acción.
- La fecha y hora exacta del cambio de estado.

## Protocolo de Decisión por Zona
1. **Contexto Espacial**: Nunca asumas que una acción en una zona afecta a otra. Usa siempre el `zone_id`.
2. **Prioridad de Seguridad**: No actives el riego si los sensores de la zona reportan humedad > 90% o inundación detected.
3. **Eficiencia Energética**: Prefiere el uso de FAN para enfriar antes que otros métodos si el VPD lo permite.

