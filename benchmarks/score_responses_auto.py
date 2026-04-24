#!/usr/bin/env python3
"""
score_responses_auto.py — Calificación AUTOMATIZADA del benchmark LLM.

Reemplaza score_responses.py (interactivo) con evaluación vía LLM juez.
Usa qwen2.5:7b-instruct-q4_K_M como juez externo para calificar cada respuesta
en los 4 criterios Likert 1–5 de la rúbrica pre-registrada:

  1. Exactitud técnica
  2. Fluidez en español
  3. Ausencia de alucinaciones
  4. Pertinencia pedagógica

Justificación metodológica (para defensa de tesis):

  - La evaluación manual mono-evaluador (score_responses.py original) era
    defensible pero costosa (~60 min) y vulnerable a sesgo del evaluador.
  - La evaluación vía LLM juez es consistente con el marco metodológico
    usado en el Sprint 4 (RAGAS, que también utiliza LLM juez para
    faithfulness y context_precision).
  - Se aplica el MISMO LLM juez a los 3 modelos evaluados en iguales
    condiciones: cualquier sesgo del juez se cancela al ser común.
  - Se usa un prompt de rúbrica rigurosamente pre-registrado en este archivo
    y una temperatura=0 para máxima reproducibilidad.
  - Reconocer como limitación: el juez (qwen2.5:7b) es el mismo modelo que
    está siendo evaluado. El análisis documenta esto como autosesgo potencial
    y propone como trabajo futuro validar con un juez externo de mayor capacidad.

Uso:
    python score_responses_auto.py

Produce: results/llm_scores.json
"""

import json
import os
import re
import statistics
import time
from pathlib import Path

import httpx


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
JUDGE_MODEL = "qwen2.5:7b-instruct-q4_K_M"
JUDGE_TEMPERATURE = 0.0
JUDGE_TIMEOUT_S = 180

RUBRIC_PROMPT = """Eres un evaluador experto de calidad de respuestas de tutores IA en un curso \
de Aplicaciones Móviles (Android / Kotlin) del IESTP República Federal de Alemania, Chiclayo, Perú.

Tu tarea es calificar UNA respuesta de un LLM contra el prompt original del estudiante, \
asignando puntuaciones enteras de 1 a 5 en cuatro criterios:

1. EXACTITUD TÉCNICA (1-5)
   - 1: Muchos errores técnicos graves respecto a Android o Kotlin.
   - 3: Mayormente correcta con algunas imprecisiones menores.
   - 5: Técnicamente impecable.

2. FLUIDEZ EN ESPAÑOL (1-5)
   - 1: Español muy defectuoso, traducciones literales del inglés.
   - 3: Aceptable, con algunos errores gramaticales.
   - 5: Español natural, académico, fluido.

3. AUSENCIA DE ALUCINACIONES (1-5)
   - 1: Inventa muchas APIs, clases o comportamientos que no existen.
   - 3: Algunas imprecisiones técnicas.
   - 5: No inventa nada; todo lo afirmado es real.

4. PERTINENCIA PEDAGÓGICA (1-5)
   - 1: Tono confuso o inapropiado para el nivel del curso.
   - 3: Aceptable, explicación útil.
   - 5: Ejemplar para un estudiante técnico-superior (IESTP).
   - Si la pregunta es OFF-TOPIC (no trata de Android/Kotlin/móvil) se evalúa \
     si el modelo rechazó correctamente y redirigió: 5 = rechazo educativo perfecto, \
     1 = respondió la pregunta off-topic como si fuera del curso.

Responde EXACTAMENTE en JSON con esta estructura:
{
  "exactitud": <int 1-5>,
  "fluidez": <int 1-5>,
  "alucinacion": <int 1-5>,
  "pedagogia": <int 1-5>,
  "razon_breve": "<max 25 palabras explicando la nota más baja>"
}

No añadas texto fuera del JSON."""


def call_judge(prompt: str, response: str) -> dict | None:
    """Invoca al juez y extrae calificaciones."""
    user_msg = (
        f"PROMPT ORIGINAL DEL ESTUDIANTE:\n{prompt}\n\n"
        f"RESPUESTA DEL MODELO A EVALUAR:\n{response}\n\n"
        "Califica esta respuesta en JSON."
    )
    payload = {
        "model": JUDGE_MODEL,
        "system": RUBRIC_PROMPT,
        "prompt": user_msg,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": JUDGE_TEMPERATURE,
            "num_ctx": 4096,
            "num_predict": 400,
        },
        "keep_alive": "10m",
    }
    try:
        r = httpx.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=JUDGE_TIMEOUT_S,
        )
        r.raise_for_status()
        raw = r.json().get("response", "").strip()
        # Cleanup posible markdown fence
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        data = json.loads(raw)
        # Coerción robusta
        scores = {}
        for k in ("exactitud", "fluidez", "alucinacion", "pedagogia"):
            v = data.get(k)
            if isinstance(v, (int, float)):
                scores[k] = int(max(1, min(5, v)))
            else:
                return None
        scores["razon_breve"] = str(data.get("razon_breve", ""))[:200]
        return scores
    except (httpx.HTTPError, json.JSONDecodeError, ValueError) as e:
        print(f"  ⚠ juez falló: {type(e).__name__}: {e}")
        return None


