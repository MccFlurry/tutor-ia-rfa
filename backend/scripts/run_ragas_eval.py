"""
run_ragas_eval.py — Evaluación RAGAS-style del pipeline RAG.

Implementa las 6 métricas estándar RAGAS con Ollama local (más robusto
que la librería `ragas` con LLMs no-OpenAI):

- faithfulness              — proporción de claims del answer soportadas por el contexto
- answer_relevancy          — similitud semántica entre pregunta original y pregunta
                              inferida por el LLM a partir del answer
- context_precision         — proporción de chunks recuperados marcados relevantes
- context_recall            — proporción de sentencias de ground_truth cubiertas por el contexto
- context_entities_recall   — fracción de entidades del ground_truth presentes en el contexto
- answer_correctness        — F1 factual ponderado + similitud semántica con ground_truth

Ejecutar:
    docker compose exec backend python scripts/run_ragas_eval.py [--max N] [--iter LABEL]

Output:
    scripts/ragas_runs/<timestamp>_<LABEL>.csv        → per-row
    scripts/ragas_runs/<timestamp>_<LABEL>.summary.json → promedios
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from langchain_ollama import OllamaEmbeddings

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import settings
from app.database import AsyncSessionLocal as async_session_maker, engine
from app.services.rag_service import query_rag, _semantic_search
from app.services.embed_service import embed_query
import redis.asyncio as aioredis
import logging

from scripts.ragas_metrics import (
    make_judge,
    make_judge_b,
    make_generator,
    metric_faithfulness,
    metric_answer_relevancy,
    metric_context_precision,
    metric_context_recall,
    metric_context_entities_recall,
    metric_answer_correctness,
    extract_claims,
    verify_claims,
    cohen_kappa,
)

# Silenciar eco SQL + loguru verbose
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
engine.echo = False


GOLDEN_PATH = BASE_DIR / "tests" / "fixtures" / "golden_set.json"
OUT_DIR = BASE_DIR / "scripts" / "ragas_runs"
OUT_DIR.mkdir(exist_ok=True)

# ----------------------------------------------------------------------------
# Pipeline por pregunta
# ----------------------------------------------------------------------------
async def run_rag(question: str) -> tuple[str, list[str]]:
    """Ejecuta el pipeline RAG y devuelve (answer, contexts)."""
    redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    # Invalidar caché para evitar respuestas viejas
    h = hashlib.sha256(question.strip().lower().encode()).hexdigest()[:16]
    await redis_client.delete(f"rag:{h}")

    async with async_session_maker() as db:
        query_vec = await embed_query(question)
        chunks = await _semantic_search(query_vec, db)
        contexts = [c["content"] for c in chunks]
        result = await query_rag(
            question=question,
            session_history=[],
            db=db,
            redis_client=redis_client,
        )
    await redis_client.aclose()
    return result["content"], contexts


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
async def main(max_q: int | None, label: str):
    with open(GOLDEN_PATH, encoding="utf-8") as f:
        golden = json.load(f)

    questions = golden["questions"]
    if max_q:
        questions = questions[:max_q]

    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    out_csv = OUT_DIR / f"{stamp}_{label}.csv"
    out_json = OUT_DIR / f"{stamp}_{label}.summary.json"

    judge = make_judge()
    judge_b = make_judge_b()
    kappa_a: list[bool] = []
    kappa_b: list[bool] = []
    gen = make_generator()
    embedder = OllamaEmbeddings(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_EMBED_MODEL,
    )

    results = []

    print(f"\n{'='*70}")
    print(f"RAGAS Evaluation · label={label} · {len(questions)} preguntas")
    print(f"config: chunk={settings.CHUNK_SIZE}/{settings.CHUNK_OVERLAP} · "
          f"threshold={settings.RAG_SIMILARITY_THRESHOLD} · top_k={settings.RAG_TOP_K}")
    print(f"output: {out_csv.name}")
    print(f"{'='*70}\n")

    # CSV writer
    fieldnames = [
        "id", "module", "type", "difficulty",
        "question", "answer", "n_contexts",
        "faithfulness", "answer_relevancy", "context_precision", "context_recall",
        "context_entities_recall", "answer_correctness",
        "elapsed_s", "error",
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for q in questions:
            qid = q["id"]
            t0 = time.time()
            row = {
                "id": qid,
                "module": q["module"],
                "type": q["type"],
                "difficulty": q["difficulty"],
                "question": q["question"][:300],
                "answer": "",
                "n_contexts": 0,
                "faithfulness": None,
                "answer_relevancy": None,
                "context_precision": None,
                "context_recall": None,
                "context_entities_recall": None,
                "answer_correctness": None,
                "elapsed_s": 0,
                "error": "",
            }
            try:
                answer, contexts = await run_rag(q["question"])
                row["answer"] = answer[:500]
                row["n_contexts"] = len(contexts)

                if contexts:
                    row["faithfulness"] = await metric_faithfulness(judge, answer, contexts)
                    row["context_precision"] = await metric_context_precision(
                        judge, q["question"], q["ground_truth"], contexts
                    )
                    row["context_recall"] = await metric_context_recall(
                        judge, q["ground_truth"], contexts
                    )
                    row["context_entities_recall"] = await metric_context_entities_recall(
                        judge, q["ground_truth"], contexts
                    )
                    if judge_b is not None:
                        claims = await extract_claims(judge, answer)
                        if claims:
                            la = await verify_claims(judge, claims, contexts)
                            lb = await verify_claims(judge_b, claims, contexts)
                            if la and lb and len(la) == len(lb):
                                kappa_a.extend(la)
                                kappa_b.extend(lb)
                    row["answer_relevancy"] = await metric_answer_relevancy(
                        gen, embedder, q["question"], answer
                    )
                    row["answer_correctness"] = await metric_answer_correctness(
                        judge, embedder, answer, q["ground_truth"]
                    )
            except Exception as e:
                row["error"] = str(e)[:200]
                print(f"  [err] Q{qid}: {e}")

            row["elapsed_s"] = round(time.time() - t0, 1)
            results.append(row)
            writer.writerow(row)
            f.flush()

            metrics_str = " ".join(
                f"{k[0]}={row[k]:.2f}" if isinstance(row[k], float) else f"{k[0]}=--"
                for k in ("faithfulness", "answer_relevancy", "context_precision",
                          "context_recall", "context_entities_recall", "answer_correctness")
            )
            print(f"Q{qid:02d} [{q['module']}/{q['type']:12s}/{q['difficulty']:6s}] "
                  f"{row['elapsed_s']:5.1f}s  {metrics_str}  ·  {q['question'][:50]}")

    # Summary
    def avg(key):
        vals = [r[key] for r in results if isinstance(r[key], (int, float))]
        return round(sum(vals) / len(vals), 3) if vals else None

    OFFICIAL = {
        "faithfulness": 0.80,
        "answer_relevancy": 0.75,
        "context_precision": 0.70,
        "context_recall": 0.75,
        "context_entities_recall": 0.70,
        "answer_correctness": 0.70,
    }

    def none_rate(key):
        total = len(results)
        nones = sum(1 for r in results if r[key] is None)
        return round(nones / total, 3) if total else None

    kappa = cohen_kappa(kappa_a, kappa_b) if kappa_a else None

    summary = {
        "label": label,
        "timestamp": stamp,
        "n_questions": len(questions),
        "config": {
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP,
            "threshold": settings.RAG_SIMILARITY_THRESHOLD,
            "top_k": settings.RAG_TOP_K,
            "llm": settings.OLLAMA_MODEL,
            "judge": settings.RAGAS_JUDGE_MODEL or settings.OLLAMA_MODEL,
            "judge_b": settings.RAGAS_JUDGE_MODEL_B or None,
            "embed": settings.OLLAMA_EMBED_MODEL,
        },
        "global": {k: avg(k) for k in OFFICIAL},
        "none_rate": {k: none_rate(k) for k in OFFICIAL},
        "thresholds": OFFICIAL,
        "kappa_faithfulness_verdicts": kappa,
        "pass": {k: (avg(k) or 0) >= OFFICIAL[k] for k in OFFICIAL},
    }

    # Breakdown por módulo / tipo / dificultad
    for dim in ("module", "type", "difficulty"):
        breakdown = {}
        buckets = {r[dim] for r in results}
        for b in sorted(buckets):
            subset = [r for r in results if r[dim] == b]
            def bavg(k):
                vs = [r[k] for r in subset if isinstance(r[k], (int, float))]
                return round(sum(vs) / len(vs), 3) if vs else None
            breakdown[b] = {
                "n": len(subset),
                "faithfulness": bavg("faithfulness"),
                "answer_relevancy": bavg("answer_relevancy"),
                "context_precision": bavg("context_precision"),
                "context_recall": bavg("context_recall"),
                "context_entities_recall": bavg("context_entities_recall"),
                "answer_correctness": bavg("answer_correctness"),
            }
        summary[f"by_{dim}"] = breakdown

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print("RESUMEN")
    print(f"{'='*70}")
    print(json.dumps(summary["global"], indent=2))
    for k in OFFICIAL:
        ok = "✓" if summary["pass"][k] else "✗"
        print(f"{k} ≥ {OFFICIAL[k]:.2f}  ·  {ok}  (valor={summary['global'][k]}, none_rate={summary['none_rate'][k]})")
    if kappa is not None:
        print(f"Cohen's κ (faithfulness verdicts, juez A vs B): {kappa}")
    print(f"\nCSV:     {out_csv}")
    print(f"Summary: {out_json}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=None, help="Limitar número de preguntas")
    parser.add_argument("--iter", dest="label", type=str, default="baseline", help="Etiqueta iteración")
    args = parser.parse_args()
    asyncio.run(main(args.max, args.label))
