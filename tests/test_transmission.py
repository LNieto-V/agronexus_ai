"""
╔══════════════════════════════════════════════════════════════════╗
║          AgroNexus AI - Script de Prueba de Transmisión          ║
║                                                                  ║
║  Prueba la comunicación con el backend usando:                   ║
║    → JWT (Supabase)   : /chat, /conversations, /dashboard        ║
║    → API Key (WriteKey): /iot/telemetry                          ║
║                                                                  ║
║  USO:                                                            ║
║    1. Configura las variables en la sección CONFIG               ║
║    2. python tests/test_transmission.py                          ║
╚══════════════════════════════════════════════════════════════════╝
"""

import requests
import time
import random
import sys
import os
from datetime import datetime
from typing import Optional

# ─────────────────────────────────────────────
# CONFIGURACIÓN  ← Edita estos valores
# ─────────────────────────────────────────────
CONFIG = {
    # URL base del backend (local o producción)
    "BASE_URL": os.getenv("AGRONEXUS_URL", "http://localhost:8000"),

    # JWT obtenido desde Supabase (login en el frontend o supabase-py)
    # Copia el token de: Dashboard → Auth → Users → tu usuario → JWT
    "JWT_TOKEN": os.getenv("AGRONEXUS_JWT", ""),

    # API Key con permisos de escritura (agnx_w_...)
    # Créala desde el frontend o con: POST /auth/keys?key_type=write
    "WRITE_API_KEY": os.getenv("AGRONEXUS_WRITE_KEY", ""),

    # Timeout para cada petición (segundos)
    "TIMEOUT": 30,
}

# Colores para terminal
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    DIM    = "\033[2m"

# ─────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────
results: list[dict] = []

def header(title: str):
    print(f"\n{C.CYAN}{C.BOLD}{'─'*60}{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}  {title}{C.RESET}")
    print(f"{C.CYAN}{'─'*60}{C.RESET}")

def log_result(test_name: str, ok: bool, status: int, detail: str = ""):
    icon  = f"{C.GREEN}✔{C.RESET}" if ok else f"{C.RED}✘{C.RESET}"
    color = C.GREEN if ok else C.RED
    print(f"  {icon} {color}{test_name}{C.RESET}  "
          f"{C.DIM}[HTTP {status}]{C.RESET}"
          + (f"  {C.DIM}{detail}{C.RESET}" if detail else ""))
    results.append({"test": test_name, "ok": ok, "status": status})

def jwt_headers() -> dict:
    return {
        "Authorization": f"Bearer {CONFIG['JWT_TOKEN']}",
        "Content-Type": "application/json",
    }

def apikey_headers() -> dict:
    return {
        "X-API-Key": CONFIG["WRITE_API_KEY"],
        "Content-Type": "application/json",
    }

def url(path: str) -> str:
    return f"{CONFIG['BASE_URL'].rstrip('/')}/{path.lstrip('/')}"


# ─────────────────────────────────────────────
# TESTS INDIVIDUALES
# ─────────────────────────────────────────────

def test_health():
    """GET /system/health — Sin autenticación"""
    header("1. Health Check (sin auth)")
    try:
        r = requests.get(url("/system/health"), timeout=CONFIG["TIMEOUT"])
        ok = r.status_code == 200
        detail = r.json().get("status", "") if ok else r.text[:80]
        log_result("GET /system/health", ok, r.status_code, detail)
        return ok
    except requests.exceptions.ConnectionError:
        print(f"  {C.RED}✘ No se pudo conectar a {CONFIG['BASE_URL']}{C.RESET}")
        print(f"  {C.YELLOW}  ¿Está corriendo el servidor? uvicorn app.main:app --reload{C.RESET}")
        results.append({"test": "GET /system/health", "ok": False, "status": 0})
        return False


def test_chat_test_endpoint():
    """POST /chat/test — Sin autenticación (endpoint de prueba pública)"""
    header("2. Chat Test (sin auth)")
    payload = {"message": "¿Cuál es la temperatura óptima para tomates?"}
    try:
        r = requests.post(url("/chat/test"), json=payload, timeout=CONFIG["TIMEOUT"])
        ok = r.status_code == 200
        if ok:
            resp = r.json().get("response", "")
            detail = resp[:80] + "..." if len(resp) > 80 else resp
        else:
            detail = r.text[:80]
        log_result("POST /chat/test", ok, r.status_code, detail)
        return ok
    except Exception as e:
        log_result("POST /chat/test", False, 0, str(e))
        return False