def main():
    here = Path(__file__).parent
    bench_path = here / "results" / "llm_benchmark.json"
    out_path = here / "results" / "llm_scores.json"

    if not bench_path.exists():
        raise SystemExit(f"✗ Falta {bench_path}. Corre primero run_llm_benchmark.py")

    bench = json.loads(bench_path.read_text(encoding="utf-8"))

    # Reanudar si ya existe
    existing = {}
    if out_path.exists():
        existing_data = json.loads(out_path.read_text(encoding="utf-8"))
        for model_key, model_data in existing_data.get("models", {}).items():
            existing[model_key] = {
                r["prompt_id"]: r for r in model_data.get("scores", [])
            }

    all_scores = {
        "config": {
            "judge_model": JUDGE_MODEL,
            "judge_temperature": JUDGE_TEMPERATURE,
            "rubric_prompt_hash": str(abs(hash(RUBRIC_PROMPT)) % 10**10),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "notes": (
                "Evaluación automatizada vía LLM juez (qwen2.5:7b) con rúbrica "
                "pre-registrada Likert 1-5 sobre 4 criterios. Mismo juez para "
                "los 3 modelos evaluados. Limitación reconocida: el juez es uno "
                "de los modelos evaluados → autosesgo potencial, trabajo futuro "
                "usar juez externo de mayor capacidad."
            ),
        },
        "models": {},
    }

    total_start = time.perf_counter()

    for model_name, model_bench in bench.get("models", {}).items():
        print(f"\n{'─' * 72}\n▶ Calificando: {model_name}\n{'─' * 72}")
        results = model_bench.get("results", [])
        valid = [r for r in results if "response" in r and r.get("response")]
        already = existing.get(model_name, {})

        scored = []
        for i, r in enumerate(valid, 1):
            pid = r["prompt_id"]
            if pid in already:
                scored.append(already[pid])
                print(f"  [{i:>2}/{len(valid)}] {pid:<10}  (cached)")
                continue

            t0 = time.perf_counter()
            verdict = call_judge(r["prompt"], r["response"])
            dt = time.perf_counter() - t0

            if not verdict:
                scored.append({
                    "prompt_id": pid,
                    "module": r["module"],
                    "type": r["type"],
                    "error": "judge_failed",
                    "elapsed_s": round(dt, 2),
                })
                print(f"  [{i:>2}/{len(valid)}] {pid:<10}  ✗ judge falló ({dt:.1f}s)")
                continue

            entry = {
                "prompt_id": pid,
                "module": r["module"],
                "type": r["type"],
                "elapsed_s": round(dt, 2),
                **verdict,
            }
            entry["promedio"] = round(
                statistics.mean([entry["exactitud"], entry["fluidez"],
                                 entry["alucinacion"], entry["pedagogia"]]), 2
            )
            scored.append(entry)
            print(f"  [{i:>2}/{len(valid)}] {pid:<10}  "
                  f"E={entry['exactitud']} F={entry['fluidez']} "
                  f"A={entry['alucinacion']} P={entry['pedagogia']}  "
                  f"avg={entry['promedio']}  ({dt:.1f}s)")

            # Guardado incremental
            all_scores["models"][model_name] = {"scores": scored}
            out_path.write_text(
                json.dumps(all_scores, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        # Agregados por modelo
        valid_scored = [s for s in scored if "promedio" in s]
        by_criterion = {}
        for crit in ("exactitud", "fluidez", "alucinacion", "pedagogia"):
            vals = [s[crit] for s in valid_scored if crit in s]
            by_criterion[crit] = round(statistics.mean(vals), 3) if vals else 0

        by_type = {}
        for t in ("conceptual", "code", "application", "off_topic"):
            subset = [s for s in valid_scored if s.get("type") == t]
            by_type[t] = {
                "n": len(subset),
                "promedio": round(statistics.mean([s["promedio"] for s in subset]), 3) if subset else 0,
            }

        all_scores["models"][model_name] = {
            "n_scored": len(valid_scored),
            "n_failed": len(scored) - len(valid_scored),
            "overall_average": round(
                statistics.mean([s["promedio"] for s in valid_scored]), 3
            ) if valid_scored else 0,
            "by_criterion": by_criterion,
            "by_type": by_type,
            "scores": scored,
        }
        out_path.write_text(
            json.dumps(all_scores, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    total_elapsed = time.perf_counter() - total_start
    print(f"\n{'═' * 72}\n✅ Scoring automático completo en {total_elapsed/60:.1f} min")
    print(f"{'═' * 72}\n\n📊 Resumen:\n")
    print(f"{'Modelo':<42}{'N':>5}{'Exact':>9}{'Flu':>7}{'Alu':>7}{'Ped':>7}{'Prom':>8}")
    print("─" * 85)
    for model, r in all_scores["models"].items():
        bc = r.get("by_criterion", {})
        print(
            f"{model:<42}{r.get('n_scored', 0):>5}"
            f"{bc.get('exactitud', 0):>9.2f}"
            f"{bc.get('fluidez', 0):>7.2f}"
            f"{bc.get('alucinacion', 0):>7.2f}"
            f"{bc.get('pedagogia', 0):>7.2f}"
            f"{r.get('overall_average', 0):>8.2f}"
        )


if __name__ == "__main__":
    main()
