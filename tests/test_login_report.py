"""
╔══════════════════════════════════════════════════════════════════╗
║     AgroNexus AI — Test Login + Reporte General por Zona        ║
║                                                                  ║
║  Flujo:                                                          ║
║    1. Login con email/password → obtiene JWT                     ║
║    2. Lista todas las zonas del usuario                          ║
║    3. Genera un reporte general para CADA zona                   ║
║    4. Genera un reporte global (sin zona específica)             ║
║                                                                  ║
║  USO:                                                            ║
║    uv run python tests/test_login_report.py                      ║
║                                                                  ║
║  CONFIGURACIÓN:                                                  ║
║    Variables de entorno o editar la sección CONFIG abajo.         ║
║      AGRONEXUS_URL    — URL base del backend                     ║
║      AGRONEXUS_EMAIL  — Email de la cuenta                       ║
║      AGRONEXUS_PASS   — Password de la cuenta                    ║
╚══════════════════════════════════════════════════════════════════╝
"""

import requests
import sys
import os
import time
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURACIÓN  ← Edita estos valores o usa env vars
# ─────────────────────────────────────────────
CONFIG = {
    "BASE_URL": os.getenv("AGRONEXUS_URL", "http://agronexus-ai.vercel.app/api"),
    "EMAIL":    os.getenv("AGRONEXUS_EMAIL", ""),
    "PASSWORD": os.getenv("AGRONEXUS_PASS", ""),
    "TIMEOUT":  60,  # Mayor por que los reportes AI pueden tardar
}

# ─────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────

class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    MAGENTA= "\033[95m"
    DIM    = "\033[2m"

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

def url(path: str) -> str:
    base = CONFIG["BASE_URL"].rstrip("/")
    # Si la base ya termina en /api, no duplicar
    if base.endswith("/api") and path.startswith("/api"):
        path = path[4:]  # Quitar /api del path
    return f"{base}/{path.lstrip('/')}"


# ─────────────────────────────────────────────
# PASO 1: LOGIN
# ─────────────────────────────────────────────

def step_login() -> str | None:
    """POST /api/auth/login → obtiene access_token."""
    header("PASO 1 — Login con credenciales")

    if not CONFIG["EMAIL"] or not CONFIG["PASSWORD"]:
        print(f"  {C.RED}✘ AGRONEXUS_EMAIL y/o AGRONEXUS_PASS no configurados.{C.RESET}")
        print(f"  {C.YELLOW}  Configura las variables de entorno:{C.RESET}")
        print(f"  {C.DIM}    export AGRONEXUS_EMAIL='tu@email.com'{C.RESET}")
        print(f"  {C.DIM}    export AGRONEXUS_PASS='tu_password'{C.RESET}")
        results.append({"test": "POST /auth/login", "ok": False, "status": 0})
        return None

    payload = {
        "email": CONFIG["EMAIL"],
        "password": CONFIG["PASSWORD"],
    }

    try:
        r = requests.post(
            url("/api/auth/login"),
            json=payload,
            timeout=CONFIG["TIMEOUT"]
        )

        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token", "")
            user  = data.get("user", {})
            email = user.get("email", "desconocido") if isinstance(user, dict) else "—"
            expires = data.get("expires_in", "?")
            log_result(
                "POST /auth/login",
                True, r.status_code,
                f"user={email} | token={token[:20]}... | expires_in={expires}s"
            )
            return token
        else:
            detail = r.text[:120]
            log_result("POST /auth/login", False, r.status_code, detail)
            return None

    except requests.exceptions.ConnectionError:
        print(f"  {C.RED}✘ No se pudo conectar a {CONFIG['BASE_URL']}{C.RESET}")
        results.append({"test": "POST /auth/login", "ok": False, "status": 0})
        return None
    except Exception as e:
        log_result("POST /auth/login", False, 0, str(e))
        return None


# ─────────────────────────────────────────────
# PASO 2: LISTAR ZONAS
# ─────────────────────────────────────────────

def step_list_zones(token: str) -> list[dict]:
    """GET /api/zones/ → lista todas las zonas del usuario."""
    header("PASO 2 — Listar zonas del usuario")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        r = requests.get(url("/api/zones/"), headers=headers, timeout=CONFIG["TIMEOUT"])

        if r.status_code == 200:
            zones = r.json()
            if not zones:
                log_result("GET /zones/", True, r.status_code, "0 zonas encontradas (vacío)")
                return []

            print(f"\n  {C.MAGENTA}{C.BOLD}  Zonas encontradas: {len(zones)}{C.RESET}")
            for i, z in enumerate(zones, 1):
                name = z.get("name", "Sin nombre")
                zone_id = z.get("id", "?")
                crop = z.get("crop_type", "—")
                print(f"    {C.DIM}{i}. {name} (id={zone_id[:12]}..., cultivo={crop}){C.RESET}")
            print()

            log_result("GET /zones/", True, r.status_code, f"{len(zones)} zona(s) encontrada(s)")
            return zones
        else:
            log_result("GET /zones/", False, r.status_code, r.text[:120])
            return []

    except Exception as e:
        log_result("GET /zones/", False, 0, str(e))
        return []


# ─────────────────────────────────────────────
# PASO 3: GENERAR REPORTES POR ZONA
# ─────────────────────────────────────────────

