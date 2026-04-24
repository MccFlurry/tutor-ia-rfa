"""
compare_ragas_runs.py — Compara dos corridas RAGAS lado a lado.

Uso:
    docker compose exec backend python scripts/compare_ragas_runs.py \\
        --baseline scripts/ragas_runs/20260424_0407_baseline.summary.json \\
        --new      scripts/ragas_runs/<nuevo>.summary.json
"""

import argparse
import json
from pathlib import Path


def compare(baseline_path: Path, new_path: Path):
    b = json.loads(baseline_path.read_text(encoding="utf-8"))
    n = json.loads(new_path.read_text(encoding="utf-8"))

    print(f"\n{'='*70}")
    print(f"COMPARACIÓN RAGAS")
    print(f"{'='*70}")
    print(f"Baseline: {b['label']}  ({b['timestamp']})")
    print(f"Nuevo:    {n['label']}  ({n['timestamp']})\n")

    print("CONFIG delta:")
    for k in ("chunk_size", "chunk_overlap", "threshold", "top_k"):
        bv = b["config"].get(k)
        nv = n["config"].get(k)
        marker = "" if bv == nv else "  ← cambió"
        print(f"  {k:18} {bv} → {nv}{marker}")

    print("\nMÉTRICAS GLOBALES:")
    print(f"  {'métrica':20} {'baseline':>10} {'nuevo':>10} {'Δ':>8}")
    print("  " + "-" * 50)
    for k in ("faithfulness", "answer_relevancy", "context_precision", "context_recall"):
        bv = b["global"].get(k) or 0
        nv = n["global"].get(k) or 0
        d = nv - bv
        arrow = "↑" if d > 0 else ("↓" if d < 0 else "=")
        print(f"  {k:20} {bv:>10.3f} {nv:>10.3f} {d:>+8.3f} {arrow}")

    print("\nUMBRALES:")
    th = n.get("thresholds", {})
    for metric, target in th.items():
        key = metric.replace("_required", "")
        bv = b["global"].get(key) or 0
        nv = n["global"].get(key) or 0
        b_pass = "✓" if bv >= target else "✗"
        n_pass = "✓" if nv >= target else "✗"
        print(f"  {key:20} umbral ≥{target}   baseline={bv:.3f} {b_pass}   nuevo={nv:.3f} {n_pass}")

    print("\nBREAKDOWN POR TIPO (faithfulness):")
    print(f"  {'tipo':15} {'baseline':>10} {'nuevo':>10} {'Δ':>8}")
    for t in sorted(set(list(b.get("by_type", {}).keys()) + list(n.get("by_type", {}).keys()))):
        bv = (b.get("by_type", {}).get(t) or {}).get("faithfulness") or 0
        nv = (n.get("by_type", {}).get(t) or {}).get("faithfulness") or 0
        print(f"  {t:15} {bv:>10.3f} {nv:>10.3f} {nv-bv:>+8.3f}")

    print("\nBREAKDOWN POR DIFICULTAD (faithfulness):")
    for d in sorted(set(list(b.get("by_difficulty", {}).keys()) + list(n.get("by_difficulty", {}).keys()))):
        bv = (b.get("by_difficulty", {}).get(d) or {}).get("faithfulness") or 0
        nv = (n.get("by_difficulty", {}).get(d) or {}).get("faithfulness") or 0
        print(f"  {d:15} {bv:>10.3f} {nv:>10.3f} {nv-bv:>+8.3f}")

    print(f"\n{'='*70}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--new", required=True)
    args = parser.parse_args()
    compare(Path(args.baseline), Path(args.new))
