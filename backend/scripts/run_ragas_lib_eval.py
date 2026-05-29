"""run_ragas_lib_eval.py — Cross-check con la librería ragas OFICIAL (instrumento autoritativo).

Mide las 6 métricas con la implementación canónica de `ragas`, usando juez local
(RAGAS_JUDGE_MODEL) + embeddings mxbai vía wrappers de LangChain. Sirve para comparar
contra los umbrales oficiales (0.70/0.75/0.80), que referencian las definiciones RAGAS
estándar — no las aproximaciones custom de run_ragas_eval.py.

Ejecutar:
    docker compose exec -e RAG_RERANK=cross_encoder -e RAGAS_JUDGE_MODEL=llama3.1:8b \
        backend python scripts/run_ragas_lib_eval.py [--max N]
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import settings
from scripts.run_ragas_eval import run_rag

from langchain_ollama import ChatOllama, OllamaEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    context_entity_recall,
    answer_correctness,
)
from datasets import Dataset

# Parche de compatibilidad: ragas pasa `temperature` (y a veces otros kwargs) como
# argumento top-level a ollama.{Async,}Client.chat(), que no los acepta → moverlos
# a `options`. Documentado: ragas es frágil con clientes no-OpenAI.
import inspect as _inspect
import ollama as _ollama

_OLLAMA_OPTS = {
    "temperature", "top_p", "top_k", "num_ctx", "num_predict",
    "stop", "seed", "repeat_penalty", "presence_penalty", "frequency_penalty",
}


def _patch_ollama_chat():
    for cls in (_ollama.AsyncClient, _ollama.Client):
        orig = cls.chat
        allowed = set(_inspect.signature(orig).parameters)

        def make(orig, allowed):
            def wrapper(self, *args, **kwargs):
                opts = dict(kwargs.get("options") or {})
                for k in list(kwargs):
                    if k in ("self", "options") or k in allowed:
                        continue
                    val = kwargs.pop(k)
                    if k in _OLLAMA_OPTS:
                        opts.setdefault(k, val)
                    # otros kwargs no soportados (ej. n) se descartan
                if opts:
                    kwargs["options"] = opts
                return orig(self, *args, **kwargs)
            return wrapper

        cls.chat = make(orig, allowed)


_patch_ollama_chat()

GOLDEN = BASE_DIR / "tests" / "fixtures" / "golden_set.json"
OUT_DIR = BASE_DIR / "scripts" / "ragas_runs"


async def build_rows(max_q: int | None) -> list[dict]:
    golden = json.load(open(GOLDEN, encoding="utf-8"))["questions"]
    if max_q:
        golden = golden[:max_q]
    rows = []
    for q in golden:
        answer, contexts = await run_rag(q["question"])
        rows.append({
            "user_input": q["question"],
            "response": answer,
            "retrieved_contexts": contexts,
            "reference": q["ground_truth"],
        })
        print(f"  RAG listo Q{q['id']} ({len(contexts)} ctx)")
    return rows


def main(max_q: int | None):
    rows = asyncio.run(build_rows(max_q))
    dataset = Dataset.from_list(rows)

    judge_model = settings.RAGAS_JUDGE_MODEL or settings.OLLAMA_MODEL
    llm = LangchainLLMWrapper(ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=judge_model,
        temperature=0,
        num_ctx=4096,
        timeout=settings.OLLAMA_TIMEOUT,
    ))
    emb = LangchainEmbeddingsWrapper(OllamaEmbeddings(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_EMBED_MODEL,
    ))

    metrics = [
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
        context_entity_recall,
        answer_correctness,
    ]

    print(f"\nEvaluando con ragas-lib · juez={judge_model} · {len(rows)} filas · rerank={settings.RAG_RERANK}")
    result = evaluate(dataset=dataset, metrics=metrics, llm=llm, embeddings=emb)

    print("\n=== RAGAS-LIB RESULT (agregado) ===")
    print(result)

    OUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    out = OUT_DIR / f"{stamp}_ragaslib.json"
    try:
        df = result.to_pandas()
        means = {c: float(df[c].mean()) for c in df.columns if df[c].dtype.kind in "fi"}
        payload = {
            "timestamp": stamp,
            "judge": judge_model,
            "rerank": settings.RAG_RERANK,
            "n": len(rows),
            "means": means,
        }
        out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print("\nMedias por métrica:")
        for k, v in means.items():
            print(f"  {k}: {v:.3f}")
        print(f"\nGuardado: {out}")
    except Exception as e:
        print(f"[warn] to_pandas/guardado falló: {e}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--max", type=int, default=None)
    main(p.parse_args().max)
