#!/usr/bin/env python3
"""
score_responses.py — Calificación interactiva de las respuestas del benchmark.

Aplica una rúbrica Likert 1–5 sobre 4 criterios a cada respuesta:
  1. Exactitud técnica
  2. Fluidez en español
  3. Ausencia de alucinaciones
  4. Pertinencia pedagógica

La rúbrica y el protocolo mono-evaluador quedan documentados en el reporte
con transparencia metodológica (no se oculta que es un único evaluador).

Uso:
    python score_responses.py

Produce: results/llm_scores.json

Tips:
- Puedes salir con 'q' en cualquier momento; guarda progreso automáticamente.
- Puedes ejecutarlo varias veces; retoma donde dejaste.
- Para los prompts off-topic (M1/M2/M3 = OFF), evalúa si el modelo rechazó
  correctamente el tema fuera de contexto (pertinencia pedagógica).
"""

import json
import sys
from pathlib import Path
from statistics import mean

RUBRIC = [
    ("exactitud",
     "Exactitud técnica",
     "¿Es técnicamente correcta respecto a Android/Kotlin y al sílabo? "
     "(1=muchos errores técnicos · 3=mayormente correcta · 5=impecable)"),
    ("fluidez",
     "Fluidez en español",
     "Gramática, vocabulario natural, no traduce literalmente del inglés. "
     "(1=español muy defectuoso · 3=aceptable · 5=natural y académico)"),
    ("alucinacion",
     "Ausencia de alucinaciones",
     "¿Inventa APIs, clases o conceptos que no existen? "
     "(1=mucho inventado · 3=algunas imprecisiones · 5=cero inventos)"),
    ("pedagogia",
     "Pertinencia pedagógica",
     "Tono didáctico, nivel apropiado para estudiante de IESTP. "
     "Para off-topic: ¿rechaza correctamente? "
     "(1=confuso o inapropiado · 3=aceptable · 5=ejemplar)"),
]


def prompt_int(question: str) -> int | None:
    while True:
        raw = input(f"     {question}\n     → ").strip().lower()
        if raw in ("q", "quit", "salir"):
            return None
        try:
            val = int(raw)
            if 1 <= val <= 5:
                return val
        except ValueError:
            pass
        print("     ❌ entrada inválida. Escribe un entero entre 1 y 5 (o 'q' para salir y guardar).")


def score_one(idx: int, total: int, entry: dict) -> dict | None:
    if "error" in entry:
        print(f"\n[{idx}/{total}] {entry['prompt_id']} — ERROR durante generación, saltando")
        return {"skipped": True, "reason": "generation_error"}

    print("\n" + "═" * 76)
    print(f"[{idx}/{total}] {entry['prompt_id']} · {entry['module']} · tipo: {entry['type']}")
    print(f"Latencia: {entry['latency_s']:.2f}s · Tokens: {entry.get('tokens_generated', 0)}")
    print("─" * 76)
    print(f"PROMPT:\n{entry['prompt']}")
    print("─" * 76)
    print(f"RESPUESTA DEL MODELO:\n{entry['response']}")
    print("═" * 76)

    scores = {}
    for key, short, long_desc in RUBRIC:
        print(f"\n  📊 {short}")
        val = prompt_int(long_desc)
        if val is None:
            return None  # user quit
        scores[key] = val

    scores["promedio"] = round(mean(scores.values()), 2)
    return scores


def main():
    here = Path(__file__).parent
    bench_path = here / "results" / "llm_benchmark.json"
    scores_path = here / "results" / "llm_scores.json"

    if not bench_path.exists():
        sys.exit(f"❌ No se encontró {bench_path}. Ejecuta primero run_llm_benchmark.py")

    bench = json.loads(bench_path.read_text(encoding="utf-8"))
    existing = {}
    if scores_path.exists():
        existing = json.loads(scores_path.read_text(encoding="utf-8"))
        print(f"↻ Reanudando desde {scores_path}")

    models_data = bench.get("models", bench)  # tolera estructura antigua

    for model, data in models_data.items():
        print(f"\n\n{'█' * 76}\n█ Modelo: {model}\n{'█' * 76}")
        model_scores = existing.get(model, {})
        entries = data.get("results", [])

        pending = [e for e in entries if str(e["prompt_id"]) not in model_scores]
        print(f"Total: {len(entries)} · Ya calificados: {len(entries) - len(pending)} · Pendientes: {len(pending)}")

        for i, entry in enumerate(entries, 1):
            key = str(entry["prompt_id"])
            if key in model_scores:
                continue
            s = score_one(i, len(entries), entry)
            if s is None:
                existing[model] = model_scores
                scores_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"\n💾 Progreso guardado en {scores_path}. Hasta luego.")
                return
            model_scores[key] = s
            existing[model] = model_scores
            scores_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

        existing[model] = model_scores

    scores_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n\n{'═' * 76}\n✅ TODOS los scores guardados en {scores_path}\n{'═' * 76}")

    print("\n📊 Promedios por modelo:")
    for model, scores in existing.items():
        vals = [s["promedio"] for s in scores.values() if isinstance(s, dict) and "promedio" in s]
        if not vals:
            continue
        per_criterion = {k: mean([s[k] for s in scores.values() if k in s]) for k in ["exactitud", "fluidez", "alucinacion", "pedagogia"]}
        print(f"  {model}")
        print(f"    promedio global: {mean(vals):.2f} (n={len(vals)})")
        for k, v in per_criterion.items():
            print(f"    {k:>14}: {v:.2f}")


if __name__ == "__main__":
    main()
