"""investigate_entity_recall.py — caracterizar context_entity_recall (anómalo 0.211 con llama3.1).

Corre SOLO context_entity_recall sobre las 50 preguntas (retrieval-only, sin generación de
respuesta → más rápido), con el juez/extractor indicado en ENTITY_JUDGE. Guarda la distribución
per-row (NaN, ceros) para distinguir artefacto de parse vs valor genuinamente bajo.

Uso:
    docker compose exec -e RAG_RERANK=cross_encoder -e ENTITY_JUDGE=qwen2.5:7b-instruct-q4_K_M \
        backend python scripts/investigate_entity_recall.py
"""
from __future__ import annotations

import asyncio
import json
import math
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import scripts.run_ragas_lib_eval  # noqa: F401  (aplica el parche ollama al importar)
from app.config import settings
from app.services.embed_service import embed_query
from app.services.rag_service import _semantic_search
from app.database import AsyncSessionLocal

from langchain_ollama import ChatOllama, OllamaEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas import evaluate
from ragas.metrics import context_entity_recall
from datasets import Dataset

GOLDEN = BASE_DIR / "tests" / "fixtures" / "golden_set.json"


async def build_rows() -> list[dict]:
    golden = json.load(open(GOLDEN, encoding="utf-8"))["questions"]
    rows = []
    async with AsyncSessionLocal() as db:
        for q in golden:
            qv = await embed_query(q["question"])
            chunks = await _semantic_search(qv, db, query_text=q["question"])
            rows.append({
                "user_input": q["question"],
                "response": "",
                "retrieved_contexts": [c["content"] for c in chunks],
                "reference": q["ground_truth"],
            })
    return rows


def main():
    rows = asyncio.run(build_rows())
    ds = Dataset.from_list(rows)
    judge = os.environ.get("ENTITY_JUDGE") or settings.OLLAMA_MODEL
    llm = LangchainLLMWrapper(ChatOllama(
        base_url=settings.OLLAMA_BASE_URL, model=judge,
        temperature=0, num_ctx=4096, timeout=settings.OLLAMA_TIMEOUT,
    ))
    emb = LangchainEmbeddingsWrapper(OllamaEmbeddings(
        base_url=settings.OLLAMA_BASE_URL, model=settings.OLLAMA_EMBED_MODEL,
    ))
    print(f"context_entity_recall · juez/extractor={judge} · {len(rows)} q · rerank={settings.RAG_RERANK}")
    res = evaluate(dataset=ds, metrics=[context_entity_recall], llm=llm, embeddings=emb)
    df = res.to_pandas()
    col = "context_entity_recall"
    raw = list(df[col])
    vals = [float(v) for v in raw if isinstance(v, (int, float)) and not math.isnan(float(v))]
    nans = len(raw) - len(vals)
    zeros = sum(1 for v in vals if v == 0.0)
    mean = sum(vals) / len(vals) if vals else float("nan")
    print(f"\nmean(non-nan)={mean:.3f}  n_valid={len(vals)}  NaN={nans}  ceros={zeros}")
    print("distribución:", sorted(round(v, 2) for v in vals))


if __name__ == "__main__":
    main()
