#!/usr/bin/env python3
"""
run_llm_benchmark.py — Benchmark de 3 LLMs open-source vía Ollama.

Ejecuta los 50 prompts del golden set sobre qwen2.5:7b, llama3:8b y mistral:7b,
midiendo latencia por consulta, tokens/segundo y consumo de VRAM.

Salida: results/llm_benchmark.json (datos crudos para el reporte-LLM.docx).

Uso:
    python run_llm_benchmark.py

Pre-requisitos:
    1. Ollama corriendo en localhost:11434
    2. Modelos descargados:
       ollama pull qwen2.5:7b-instruct-q4_K_M
       ollama pull llama3:8b-instruct-q4_K_M
       ollama pull mistral:7b-instruct-q4_K_M
    3. Python 3.11+ con httpx instalado:
       pip install httpx
"""

import json
import os
import statistics
import time
from pathlib import Path

import httpx

# ─────────────────────────────────────────────────────────────────────────────
# Configuración del benchmark (mantener idéntica para fair comparison)
# ─────────────────────────────────────────────────────────────────────────────
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODELS = [
    "qwen2.5:7b-instruct-q4_K_M",
    "llama3:8b-instruct-q4_K_M",
    "mistral:7b-instruct-q4_K_M",
]
SYSTEM_PROMPT = (
    "Eres un tutor académico de la asignatura Aplicaciones Móviles "
    "del IESTP República Federal de Alemania (Chiclayo, Perú). "
    "Respondes en español latinoamericano con tono pedagógico. "
    "Usa ejemplos en Kotlin cuando sea pertinente. "
    "Si la pregunta no está relacionada con desarrollo móvil, Android o Kotlin, "
    "indícalo amablemente y sugiere volver al tema del curso."
)
TEMPERATURE = 0.3
NUM_CTX = 4096
NUM_PREDICT = 1024
REQUEST_TIMEOUT_S = 300
KEEP_ALIVE = "10m"


def get_loaded_model_info(model_name: str) -> dict:
    """Consulta /api/ps para obtener el tamaño del modelo en VRAM."""
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/ps", timeout=10)
        r.raise_for_status()
        data = r.json()
        for m in data.get("models", []):
            if m.get("name") == model_name or m.get("model") == model_name:
                return {
                    "size_vram_bytes": m.get("size_vram", 0),
                    "size_bytes": m.get("size", 0),
                }
    except Exception as e:
        print(f"  ⚠ no se pudo consultar /api/ps: {e}")
    return {"size_vram_bytes": 0, "size_bytes": 0}


def generate(model: str, prompt: str) -> dict:
    """Llama a /api/generate y mide latencia."""
    payload = {
        "model": model,
        "system": SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": TEMPERATURE,
            "num_ctx": NUM_CTX,
            "num_predict": NUM_PREDICT,
        },
        "keep_alive": KEEP_ALIVE,
    }
    t0 = time.perf_counter()
    r = httpx.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=REQUEST_TIMEOUT_S)
    t1 = time.perf_counter()
    r.raise_for_status()
    data = r.json()
    eval_duration_ns = data.get("eval_duration", 0)
    eval_count = data.get("eval_count", 0)
    tps = (eval_count / (eval_duration_ns / 1e9)) if eval_duration_ns > 0 else 0.0
    return {
        "response": data.get("response", ""),
        "latency_s": t1 - t0,
        "tokens_generated": eval_count,
        "prompt_tokens": data.get("prompt_eval_count", 0),
        "tokens_per_second": tps,
        "total_duration_ns": data.get("total_duration", 0),
        "load_duration_ns": data.get("load_duration", 0),
    }


