"""
AgroNexus AI — Transmisión masiva de 80 datos de sensores
Endpoint : POST /iot/telemetry
Auth     : X-API-Key (agnx_w_...)

USO:
  export AGRONEXUS_URL="http://localhost:8000"
  export AGRONEXUS_WRITE_KEY="agnx_w_..."
  python tests/test_iot_bulk.py
"""

import requests
import random
import time
import os
import sys

# ─── CONFIG ───────────────────────────────────────────────
BASE_URL = os.getenv("AGRONEXUS_URL", "http://localhost:8000").rstrip("/")
WRITE_KEY = os.getenv("AGRONEXUS_WRITE_KEY", "")  # ← o pégalo aquí directamente
TOTAL = 80  # cantidad de envíos
DELAY = 0.2  # segundos entre envíos (ajusta a tu gusto)
TIMEOUT = 20  # segundos por request
# ──────────────────────────────────────────────────────────

ENDPOINT = f"{BASE_URL}/iot/telemetry"
HEADERS = {"X-API-Key": WRITE_KEY, "Content-Type": "application/json"}

# Colores
G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
C = "\033[96m"
D = "\033[2m"
B = "\033[1m"
X = "\033[0m"


def generate_sensor_data() -> dict:
    """Genera una lectura realista de sensores ESP32."""
    return {
        "temperature": round(random.uniform(18.0, 40.0), 1),
        "humidity": round(random.uniform(40.0, 90.0), 1),
        "light": round(random.uniform(0.0, 10000.0), 0),
        "ph": round(random.uniform(4.5, 8.0), 2),
        "ec": round(random.uniform(0.5, 4.0), 2),
    }


def progress_bar(current: int, total: int, width: int = 40) -> str:
    filled = int(width * current / total)
    pct = int(100 * current / total)
    bar = f"{G}{'█' * filled}{D}{'░' * (width - filled)}{X}"
    return f"[{bar}] {B}{pct:3d}%{X} ({current}/{total})"


def main():
    if not WRITE_KEY:
        print(f"\n{R}✘ WRITE_KEY no configurada.{X}")
        print(f"  Exporta la variable o edita el script:\n")
        print(f"  {Y}export AGRONEXUS_WRITE_KEY='agnx_w_...'{X}\n")
        sys.exit(1)

    print(f"\n{C}{B}{'═' * 56}{X}")
    print(f"{C}{B}  AgroNexus AI — Transmisión de {TOTAL} lecturas IoT{X}")
    print(f"{C}{B}{'═' * 56}{X}")
    print(f"  {D}Endpoint : {ENDPOINT}{X}")
    print(f"  {D}API Key  : {WRITE_KEY[:12]}...{X}")
    print(f"  {D}Delay    : {DELAY}s entre envíos{X}\n")

    ok_count = 0
    fail_count = 0
    actions_total = 0
    alerts_total = 0

    for i in range(1, TOTAL + 1):
        sensor_data = generate_sensor_data()
        payload = {"sensor_data": sensor_data}

        try:
            r = requests.post(ENDPOINT, headers=HEADERS, json=payload, timeout=TIMEOUT)

            if r.status_code == 200:
                data = r.json()
                acts = data.get("actions", [])
                alts = data.get("alerts", [])
                actions_total += len(acts)
                alerts_total += len(alts)
                ok_count += 1
                status_icon = G + "✔" + X
                extra = ""
                if acts:
                    extra += f" {Y}▶ {', '.join(a['device'] + '→' + a['action'] for a in acts)}{X}"
                if alts:
                    extra += f" {R}⚠ {len(alts)} alerta(s){X}"
            else:
                fail_count += 1
                status_icon = R + "✘" + X
                extra = f" {R}HTTP {r.status_code} — {r.text[:60]}{X}"

        except requests.exceptions.Timeout:
            fail_count += 1
            status_icon = R + "✘" + X
            extra = f" {R}Timeout{X}"
        except requests.exceptions.ConnectionError:
            fail_count += 1
            status_icon = R + "✘" + X
            extra = f" {R}Sin conexión{X}"
            print(
                f"\r  {status_icon} #{i:02d} — {R}No se pudo conectar al servidor.{X}"
            )
            print(f"  {Y}¿Está corriendo? →  uvicorn app.main:app --reload{X}\n")
            sys.exit(1)

        # Línea de estado
        t = sensor_data["temperature"]
        h = sensor_data["humidity"]
        ph = sensor_data["ph"]
        bar = progress_bar(i, TOTAL)
        print(f"  {status_icon} #{i:02d}  T={t}°C  H={h}%  pH={ph}  {bar}{extra}")

        if i < TOTAL:
            time.sleep(DELAY)

    # ── Resumen ────────────────────────────────────────────
    print(f"\n{C}{B}{'─' * 56}{X}")
    print(f"{C}{B}  RESUMEN{X}")
    print(f"{C}{'─' * 56}{X}")
    print(f"  Enviados  : {B}{TOTAL}{X}")
    print(f"  {G}Exitosos  : {ok_count}{X}")
    print(f"  {R}Fallidos  : {fail_count}{X}")
    print(f"  Acciones IA totales : {actions_total}")
    print(f"  Alertas totales     : {alerts_total}")
    pct = int(100 * ok_count / TOTAL)
    bar = progress_bar(ok_count, TOTAL)
    print(f"\n  Tasa de éxito: {bar}\n")

    sys.exit(0 if fail_count == 0 else 1)


if __name__ == "__main__":
    main()
