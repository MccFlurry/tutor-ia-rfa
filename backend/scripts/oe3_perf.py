"""
oe3_perf.py — Harness de rendimiento [OE3] (Sprint 5 · despliegue GCE).

Mide los 4 indicadores de RENDIMIENTO de OE3 sobre el sistema desplegado:
  - TTFT  P95 ≤ 2.5 s    (time-to-first-token)
  - ITL   P95 ≤ 250 ms   (inter-token latency)
  - throughput ≥ 8 tok/s  a concurrencia 3
  - e2e   P95 ≤ 8 s      (request completo de /chat)

Por qué dos planos de medición:
  - TTFT / ITL / throughput se miden contra **Ollama directo** (`/api/chat`,
    stream=true) porque el endpoint /chat del backend es BLOQUEANTE: el cliente
    recibe la respuesta completa de una sola vez, sin streaming → es imposible
    cronometrar el primer token o los gaps inter-token desde fuera del backend.
  - e2e se mide contra el **endpoint real** `/chat/sessions/{id}/message` con
    autenticación, que es lo que vive el estudiante (embed + pgvector + rerank +
    LLM + BD).

Notas de fidelidad:
  - El RAG cachea en Redis (`rag:{hash}` TTL 1h). Para medir latencia REAL de
    generación (no cache hits), el e2e usa preguntas con nonce único.
  - El plano de generación usa un system prompt + contexto sintético de tamaño
    comparable al de producción para cargar el prompt_eval de forma realista.

Uso (en la VM, con el stack levantado, desde el contenedor backend):
    docker compose exec backend python scripts/oe3_perf.py
    docker compose exec backend python scripts/oe3_perf.py --iterations 40 --concurrency 3
    docker compose exec backend python scripts/oe3_perf.py --e2e --api-base https://api.tutoriesrfa.lat/api/v1

Salida: reporte JSON a stdout + archivo oe3_results/perf_<ts>.json
"""

import argparse
import asyncio
import json
import math
import os
import time

import httpx

# Allow running via `python scripts/oe3_perf.py` from /app (mismo patron que ingest_corpus.py)
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.config import settings


# ------------------------------------------------------------------
# Umbrales oficiales OE3 (rendimiento)
# ------------------------------------------------------------------
THRESHOLDS = {
    "ttft_p95_s": {"target": 2.5, "op": "<="},
    "itl_p95_ms": {"target": 250.0, "op": "<="},
    "throughput_tok_s": {"target": 8.0, "op": ">="},
    "e2e_p95_s": {"target": 8.0, "op": "<="},
}

# Contexto sintético (~ tamaño de un par de chunks reales del corpus) para que el
# prompt_eval de Ollama se parezca al de producción. No pretende ser correcto,
# solo cargar el modelo de forma realista.
CONTEXT_SAMPLE = (
    "[Fragmento 1 — Fuente: modulo-2-kotlin.md]\n"
    "En Kotlin, una `data class` genera automaticamente equals(), hashCode(), "
    "toString() y copy(). Las propiedades se declaran con val (inmutable) o var "
    "(mutable). El operador Elvis ?: provee un valor por defecto cuando la "
    "expresion de la izquierda es null. Las funciones de extension permiten "
    "agregar comportamiento a clases existentes sin heredar de ellas.\n\n"
    "---\n\n"
    "[Fragmento 2 — Fuente: modulo-3-ui.md]\n"
    "En Jetpack Compose, una funcion @Composable describe la UI de forma "
    "declarativa. El estado se maneja con remember y mutableStateOf; cuando el "
    "estado cambia, Compose recompone solo las partes afectadas. Los modificadores "
    "(Modifier) se encadenan para ajustar tamano, padding y comportamiento."
)

SYSTEM_TEMPLATE = (
    "Eres un tutor academico del curso de Aplicaciones Moviles del IESTP RFA. "
    "Responde SIEMPRE en espanol peruano, basandote unicamente en el CONTEXTO. "
    "Si el contexto no cubre algo, dilo; no inventes.\n\n"
    "CONTEXTO DEL CURSO:\n{context}\n\nHISTORIAL: Sin historial previo."
)

# Preguntas representativas del dominio (fallback si no hay golden set).
FALLBACK_QUESTIONS = [
    "Que es una data class en Kotlin y para que sirve?",
    "Como funciona el operador Elvis en Kotlin?",
    "Para que se usa remember en Jetpack Compose?",
    "Que diferencia hay entre val y var?",
    "Como se declara una funcion de extension en Kotlin?",
    "Que hace mutableStateOf en Compose?",
    "Como se encadenan los Modifier en Compose?",
    "Que metodos genera automaticamente una data class?",
    "Como se maneja el estado en una funcion Composable?",
    "Que es la recomposicion en Jetpack Compose?",
]