def test_jwt_conversations():
    """GET /conversations — Requiere JWT"""
    header("3. Conversaciones (JWT)")
    if not CONFIG["JWT_TOKEN"]:
        print(f"  {C.YELLOW}⚠  JWT_TOKEN no configurado — saltando tests de JWT{C.RESET}")
        return None

    # 3a. Listar conversaciones
    r = requests.get(url("/conversations"), headers=jwt_headers(), timeout=CONFIG["TIMEOUT"])
    ok = r.status_code == 200
    count = len(r.json()) if ok else 0
    log_result("GET /conversations", ok, r.status_code, f"{count} conversaciones")

    # 3b. Crear conversación
    r2 = requests.post(
        url("/conversations"),
        headers=jwt_headers(),
        json={"title": f"Test {datetime.now().strftime('%H:%M:%S')}"},
        timeout=CONFIG["TIMEOUT"]
    )
    ok2 = r2.status_code == 201
    session_id: Optional[str] = None
    if ok2:
        session_id = r2.json().get("id")
        log_result("POST /conversations", ok2, r2.status_code, f"id={session_id}")
    else:
        log_result("POST /conversations", ok2, r2.status_code, r2.text[:80])

    return session_id


def test_jwt_chat(session_id: Optional[str] = None):
    """POST /chat — Requiere JWT"""
    header("4. Chat con JWT")
    if not CONFIG["JWT_TOKEN"]:
        print(f"  {C.YELLOW}⚠  JWT_TOKEN no configurado — saltando{C.RESET}")
        return

    payload = {
        "message": "Dame un resumen del estado del invernadero",
        "session_id": session_id
    }
    r = requests.post(url("/chat"), headers=jwt_headers(), json=payload, timeout=CONFIG["TIMEOUT"])
    ok = r.status_code == 200
    if ok:
        data = r.json()
        resp_preview = data.get("response", "")[:80]
        actions      = len(data.get("actions", []))
        alerts       = len(data.get("alerts", []))
        log_result("POST /chat", ok, r.status_code,
                   f"response='{resp_preview}...' | actions={actions} | alerts={alerts}")
    else:
        log_result("POST /chat", ok, r.status_code, r.text[:120])


def test_jwt_chat_history(session_id: Optional[str] = None):
    """GET /chat/history — Requiere JWT"""
    header("5. Historial de Chat (JWT)")
    if not CONFIG["JWT_TOKEN"]:
        print(f"  {C.YELLOW}⚠  JWT_TOKEN no configurado — saltando{C.RESET}")
        return

    params = {}
    if session_id:
        params["session_id"] = session_id

    r = requests.get(url("/chat/history"), headers=jwt_headers(), params=params, timeout=CONFIG["TIMEOUT"])
    ok = r.status_code == 200
    if ok:
        msgs = r.json().get("history", [])
        log_result("GET /chat/history", ok, r.status_code, f"{len(msgs)} mensajes")
    else:
        log_result("GET /chat/history", ok, r.status_code, r.text[:80])


def test_dashboard(session_id: Optional[str] = None):
    """GET /dashboard/summary — Requiere JWT"""
    header("6. Dashboard (JWT)")
    if not CONFIG["JWT_TOKEN"]:
        print(f"  {C.YELLOW}⚠  JWT_TOKEN no configurado — saltando{C.RESET}")
        return

    r = requests.get(url("/dashboard/summary"), headers=jwt_headers(), timeout=CONFIG["TIMEOUT"])
    ok = r.status_code == 200
    if ok:
        data = r.json()
        sensors = data.get("latest_sensors", {})
        log_result("GET /dashboard/summary", ok, r.status_code,
                   f"temp={sensors.get('temperature')}°C | hum={sensors.get('humidity')}%")
    else:
        log_result("GET /dashboard/summary", ok, r.status_code, r.text[:80])


def test_iot_telemetry():
    """POST /iot/telemetry — Requiere API Key (WriteKey)"""
    header("7. Telemetría IoT (API Key)")
    if not CONFIG["WRITE_API_KEY"]:
        print(f"  {C.YELLOW}⚠  WRITE_API_KEY no configurado — saltando tests de IoT{C.RESET}")
        return

    # Simula datos de sensores ESP32 con valores variados
    test_cases = [
        {
            "name": "Valores normales",
            "data": {
                "temperature": round(random.uniform(22, 26), 1),
                "humidity":    round(random.uniform(60, 75), 1),
                "light":       round(random.uniform(3000, 6000), 0),
                "ph":          round(random.uniform(6.0, 6.8), 2),
                "ec":          round(random.uniform(1.5, 2.5), 2),
            }
        },
        {
            "name": "Temperatura crítica alta (>35°C)",
            "data": {
                "temperature": 38.5,
                "humidity":    45.0,
                "light":       8000.0,
                "ph":          6.5,
                "ec":          2.0,
            }
        },
        {
            "name": "pH fuera de rango (<5.5)",
            "data": {
                "temperature": 24.0,
                "humidity":    70.0,
                "light":       5000.0,
                "ph":          4.8,
                "ec":          1.8,
            }
        },
        {
            "name": "Solo temperatura y humedad",
            "data": {
                "temperature": 25.0,
                "humidity":    68.0,
            }
        },
    ]

    for case in test_cases:
        payload = {"sensor_data": case["data"]}
        try:
            r = requests.post(
                url("/iot/telemetry"),
                headers=apikey_headers(),
                json=payload,
                timeout=CONFIG["TIMEOUT"]
            )
            ok = r.status_code == 200
            if ok:
                data    = r.json()
                actions = data.get("actions", [])
                alerts  = data.get("alerts", [])
                acts_str = ", ".join([f"{a['device']}→{a['action']}" for a in actions]) or "ninguna"
                alrt_str = f"{len(alerts)} alertas" if alerts else "sin alertas"
                log_result(f"POST /iot/telemetry [{case['name']}]", ok, r.status_code,
                           f"actions=[{acts_str}] | {alrt_str}")
            else:
                log_result(f"POST /iot/telemetry [{case['name']}]", ok, r.status_code, r.text[:80])
        except Exception as e:
            log_result(f"POST /iot/telemetry [{case['name']}]", False, 0, str(e))

        time.sleep(0.5)  # Pausa entre envíos


