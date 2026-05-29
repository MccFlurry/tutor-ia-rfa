"""oe1_retrieval.py — Métricas de recuperación OE1 sobre el golden set.

Mide las métricas de embeddings que faltaban / estaban bajo umbral en el reporte-LLM,
con el pipeline de PRODUCCIÓN (mxbai-embed-large + cross-encoder rerank):

  - Recall@5   ≥ 0.70   (hit-rate@5: ≥1 chunk relevante en top-5)
  - MRR@10     ≥ 0.65
  - nDCG@10    ≥ 0.55

Compara dos condiciones: SIN rerank (orden coseno) vs CON rerank (cross-encoder).
Relevancia binaria: un chunk es relevante si contiene ≥2 de los expected_context_keywords
(substring, case-insensitive) — misma definición que el reporte-LLM original, extendida a top-10.

Nota: el índice pgvector está embebido con mxbai (1024-dim); nomic-embed-text (768-dim) no es
comparable sin re-indexar el corpus, y ya quedó descartado en el reporte original (Recall@5 0.35).

Ejecutar:
    docker exec tutor_backend python scripts/oe1_retrieval.py [--max N] [--pool 30]

Salida: docs/oe1_retrieval_results.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import text

from app.config import settings
from app.database import AsyncSessionLocal as async_session_maker, engine
from app.services.embed_service import embed_query
from app.services.rerank_service import rerank

import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
engine.echo = False

GOLDEN = BASE_DIR / "tests" / "fixtures" / "golden_set.json"
OUT_JSON = BASE_DIR / "docs" / "oe1_retrieval_results.json"
THRESHOLDS = {"recall@5": 0.70, "mrr@10": 0.65, "ndcg@10": 0.55}


def is_relevant(content: str, keywords: list[str]) -> bool:
    c = content.lower()
    hits = sum(1 for kw in keywords if kw.lower() in c)
    return hits >= min(2, len(keywords))


def dcg(rels: list[int]) -> float:
    return sum(r / math.log2(i + 2) for i, r in enumerate(rels))


def ndcg_at_k(rels: list[int], k: int) -> float:
    actual = dcg(rels[:k])
    ideal = dcg(sorted(rels, reverse=True)[:k])
    return actual / ideal if ideal > 0 else 0.0


def mrr_at_k(rels: list[int], k: int) -> float:
    for i, r in enumerate(rels[:k]):
        if r:
            return 1.0 / (i + 1)
    return 0.0


async def fetch_pool(db, qvec: list[float], pool_k: int) -> list[dict]:
    """Top pool_k candidatos por coseno (umbral laxo), pre-ordenados por similitud desc."""
    vec_literal = "[" + ",".join(str(v) for v in qvec) + "]"
    sql = text(f"""
        SELECT content, 1 - (embedding <=> '{vec_literal}'::vector) AS similarity
        FROM document_chunks
        WHERE 1 - (embedding <=> '{vec_literal}'::vector) >= :threshold
        ORDER BY embedding <=> '{vec_literal}'::vector
        LIMIT :pool_k
    """)
    rows = (await db.execute(sql, {"threshold": settings.RAG_FETCH_THRESHOLD, "pool_k": pool_k})).fetchall()
    return [{"content": r.content, "similarity": float(r.similarity)} for r in rows]


async def main(max_q: int | None, pool_k: int):
    golden = json.load(open(GOLDEN, encoding="utf-8"))["questions"]
    if max_q:
        golden = golden[:max_q]

    conditions = ("cosine_only", "rerank")
    acc = {cond: {"recall@5": [], "mrr@10": [], "ndcg@10": []} for cond in conditions}
    by_module = {cond: {} for cond in conditions}

    print(f"OE1 recuperación · {len(golden)} queries · pool={pool_k} · embed={settings.OLLAMA_EMBED_MODEL}")

    async with async_session_maker() as db:
        for q in golden:
            kws = q["expected_context_keywords"]
            qvec = await embed_query(q["question"])
            pool = await fetch_pool(db, qvec, pool_k)
            if not pool:
                print(f"  Q{q['id']:02d} pool vacío")
                continue

            ranked = {
                "cosine_only": pool[:10],
                "rerank": rerank(q["question"], pool, top_k=10),
            }
            for cond in conditions:
                rels = [1 if is_relevant(c["content"], kws) else 0 for c in ranked[cond]]
                r5 = 1.0 if any(rels[:5]) else 0.0
                mrr = mrr_at_k(rels, 10)
                ndcg = ndcg_at_k(rels, 10)
                acc[cond]["recall@5"].append(r5)
                acc[cond]["mrr@10"].append(mrr)
                acc[cond]["ndcg@10"].append(ndcg)
                bm = by_module[cond].setdefault(q["module"], {"recall@5": [], "mrr@10": [], "ndcg@10": []})
                bm["recall@5"].append(r5); bm["mrr@10"].append(mrr); bm["ndcg@10"].append(ndcg)
            print(f"  Q{q['id']:02d} [{q['module']}] cos:r5={acc['cosine_only']['recall@5'][-1]:.0f} "
                  f"ndcg={acc['cosine_only']['ndcg@10'][-1]:.2f} | "
                  f"rr:r5={acc['rerank']['recall@5'][-1]:.0f} ndcg={acc['rerank']['ndcg@10'][-1]:.2f}")

    def mean(xs):
        return round(sum(xs) / len(xs), 4) if xs else None

    results = {"thresholds": THRESHOLDS, "embed_model": settings.OLLAMA_EMBED_MODEL,
               "pool_k": pool_k, "n_queries": len(golden),
               "relevance_def": "≥2 expected_context_keywords (substring, case-insensitive)",
               "conditions": {}}
    for cond in conditions:
        results["conditions"][cond] = {
            "recall@5": mean(acc[cond]["recall@5"]),
            "mrr@10": mean(acc[cond]["mrr@10"]),
            "ndcg@10": mean(acc[cond]["ndcg@10"]),
            "by_module": {mod: {k: mean(v) for k, v in d.items()} for mod, d in by_module[cond].items()},
        }

    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== OE1 RECUPERACIÓN ===")
    for cond in conditions:
        c = results["conditions"][cond]
        print(f"{cond:12s}: Recall@5={c['recall@5']} MRR@10={c['mrr@10']} nDCG@10={c['ndcg@10']}")
    print(f"Guardado: {OUT_JSON}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--max", type=int, default=None)
    p.add_argument("--pool", type=int, default=settings.RAG_FETCH_K)
    a = p.parse_args()
    asyncio.run(main(a.max, a.pool))