# ------------------------------------------------------------------
# Utilidades de percentiles
# ------------------------------------------------------------------
def percentile(values: list[float], p: float) -> float | None:
    """Percentil p (0-100) por interpolacion lineal."""
    if not values:
        return None
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return s[int(k)]
    return s[f] + (s[c] - s[f]) * (k - f)


def summarize(values: list[float]) -> dict:
    return {
        "n": len(values),
        "min": min(values) if values else None,
        "mean": (sum(values) / len(values)) if values else None,
        "p50": percentile(values, 50),
        "p95": percentile(values, 95),
        "max": max(values) if values else None,
    }


def load_questions() -> list[str]:
    """Usa el golden set si esta disponible; si no, las preguntas fallback."""
    gs_path = os.path.join(
        os.path.dirname(__file__), "..", "tests", "fixtures", "golden_set.json"
    )
    try:
        with open(gs_path, encoding="utf-8") as fh:
            data = json.load(fh)
        items = data.get("questions", []) if isinstance(data, dict) else data
        qs = [it["question"] for it in items if isinstance(it, dict) and it.get("question")]
        if qs:
            return qs
    except (FileNotFoundError, KeyError, TypeError, json.JSONDecodeError):
        pass
    return FALLBACK_QUESTIONS


# ------------------------------------------------------------------
# Plano 1: generacion (TTFT / ITL / throughput) contra Ollama directo
# ------------------------------------------------------------------
async def measure_generation(
    client: httpx.AsyncClient,
    base_url: str,
    model: str,
    question: str,
    num_predict: int,
) -> dict:
    """Stream contra Ollama /api/chat; devuelve TTFT, gaps inter-token y tok/s."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_TEMPLATE.format(context=CONTEXT_SAMPLE)},
            {"role": "user", "content": question},
        ],
        "stream": True,
        "options": {"temperature": 0.1, "num_ctx": 8192, "num_predict": num_predict},
    }

    t0 = time.perf_counter()
    first_t: float | None = None
    chunk_times: list[float] = []
    final: dict = {}

    async with client.stream("POST", f"{base_url}/api/chat", json=payload) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line.strip():
                continue
            obj = json.loads(line)
            now = time.perf_counter()
            content = obj.get("message", {}).get("content", "")
            if content:
                if first_t is None:
                    first_t = now
                chunk_times.append(now)
            if obj.get("done"):
                final = obj

    t_end = time.perf_counter()
    ttft = (first_t - t0) if first_t is not None else None
    gaps = [chunk_times[i] - chunk_times[i - 1] for i in range(1, len(chunk_times))]

    # tok/s autoritativo desde las metricas de Ollama (eval_count / eval_duration ns)
    eval_count = final.get("eval_count")
    eval_dur_ns = final.get("eval_duration")
    tok_s = None
    if eval_count and eval_dur_ns:
        tok_s = eval_count / (eval_dur_ns / 1e9)

    return {
        "ttft_s": ttft,
        "gaps_s": gaps,
        "tokens": eval_count or len(chunk_times),
        "tok_s_single": tok_s,
        "wall_s": t_end - t0,
    }


async def run_generation(args) -> dict:
    questions = load_questions()
    base_url = args.ollama_base or settings.OLLAMA_BASE_URL
    model = args.model or settings.OLLAMA_MODEL

    sem = asyncio.Semaphore(args.concurrency)
    results: list[dict] = []
    errors = 0

    async def worker(i: int):
        nonlocal errors
        q = questions[i % len(questions)]
        async with sem:
            try:
                r = await measure_generation(client, base_url, model, q, args.num_predict)
                results.append(r)
            except Exception as exc:  # noqa: BLE001
                errors += 1
                print(f"  [gen] error iter {i}: {exc}")

    timeout = httpx.Timeout(args.timeout, read=args.timeout)
    print(f"==> Generacion: {args.iterations} reqs, conc {args.concurrency}, modelo {model}")
    run_t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=timeout) as client:
        await asyncio.gather(*(worker(i) for i in range(args.iterations)))
    run_wall = time.perf_counter() - run_t0

    ttfts = [r["ttft_s"] for r in results if r["ttft_s"] is not None]
    all_gaps_ms = [g * 1000.0 for r in results for g in r["gaps_s"]]
    total_tokens = sum(r["tokens"] for r in results)
    # throughput agregado del sistema bajo concurrencia sostenida = tokens / wall
    throughput = total_tokens / run_wall if run_wall > 0 else None
    single_tok_s = [r["tok_s_single"] for r in results if r["tok_s_single"]]

    return {
        "requests_ok": len(results),
        "requests_err": errors,
        "run_wall_s": round(run_wall, 2),
        "total_tokens": total_tokens,
        "ttft_s": summarize(ttfts),
        "itl_ms": summarize(all_gaps_ms),
        "throughput_tok_s_aggregate": round(throughput, 2) if throughput else None,
        "tok_s_per_request": summarize(single_tok_s),
    }


# ------------------------------------------------------------------
# Plano 2: e2e contra el endpoint real /chat (autenticado)
# ------------------------------------------------------------------
async def login(client: httpx.AsyncClient, api_base: str) -> str:
    resp = await client.post(
        f"{api_base}/auth/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def run_e2e(args) -> dict:
    api_base = args.api_base
    questions = load_questions()
    timeout = httpx.Timeout(args.timeout, read=args.timeout)

    print(f"==> e2e: {args.e2e_iterations} reqs contra {api_base}/chat")
    latencies: list[float] = []
    statuses: dict[int, int] = {}

    async with httpx.AsyncClient(timeout=timeout, verify=not args.insecure) as client:
        token = await login(client, api_base)
        headers = {"Authorization": f"Bearer {token}"}

        for i in range(args.e2e_iterations):
            # sesion nueva por request → sin acumular historial
            sresp = await client.post(f"{api_base}/chat/sessions", headers=headers)
            if sresp.status_code != 201:
                statuses[sresp.status_code] = statuses.get(sresp.status_code, 0) + 1
                if sresp.status_code == 429:
                    print("  [e2e] 429 rate limit alcanzado → detengo el muestreo")
                    break
                continue
            sid = sresp.json()["id"]

            # nonce para evitar cache Redis y medir generacion real
            q = f"{questions[i % len(questions)]} (consulta #{i}-{int(time.time())})"
            t0 = time.perf_counter()
            mresp = await client.post(
                f"{api_base}/chat/sessions/{sid}/message",
                headers=headers,
                json={"content": q},
            )
            dt = time.perf_counter() - t0
            statuses[mresp.status_code] = statuses.get(mresp.status_code, 0) + 1
            if mresp.status_code == 200:
                latencies.append(dt)
            elif mresp.status_code == 429:
                print("  [e2e] 429 rate limit alcanzado → detengo el muestreo")
                break

    return {
        "requests_ok": len(latencies),
        "status_counts": statuses,
        "e2e_s": summarize(latencies),
        "note": (
            "Limitado por CHAT_RATE_LIMIT_PER_HOUR. Para una muestra mayor, sube "
            "ese valor en .env durante la medicion o usa varios usuarios."
        ),
    }


# ------------------------------------------------------------------
# Evaluacion vs umbrales + salida
# ------------------------------------------------------------------
def evaluate(gen: dict, e2e: dict | None) -> dict:
    checks = {}

    def check(name, value):
        t = THRESHOLDS[name]
        if value is None:
            checks[name] = {"value": None, "target": t["target"], "pass": None}
            return
        ok = value <= t["target"] if t["op"] == "<=" else value >= t["target"]
        checks[name] = {"value": round(value, 3), "target": t["target"], "op": t["op"], "pass": ok}

    check("ttft_p95_s", gen["ttft_s"]["p95"])
    check("itl_p95_ms", gen["itl_ms"]["p95"])
    check("throughput_tok_s", gen["throughput_tok_s_aggregate"])
    check("e2e_p95_s", e2e["e2e_s"]["p95"] if e2e and e2e["e2e_s"] else None)
    return checks


async def main():
    ap = argparse.ArgumentParser(description="Harness de rendimiento OE3")
    ap.add_argument("--iterations", type=int, default=30, help="reqs plano generacion")
    ap.add_argument("--concurrency", type=int, default=3, help="concurrencia (OE3 = 3)")
    ap.add_argument("--num-predict", type=int, default=256, help="tokens a generar por req")
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--ollama-base", default=None, help="override OLLAMA_BASE_URL")
    ap.add_argument("--model", default=None, help="override OLLAMA_MODEL")
    ap.add_argument("--e2e", action="store_true", help="ademas medir e2e contra /chat")
    ap.add_argument("--e2e-iterations", type=int, default=15)
    ap.add_argument("--api-base", default="http://localhost:8000/api/v1")
    ap.add_argument("--insecure", action="store_true", help="no verificar TLS (self-signed)")
    args = ap.parse_args()

    gen = await run_generation(args)
    e2e = await run_e2e(args) if args.e2e else None
    checks = evaluate(gen, e2e)

    report = {
        "kind": "oe3_perf",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": args.model or settings.OLLAMA_MODEL,
        "concurrency": args.concurrency,
        "generation": gen,
        "e2e": e2e,
        "checks": checks,
        "verdict": all(c["pass"] for c in checks.values() if c["pass"] is not None),
    }

    out_dir = "oe3_results"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"perf_{time.strftime('%Y%m%d_%H%M%S')}.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(json.dumps(report["checks"], indent=2, ensure_ascii=False))
    print("=" * 60)
    print(f"Reporte completo: {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
