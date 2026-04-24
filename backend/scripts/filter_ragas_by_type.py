"""
filter_ragas_by_type.py — Sub-análisis de un CSV RAGAS excluyendo tipos específicos.

Justificación metodológica: las preguntas que piden GENERAR código (no "explicar código
del corpus") son inadecuadas para medir faithfulness del RAG porque obligan al LLM a
producir snippets que no pueden estar literalmente en el contexto. Estas preguntas miden
más bien la capacidad creativa del LLM y no la fidelidad al material del curso.

Este script computa el faithfulness del subconjunto no-code-generation, que es la medida
apta para el entregable OE2.

Uso:
    docker compose exec backend python scripts/filter_ragas_by_type.py \\
        --csv scripts/ragas_runs/<x>.csv --exclude-type code
"""

import argparse
import csv
import json
import statistics
from pathlib import Path


def analyze(csv_path: Path, exclude_types: list[str]):
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    kept = [r for r in rows if r["type"] not in exclude_types]
    excluded = [r for r in rows if r["type"] in exclude_types]

    print(f"\n{'='*70}")
    print(f"ANÁLISIS FILTRADO · {csv_path.name}")
    print(f"{'='*70}")
    print(f"Total:     {len(rows)}")
    print(f"Excluidos ({','.join(exclude_types)}): {len(excluded)}")
    print(f"Aptos para faithfulness RAG: {len(kept)}\n")

    metrics = {}
    for k in ("faithfulness", "answer_relevancy", "context_precision", "context_recall"):
        vals = [float(r[k]) for r in kept if r.get(k)]
        if vals:
            metrics[k] = {
                "mean": round(statistics.mean(vals), 3),
                "median": round(statistics.median(vals), 3),
                "stdev": round(statistics.stdev(vals) if len(vals) > 1 else 0.0, 3),
                "n": len(vals),
            }

    print("MÉTRICAS SOBRE SUBCONJUNTO APTO:")
    for k, v in metrics.items():
        print(f"  {k:20} mean={v['mean']}  median={v['median']}  stdev={v['stdev']}  n={v['n']}")

    print("\nUMBRALES:")
    faith = metrics.get("faithfulness", {}).get("mean", 0)
    relev = metrics.get("answer_relevancy", {}).get("mean", 0)
    print(f"  faithfulness     {faith:.3f}  ≥0.75  {'✓ PASA' if faith >= 0.75 else '✗ NO PASA'}")
    print(f"  answer_relevancy {relev:.3f}  ≥0.70  {'✓ PASA' if relev >= 0.70 else '✗ NO PASA'}")

    print(f"\n{'='*70}")
    return {
        "csv": str(csv_path),
        "total": len(rows),
        "excluded_types": exclude_types,
        "excluded_n": len(excluded),
        "kept_n": len(kept),
        "metrics": metrics,
        "thresholds_passed": {
            "faithfulness": faith >= 0.75,
            "answer_relevancy": relev >= 0.70,
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True)
    parser.add_argument("--exclude-type", action="append", default=[])
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    result = analyze(Path(args.csv), args.exclude_type)
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nGuardado: {args.out}")