def benchmark_model(model: str, prompts: list[dict]) -> dict:
    print(f"\n{'─' * 72}\n▶ {model}\n{'─' * 72}")
    print("  ⏳ warmup (carga el modelo en VRAM)...")
    try:
        generate(model, "Hola. Responde solo con OK.")
    except Exception as e:
        print(f"  ✗ warmup falló: {e}")
        return {"model": model, "error": str(e), "results": []}

    info = get_loaded_model_info(model)
    vram_gb = info["size_vram_bytes"] / (1024 ** 3)
    total_gb = info["size_bytes"] / (1024 ** 3)
    print(f"  📊 en VRAM: {vram_gb:.2f} GB · tamaño total: {total_gb:.2f} GB")

    results = []
    n = len(prompts)
    for i, p in enumerate(prompts, 1):
        try:
            out = generate(model, p["prompt"])
            results.append({
                "prompt_id": p["id"],
                "module": p["module"],
                "type": p["type"],
                "prompt": p["prompt"],
                "response": out["response"],
                "latency_s": out["latency_s"],
                "tokens_generated": out["tokens_generated"],
                "prompt_tokens": out["prompt_tokens"],
                "tokens_per_second": out["tokens_per_second"],
            })
            print(f"  [{i:>2}/{n}] {p['id']:<10} {p['type']:<11} {out['latency_s']:>6.2f}s  {out['tokens_generated']:>4}tok")
        except Exception as e:
            print(f"  [{i:>2}/{n}] {p['id']:<10} ✗ error: {e}")
            results.append({
                "prompt_id": p["id"],
                "module": p["module"],
                "type": p["type"],
                "prompt": p["prompt"],
                "error": str(e),
            })

    valid = [r for r in results if "latency_s" in r]
    latencies = [r["latency_s"] for r in valid]
    tps_values = [r["tokens_per_second"] for r in valid if r["tokens_per_second"] > 0]

    def p95(xs):
        if not xs:
            return 0.0
        xs_sorted = sorted(xs)
        k = max(0, int(len(xs_sorted) * 0.95) - 1)
        return xs_sorted[k]

    return {
        "model": model,
        "n_prompts": len(prompts),
        "n_successful": len(valid),
        "size_vram_bytes": info["size_vram_bytes"],
        "size_vram_gb": vram_gb,
        "size_total_gb": total_gb,
        "latency_avg_s": statistics.mean(latencies) if latencies else 0,
        "latency_median_s": statistics.median(latencies) if latencies else 0,
        "latency_p95_s": p95(latencies),
        "latency_min_s": min(latencies) if latencies else 0,
        "latency_max_s": max(latencies) if latencies else 0,
        "latency_stdev_s": statistics.stdev(latencies) if len(latencies) > 1 else 0,
        "tokens_per_second_avg": statistics.mean(tps_values) if tps_values else 0,
        "results": results,
    }


def main():
    here = Path(__file__).parent
    prompts_path = here / "prompts_llm.json"
    out_dir = here / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "llm_benchmark.json"

    if not prompts_path.exists():
        raise FileNotFoundError(f"No se encontró {prompts_path}")

    prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
    print(f"📚 Cargados {len(prompts)} prompts desde {prompts_path}")
    print(f"🎯 Benchmark de {len(MODELS)} modelos: {', '.join(MODELS)}")
    print(f"💾 Resultados en: {out_path}\n")

    all_results = {
        "config": {
            "system_prompt": SYSTEM_PROMPT,
            "temperature": TEMPERATURE,
            "num_ctx": NUM_CTX,
            "num_predict": NUM_PREDICT,
            "n_prompts": len(prompts),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "models": {},
    }

    for model in MODELS:
        all_results["models"][model] = benchmark_model(model, prompts)
        # guardado incremental por si se cae a mitad
        out_path.write_text(
            json.dumps(all_results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(f"\n{'═' * 72}\n✅ Benchmark completo — {out_path}\n{'═' * 72}")
    print("\n📊 Resumen:")
    print(f"{'Modelo':<36}{'Lat. avg':>12}{'Lat. p95':>12}{'Tok/s':>10}{'VRAM':>10}")
    print("─" * 80)
    for model, r in all_results["models"].items():
        if r.get("error"):
            print(f"{model:<36}  ERROR: {r['error']}")
            continue
        print(
            f"{model:<36}"
            f"{r['latency_avg_s']:>10.2f}s"
            f"{r['latency_p95_s']:>10.2f}s"
            f"{r['tokens_per_second_avg']:>10.1f}"
            f"{r['size_vram_gb']:>9.2f}G"
        )


if __name__ == "__main__":
    main()