def step_generate_reports(token: str, zones: list[dict]):
    """POST /api/chat/report → genera reporte para cada zona + global."""
    header("PASO 3 — Generar reportes agronómicos")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # 3a. Reporte por cada zona individual
    for i, zone in enumerate(zones, 1):
        zone_id   = zone.get("id")
        zone_name = zone.get("name", "Sin nombre")

        print(f"\n  {C.MAGENTA}▸ Reporte {i}/{len(zones)}: {zone_name}{C.RESET}")

        payload = {
            "zone_id": zone_id,
            "hours": 24,
            "focus": "general",
        }

        try:
            start = time.time()
            r = requests.post(
                url("/api/chat/report"),
                headers=headers,
                json=payload,
                timeout=CONFIG["TIMEOUT"]
            )
            elapsed = round(time.time() - start, 1)

            if r.status_code == 200:
                data = r.json()
                response = data.get("response", "")
                preview  = response[:100].replace("\n", " ") + "..." if len(response) > 100 else response
                log_result(
                    f"POST /chat/report [zona: {zone_name}]",
                    True, r.status_code,
                    f"({elapsed}s) {len(response)} chars — {preview}"
                )
            elif r.status_code == 429:
                log_result(
                    f"POST /chat/report [zona: {zone_name}]",
                    False, r.status_code,
                    f"({elapsed}s) Cuota agotada — el reporte requiere reintentar más tarde"
                )
            else:
                log_result(
                    f"POST /chat/report [zona: {zone_name}]",
                    False, r.status_code,
                    f"({elapsed}s) {r.text[:100]}"
                )

        except requests.exceptions.Timeout:
            log_result(f"POST /chat/report [zona: {zone_name}]", False, 0, "TIMEOUT")
        except Exception as e:
            log_result(f"POST /chat/report [zona: {zone_name}]", False, 0, str(e))

        # Pausa entre reportes para evitar rate-limiting
        if i < len(zones):
            print(f"  {C.DIM}  ⏳ Esperando 2s antes del siguiente reporte...{C.RESET}")
            time.sleep(2)

    # 3b. Reporte GLOBAL (sin zone_id)
    print(f"\n  {C.MAGENTA}▸ Reporte GLOBAL (todas las zonas){C.RESET}")
    payload_global = {
        "zone_id": None,
        "hours": 24,
        "focus": "general",
    }

    try:
        start = time.time()
        r = requests.post(
            url("/api/chat/report"),
            headers=headers,
            json=payload_global,
            timeout=CONFIG["TIMEOUT"]
        )
        elapsed = round(time.time() - start, 1)

        if r.status_code == 200:
            data = r.json()
            response = data.get("response", "")
            preview  = response[:100].replace("\n", " ") + "..." if len(response) > 100 else response
            log_result(
                "POST /chat/report [GLOBAL]",
                True, r.status_code,
                f"({elapsed}s) {len(response)} chars — {preview}"
            )
        elif r.status_code == 429:
            log_result(
                "POST /chat/report [GLOBAL]",
                False, r.status_code,
                f"({elapsed}s) Cuota agotada"
            )
        else:
            log_result(
                "POST /chat/report [GLOBAL]",
                False, r.status_code,
                f"({elapsed}s) {r.text[:100]}"
            )

    except requests.exceptions.Timeout:
        log_result("POST /chat/report [GLOBAL]", False, 0, "TIMEOUT")
    except Exception as e:
        log_result("POST /chat/report [GLOBAL]", False, 0, str(e))


# ─────────────────────────────────────────────
# RESUMEN FINAL
# ─────────────────────────────────────────────

def print_summary() -> bool:
    header("RESUMEN FINAL")
    total  = len(results)
    passed = sum(1 for r in results if r["ok"])
    failed = total - passed
    pct    = int((passed / total) * 100) if total else 0

    bar_len = 40
    filled  = int(bar_len * passed / total) if total else 0
    bar     = f"{C.GREEN}{'█' * filled}{C.RED}{'░' * (bar_len - filled)}{C.RESET}"

    print(f"\n  {bar}  {pct}%")
    print(f"\n  {C.GREEN}✔ Pasados: {passed}{C.RESET}   "
          f"{C.RED}✘ Fallidos: {failed}{C.RESET}   "
          f"Total: {total}")

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
    print(f"\n{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════════╗{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}║  AgroNexus AI — Login + Reporte General por Zonas    ║{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}╚══════════════════════════════════════════════════════════╝{C.RESET}")
    print(f"\n  {C.DIM}Backend : {CONFIG['BASE_URL']}{C.RESET}")
    print(f"  {C.DIM}Email   : {CONFIG['EMAIL'] or '✘ no configurado'}{C.RESET}")
    print(f"  {C.DIM}Hora    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{C.RESET}")

    # PASO 1: Login
    token = step_login()
    if not token:
        print(f"\n{C.RED}  ✘ No se pudo autenticar. Abortando.{C.RESET}\n")
        print_summary()
        sys.exit(1)

    # PASO 2: Listar zonas
    zones = step_list_zones(token)

    # PASO 3: Generar reportes
    step_generate_reports(token, zones)

    # Resumen
    all_ok = print_summary()
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