def test_auth_keys():
    """GET /auth/keys — Requiere JWT"""
    header("8. API Keys del Usuario (JWT)")
    if not CONFIG["JWT_TOKEN"]:
        print(f"  {C.YELLOW}⚠  JWT_TOKEN no configurado — saltando{C.RESET}")
        return

    r = requests.get(url("/auth/keys"), headers=jwt_headers(), timeout=CONFIG["TIMEOUT"])
    ok = r.status_code == 200
    if ok:
        keys  = r.json()
        types = [k.get("key_type") for k in keys]
        log_result("GET /auth/keys", ok, r.status_code, f"{len(keys)} llave(s): {types}")
    else:
        log_result("GET /auth/keys", ok, r.status_code, r.text[:80])


def test_unauthorized():
    """Verifica que los endpoints protegidos rechacen tokens inválidos"""
    header("9. Seguridad — Acceso no autorizado")

    # Sin token
    r = requests.get(url("/conversations"), timeout=CONFIG["TIMEOUT"])
    ok = r.status_code in (401, 403, 422)
    log_result("GET /conversations sin token → 401/403", ok, r.status_code)

    # Token falso
    bad_headers = {"Authorization": "Bearer token_invalido_abc123"}
    r2 = requests.post(url("/chat"), headers=bad_headers, json={"message": "test"}, timeout=CONFIG["TIMEOUT"])
    ok2 = r2.status_code in (401, 403, 422)
    log_result("POST /chat con JWT inválido → 401/403", ok2, r2.status_code)

    # API Key falsa en IoT
    bad_key_headers = {"X-API-Key": "agnx_w_fake_key_12345", "Content-Type": "application/json"}
    r3 = requests.post(
        url("/iot/telemetry"),
        headers=bad_key_headers,
        json={"sensor_data": {"temperature": 24.0}},
        timeout=CONFIG["TIMEOUT"]
    )
    ok3 = r3.status_code in (401, 403)
    log_result("POST /iot/telemetry con API Key falsa → 401/403", ok3, r3.status_code)


# ─────────────────────────────────────────────
# RESUMEN FINAL
# ─────────────────────────────────────────────

def print_summary():
    header("RESUMEN")
    total   = len(results)
    passed  = sum(1 for r in results if r["ok"])
    failed  = total - passed
    pct     = int((passed / total) * 100) if total else 0

    bar_len = 40
    filled  = int(bar_len * passed / total) if total else 0
    bar     = f"{C.GREEN}{'█' * filled}{C.RED}{'░' * (bar_len - filled)}{C.RESET}"

    print(f"\n  {bar}  {pct}%")
    print(f"\n  {C.GREEN}✔ Pasados: {passed}{C.RESET}   {C.RED}✘ Fallidos: {failed}{C.RESET}   Total: {total}")

    if failed > 0:
        print(f"\n  {C.RED}Tests fallidos:{C.RESET}")
        for r in results:
            if not r["ok"]:
                print(f"    {C.RED}✘{C.RESET} {r['test']}  [HTTP {r['status']}]")

    print()
    return failed == 0


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print(f"\n{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════╗{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}║   AgroNexus AI — Test de Transmisión con Token   ║{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}╚══════════════════════════════════════════════════╝{C.RESET}")
    print(f"\n  {C.DIM}Backend : {CONFIG['BASE_URL']}{C.RESET}")
    print(f"  {C.DIM}JWT     : {'✔ configurado' if CONFIG['JWT_TOKEN'] else '✘ no configurado'}{C.RESET}")
    print(f"  {C.DIM}API Key : {'✔ configurado' if CONFIG['WRITE_API_KEY'] else '✘ no configurado'}{C.RESET}")

    # Ejecutar tests en orden
    server_ok = test_health()
    if not server_ok:
        print(f"\n{C.RED}  El servidor no responde. Verifica que esté activo.{C.RESET}\n")
        sys.exit(1)

    test_chat_test_endpoint()
    session_id = test_jwt_conversations()
    test_jwt_chat(session_id)
    test_jwt_chat_history(session_id)
    test_dashboard()
    test_iot_telemetry()
    test_auth_keys()
    test_unauthorized()

    all_ok = print_summary()
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
