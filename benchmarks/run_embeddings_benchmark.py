#!/usr/bin/env python3
"""
run_embeddings_benchmark.py — Compara mxbai-embed-large vs nomic-embed-text
en la tarea de recuperación de chunks relevantes del corpus del curso.

Métricas:
  - Recall@5: proporción de queries donde al menos un chunk relevante
    (definido por expected_keywords) aparece en el top-5 por similitud coseno.
  - MRR (Mean Reciprocal Rank): 1 / rango del primer chunk relevante.
  - Dimensionalidad, latencia de embedding por query.

Un chunk se considera "relevante" si contiene al menos N palabras clave
esperadas (substring match, case-insensitive). N se define en golden_set_embeddings.json.

Uso:
    # 1. exporta primero el corpus:  python export_corpus.py
    # 2. asegúrate de tener los modelos:
    #    ollama pull mxbai-embed-large
    #    ollama pull nomic-embed-text
    # 3. ejecuta:
    python run_embeddings_benchmark.py

Produce: results/embeddings_benchmark.json
"""

import json
import math
import statistics
import time
from pathlib import Path

import os
import httpx

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
EMBEDDING_MODELS = ["mxbai-embed-large", "nomic-embed-text"]


def embed(model: str, text: str) -> list[float]:
    r = httpx.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": model, "prompt": text},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["embedding"]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def is_relevant(chunk_text: str, keywords: list[str], min_match: int) -> bool:
    lower = chunk_text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in lower)
    return hits >= min_match


def evaluate_model(
    model: str,
    queries: list[dict],
    corpus: list[dict],
    k: int,
    min_match: int,
) -> dict:
    print(f"\n{'─' * 72}\n▶ {model}\n{'─' * 72}")

    # 1. Embedding del corpus (la parte costosa)
    print(f"  ⏳ Embeddings del corpus ({len(corpus)} chunks)...")
    t0 = time.perf_counter()
    chunk_vectors = []
    for i, c in enumerate(corpus, 1):
        vec = embed(model, c["text"])
        chunk_vectors.append(vec)
        if i % 25 == 0 or i == len(corpus):
            print(f"     {i}/{len(corpus)}")
    corpus_embed_time = time.perf_counter() - t0
    dim = len(chunk_vectors[0]) if chunk_vectors else 0
    print(f"  ✓ corpus embebido en {corpus_embed_time:.1f}s · dim={dim}")

    # 2. Evaluación por query
    recalls = []
    reciprocal_ranks = []
    query_latencies = []
    per_query = []

    for q in queries:
        t0 = time.perf_counter()
        qv = embed(model, q["query"])
        query_latencies.append(time.perf_counter() - t0)

        sims = [(i, cosine(qv, cv)) for i, cv in enumerate(chunk_vectors)]
        sims.sort(key=lambda x: x[1], reverse=True)

        # Top-k IDs
        topk = sims[:k]
        topk_relevance = [
            is_relevant(corpus[i]["text"], q["expected_keywords"], min_match)
            for i, _ in topk
        ]
        recall = 1.0 if any(topk_relevance) else 0.0
        recalls.append(recall)

        # MRR: primer rango en que aparece un chunk relevante
        rr = 0.0
        for rank, (i, _) in enumerate(sims, start=1):
            if is_relevant(corpus[i]["text"], q["expected_keywords"], min_match):
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

        per_query.append({
            "query_id": q["id"],
            "query": q["query"],
            "recall_at_k": recall,
            "reciprocal_rank": rr,
            "top_k_similarities": [round(s, 4) for _, s in topk],
            "top_k_relevant_flags": topk_relevance,
        })
        print(f"     {q['id']}: recall={recall:.0f}  rr={rr:.3f}  top1_sim={topk[0][1]:.3f}")

    return {
        "model": model,
        "embedding_dim": dim,
        "n_queries": len(queries),
        "n_corpus_chunks": len(corpus),
        "k": k,
        "min_keywords_match": min_match,
        "recall_at_k": statistics.mean(recalls),
        "mrr": statistics.mean(reciprocal_ranks),
        "query_latency_avg_ms": statistics.mean(query_latencies) * 1000,
        "query_latency_p95_ms": sorted(query_latencies)[int(len(query_latencies) * 0.95) - 1] * 1000 if len(query_latencies) >= 20 else max(query_latencies) * 1000,
        "corpus_embed_time_s": corpus_embed_time,
        "per_query": per_query,
    }


def main():
    here = Path(__file__).parent
    golden_path = here / "golden_set_embeddings.json"
    corpus_path = here / "results" / "corpus_chunks.json"
    out_path = here / "results" / "embeddings_benchmark.json"

    if not golden_path.exists():
        raise FileNotFoundError(f"No se encontró {golden_path}")
    if not corpus_path.exists():
        raise FileNotFoundError(
            f"No se encontró {corpus_path}. Ejecuta primero: python export_corpus.py"
        )

    gs = json.loads(golden_path.read_text(encoding="utf-8"))
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    k = gs.get("k", 5)
    min_match = gs.get("min_keywords_match", 2)
    queries = gs["queries"]

    print(f"📚 {len(queries)} queries · {len(corpus)} chunks del corpus")
    print(f"🎯 k={k}, min_keywords_match={min_match}\n")

    all_results = {
        "config": {
            "k": k,
            "min_keywords_match": min_match,
            "n_queries": len(queries),
            "n_corpus": len(corpus),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "models": {},
    }

    for model in EMBEDDING_MODELS:
        all_results["models"][model] = evaluate_model(model, queries, corpus, k, min_match)
        out_path.write_text(
            json.dumps(all_results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    print(f"\n{'═' * 72}\n✅ Embeddings benchmark completo — {out_path}\n{'═' * 72}")
    print("\n📊 Resumen:")
    print(f"{'Modelo':<28}{'Dim':>8}{'Recall@'+str(k):>12}{'MRR':>10}{'Lat.(ms)':>12}")
    print("─" * 72)
    for model, r in all_results["models"].items():
        print(
            f"{model:<28}{r['embedding_dim']:>8}"
            f"{r['recall_at_k']:>12.3f}"
            f"{r['mrr']:>10.3f}"
            f"{r['query_latency_avg_ms']:>12.1f}"
        )


if __name__ == "__main__":
    main()
