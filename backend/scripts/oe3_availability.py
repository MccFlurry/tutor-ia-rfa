"""
oe3_availability.py — Harness de DISPONIBILIDAD + trazabilidad de errores [OE3].

Mide los indicadores de disponibilidad de OE3 a partir de dos fuentes que se
acumulan mientras el sistema corre (idealmente durante toda la ventana del piloto):

  1. Log de acceso JSON de Caddy (/var/log/caddy/access.log) →
       - tasa de 5xx ≤ 2 %
       - latencia P50/P95/P99 a nivel proxy
  2. Log del poller de salud (/var/log/tutor/health.log, CSV: epoch,code,latency) →
       - uptime ≥ 99 %
       - health checks ≥ 99 %
       - MTBF ≥ 48 h

El poller lo genera `infra/scripts/health-poller.sh` (curl /health cada 60 s).
Para MTBF ≥ 48 h se necesita una ventana de observación de al menos ~48 h.

Uso (en la VM):
    python scripts/oe3_availability.py \
        --caddy-log /var/log/caddy/access.log \
        --health-log /var/log/tutor/health.log

Salida: reporte JSON a stdout + archivo oe3_results/availability_<ts>.json
"""

import argparse
import json
import math
import os
import time


THRESHOLDS = {
    "uptime_pct": {"target": 99.0, "op": ">="},
    "health_pct": {"target": 99.0, "op": ">="},
    "http_5xx_pct": {"target": 2.0, "op": "<="},
    "mtbf_hours": {"target": 48.0, "op": ">="},
}


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * (p / 100.0)
    f, c = math.floor(k), math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] + (s[c] - s[f]) * (k - f)


# ------------------------------------------------------------------
# Caddy access log (JSON lines)
# ------------------------------------------------------------------
def parse_caddy(path: str) -> dict:
    total = 0
    by_class = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0, "other": 0}
    durations: list[float] = []

    if not os.path.exists(path):
        return {"available": False, "reason": f"no existe {path}"}

    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            status = obj.get("status")
            if not isinstance(status, int):
                continue
            total += 1
            cls = f"{status // 100}xx"
            by_class[cls if cls in by_class else "other"] += 1
            dur = obj.get("duration")
            if isinstance(dur, (int, float)):
                durations.append(float(dur))

    if total == 0:
        return {"available": False, "reason": "log vacio o sin requests"}

    pct_5xx = 100.0 * by_class["5xx"] / total
    return {
        "available": True,
        "total_requests": total,
        "by_class": by_class,
        "http_5xx_pct": round(pct_5xx, 3),
        "latency_s": {
            "p50": percentile(durations, 50),
            "p95": percentile(durations, 95),
            "p99": percentile(durations, 99),
            "max": max(durations) if durations else None,
        },
    }


# ------------------------------------------------------------------
# Health poller log (CSV: epoch,code,latency)
# ------------------------------------------------------------------
def parse_health(path: str) -> dict:
    if not os.path.exists(path):
        return {"available": False, "reason": f"no existe {path}"}

    samples: list[tuple[int, int]] = []  # (epoch, code)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = line.strip().split(",")
            if len(parts) < 2:
                continue
            try:
                epoch = int(float(parts[0]))
                code = int(parts[1])
            except ValueError:
                continue
            samples.append((epoch, code))

    if len(samples) < 2:
        return {"available": False, "reason": "menos de 2 muestras"}

    samples.sort(key=lambda s: s[0])
    total = len(samples)
    ok = sum(1 for _, c in samples if c == 200)
    uptime_pct = 100.0 * ok / total

    # Episodios de fallo: rachas consecutivas de codigo != 200
    failures = 0
    prev_ok = True
    for _, c in samples:
        is_ok = c == 200
        if not is_ok and prev_ok:
            failures += 1
        prev_ok = is_ok

    window_s = samples[-1][0] - samples[0][0]
    window_h = window_s / 3600.0
    # MTBF = tiempo operativo total / numero de fallos. Sin fallos → ≥ ventana.
    mtbf_h = window_h / failures if failures > 0 else window_h

    return {
        "available": True,
        "samples": total,
        "ok": ok,
        "uptime_pct": round(uptime_pct, 3),
        "health_pct": round(uptime_pct, 3),  # mismo instrumento
        "window_hours": round(window_h, 2),
        "failure_episodes": failures,
        "mtbf_hours": round(mtbf_h, 2),
        "mtbf_note": (
            "Sin fallos en la ventana → MTBF ≥ ventana observada."
            if failures == 0
            else "MTBF = ventana / episodios de fallo."
        ),
    }


def evaluate(caddy: dict, health: dict) -> dict:
    checks = {}

    def check(name, value, available):
        t = THRESHOLDS[name]
        if not available or value is None:
            checks[name] = {"value": value, "target": t["target"], "pass": None}
            return
        ok = value <= t["target"] if t["op"] == "<=" else value >= t["target"]
        checks[name] = {"value": value, "target": t["target"], "op": t["op"], "pass": ok}

    check("uptime_pct", health.get("uptime_pct"), health.get("available"))
    check("health_pct", health.get("health_pct"), health.get("available"))
    check("http_5xx_pct", caddy.get("http_5xx_pct"), caddy.get("available"))
    check("mtbf_hours", health.get("mtbf_hours"), health.get("available"))
    return checks


def main():
    ap = argparse.ArgumentParser(description="Harness de disponibilidad OE3")
    ap.add_argument("--caddy-log", default="/var/log/caddy/access.log")
    ap.add_argument("--health-log", default="/var/log/tutor/health.log")
    args = ap.parse_args()

    caddy = parse_caddy(args.caddy_log)
    health = parse_health(args.health_log)
    checks = evaluate(caddy, health)

    report = {
        "kind": "oe3_availability",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "caddy": caddy,
        "health": health,
        "checks": checks,
        "verdict": all(c["pass"] for c in checks.values() if c["pass"] is not None),
    }

    out_dir = "oe3_results"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"availability_{time.strftime('%Y%m%d_%H%M%S')}.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(json.dumps(report["checks"], indent=2, ensure_ascii=False))
    print("=" * 60)
    print(f"Reporte completo: {out_path}")


if __name__ == "__main__":
    main()
