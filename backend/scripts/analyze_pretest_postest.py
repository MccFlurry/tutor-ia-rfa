"""OE4 — Analisis pretest/postest grupo piloto IESTP RFA.

Diseno pre-experimental: prueba t de Student para muestras relacionadas
(pareada, una cola: postest > pretest) con p < 0.05 + tamano del efecto.
Replica la metodologia de notebooks/pretest_postest_analysis.ipynb.

Escala vigesimal (0-20). Ejecutar desde backend/: python scripts/analyze_pretest_postest.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

CSV = Path(__file__).resolve().parents[2] / "docs" / "datos-pretest-postest.csv"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    df = pd.read_csv(CSV).dropna()
    pre = df["pretest"].to_numpy(dtype=float)
    post = df["postest"].to_numpy(dtype=float)
    diff = post - pre
    n = len(df)

    # --- Descriptivos ---
    print("=" * 60)
    print(f"OE4 — Pretest/Postest · n = {n} (escala 0-20)")
    print("=" * 60)
    print(f"Pretest : media {pre.mean():.2f} ± {pre.std(ddof=1):.2f}  "
          f"[min {pre.min():.0f}, max {pre.max():.0f}]")
    print(f"Postest : media {post.mean():.2f} ± {post.std(ddof=1):.2f}  "
          f"[min {post.min():.0f}, max {post.max():.0f}]")
    print(f"Ganancia: media {diff.mean():.2f} ± {diff.std(ddof=1):.2f}")

    improved = int((diff > 0).sum())
    flat = int((diff == 0).sum())
    declined = int((diff < 0).sum())
    print(f"Mejoraron {improved}/{n} ({improved/n*100:.0f}%) · "
          f"sin cambio {flat} · bajaron {declined}")

    # --- Supuesto: normalidad de las diferencias (Shapiro-Wilk) ---
    w, p_norm = stats.shapiro(diff)
    normal = p_norm > 0.05
    print("-" * 60)
    print(f"Shapiro-Wilk diferencias: W = {w:.4f}, p = {p_norm:.4f} "
          f"→ {'normal' if normal else 'NO normal'} (alpha 0.05)")

    # --- Prueba principal: t pareada, una cola (post > pre) ---
    t, p = stats.ttest_rel(post, pre, alternative="greater")
    dfree = n - 1
    print("-" * 60)
    print(f"t de Student pareada (una cola, H1: postest > pretest)")
    print(f"  t({dfree}) = {t:.4f}   p = {p:.3e}")
    print(f"  Decision: {'SIGNIFICATIVO (p < 0.05) ✓' if p < 0.05 else 'NO significativo'}")

    # --- Tamano del efecto: Cohen's d (pareado) + IC 95% de la diferencia ---
    d = diff.mean() / diff.std(ddof=1)
    sem = diff.std(ddof=1) / np.sqrt(n)
    tcrit = stats.t.ppf(0.975, dfree)
    ci_low, ci_high = diff.mean() - tcrit * sem, diff.mean() + tcrit * sem
    if abs(d) < 0.5:
        mag = "pequeno"
    elif abs(d) < 0.8:
        mag = "mediano"
    else:
        mag = "grande"
    print("-" * 60)
    print(f"Cohen's d (pareado) = {d:.3f}  → efecto {mag}")
    print(f"IC 95% de la ganancia media: [{ci_low:.2f}, {ci_high:.2f}]")

    # --- Robustez: Wilcoxon signed-rank (no parametrico) ---
    wstat, wp = stats.wilcoxon(post, pre, alternative="greater")
    print("-" * 60)
    print(f"Wilcoxon signed-rank (robustez): W = {wstat:.1f}, p = {wp:.3e}")

    # --- Veredicto OE4 ---
    print("=" * 60)
    test_p = p if normal else wp
    test_name = "t pareada" if normal else "Wilcoxon (diferencias no normales)"
    ok = test_p < 0.05
    print(f"OE4 → prueba aplicable: {test_name}")
    print(f"OE4 → {'VALIDADO: mejora estadisticamente significativa (p < 0.05)' if ok else 'NO validado'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
