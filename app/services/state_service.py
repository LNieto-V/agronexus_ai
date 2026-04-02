from typing import Any, Dict

class StateService:
    def __init__(self):
        # Variables de estado locales del backend (simulando sensores o flags de sistema)
        self._state: Dict[str, Any] = {
            "system_mode": "AUTO",
            "last_maintenance": "2026-03-25",
            "pump_health": 0.98,
            "alerts_active": [],
            "maintenance_required": False
        }

    def get_state(self, key: str = None):
        """Returns the current state of a key or the full state."""
        if key:
            return self._state.get(key)
        return self._state

    def set_state(self, key: str, value: Any):
        """Updates a state key."""
        self._state[key] = value

# Singleton para el estado del servidor
backend_state = StateService()
