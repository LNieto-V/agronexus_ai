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

    @property
    def system_mode(self) -> str:
        """Returns the current system mode."""
        return self._state.get("system_mode", "AUTO")

    def update_mode(self, mode: str) -> bool:
        """Updates the system mode (AUTO or MANUAL)."""
        valid_modes = ["AUTO", "MANUAL"]
        if mode.upper() in valid_modes:
            self._state["system_mode"] = mode.upper()
            return True
        return False

# Singleton para el estado del servidor
backend_state = StateService()
