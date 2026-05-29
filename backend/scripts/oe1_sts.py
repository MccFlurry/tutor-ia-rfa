"""oe1_sts.py — Correlación STS (Spearman) del modelo de embeddings seleccionado.

Métrica OE1 faltante: Spearman STS ≥ 0.70. Mide la correlación de rango entre la
similitud coseno de mxbai-embed-large y las puntuaciones humanas de un benchmark STS
en español (stsb_multi_mt, config 'es'; gold 0-5).

Ejecutar:
    docker exec tutor_backend python scripts/oe1_sts.py [--max N] [--split test]

Salida: docs/oe1_sts_results.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr, pearsonr

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import settings
from app.services.embed_service import embed_documents

OUT_JSON = BASE_DIR / "docs" / "oe1_sts_results.json"
THRESHOLD = 0.70


def load_sts(split: str):
    """Carga un benchmark STS en español. Intenta varias fuentes."""
    from datasets import load_dataset
    errors = []
    for kwargs in (
        dict(path="stsb_multi_mt", name="es", split=split, trust_remote_code=True),
        dict(path="stsb_multi_mt", name="es", split=split),
        dict(path="PhilipMay/stsb_multi_mt", name="es", split=split, trust_remote_code=True),
    ):
        try:
            ds = load_dataset(**kwargs)
            return ds, kwargs
        except Exception as e:
            errors.append(f"{kwargs.get('path')}({kwargs.get('name')}): {type(e).__name__}: {str(e)[:120]}")
    raise RuntimeError("No se pudo cargar STS-es. Intentos:\n" + "\n".join(errors))


async def embed_all(texts: list[str], batch: int = 64) -> np.ndarray:
    vecs: list[list[float]] = []
    for i in range(0, len(texts), batch):
        chunk = texts[i:i + batch]
        vecs.extend(await embed_documents(chunk))
        print(f"  embed {min(i + batch, len(texts))}/{len(texts)}")
    arr = np.array(vecs, dtype=np.float64)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return arr / norms


async def main(max_n: int | None, split: str):
    print(f"OE1 STS · embed={settings.OLLAMA_EMBED_MODEL} · split={split}")
    ds, used = load_sts(split)
    s1 = [r["sentence1"] for r in ds]
    s2 = [r["sentence2"] for r in ds]
    gold = [float(r["similarity_score"]) for r in ds]
    if max_n:
        s1, s2, gold = s1[:max_n], s2[:max_n], gold[:max_n]
    print(f"  cargado: {len(s1)} pares ({used.get('path')}/{used.get('name')})")

    a = await embed_all(s1)
    b = await embed_all(s2)
    cos = np.sum(a * b, axis=1)  # ya normalizados

    rho = float(spearmanr(cos, gold).correlation)
    r = float(pearsonr(cos, gold)[0])

    results = {
        "embed_model": settings.OLLAMA_EMBED_MODEL,
        "dataset": f"{used.get('path')} ({used.get('name')}, split={split})",
        "n_pairs": len(gold),
        "spearman": round(rho, 4),
        "pearson": round(r, 4),
        "threshold": THRESHOLD,
        "pass": rho >= THRESHOLD,
    }
    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n=== OE1 STS ===\nSpearman={rho:.4f} (umbral {THRESHOLD}) · Pearson={r:.4f} · n={len(gold)}")
    print(f"Guardado: {OUT_JSON}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--max", type=int, default=None)
    p.add_argument("--split", type=str, default="test")
    a = p.parse_args()
    asyncio.run(main(a.max, a.split))
