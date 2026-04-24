"""
run_ragas_eval.py — Evaluación RAGAS-style del pipeline RAG.

Implementa las 4 métricas estándar RAGAS con Ollama local (más robusto
que la librería `ragas` con LLMs no-OpenAI):

- faithfulness       — proporción de claims del answer soportadas por el contexto
- answer_relevancy   — similitud semántica entre pregunta original y pregunta
                       inferida por el LLM a partir del answer
- context_precision  — proporción de chunks recuperados marcados relevantes
- context_recall     — proporción de sentencias de ground_truth cubiertas por el contexto

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
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import settings
from app.database import AsyncSessionLocal as async_session_maker, engine
from app.services.rag_service import query_rag, _semantic_search
from app.services.embed_service import embed_query
import redis.asyncio as aioredis
import logging

# Silenciar eco SQL + loguru verbose
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
engine.echo = False


GOLDEN_PATH = BASE_DIR / "tests" / "fixtures" / "golden_set.json"
OUT_DIR = BASE_DIR / "scripts" / "ragas_runs"
OUT_DIR.mkdir(exist_ok=True)

ANSWER_RELEVANCY_N = 2  # número de preguntas sintéticas generadas por answer


# ----------------------------------------------------------------------------
# Judge LLM (temperature=0 para determinismo)
# ----------------------------------------------------------------------------
def make_judge() -> ChatOllama:
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.0,
        num_ctx=4096,
        num_predict=512,
        timeout=settings.OLLAMA_TIMEOUT,
        format="json",
    )


def make_generator() -> ChatOllama:
    # temperature > 0 para que genere preguntas ligeramente distintas en answer_relevancy
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.7,
        num_ctx=4096,
        num_predict=256,
        timeout=settings.OLLAMA_TIMEOUT,
        format="json",
    )


async def _ainvoke_json(llm: ChatOllama, system: str, human: str) -> dict | None:
    try:
        resp = await llm.ainvoke([
            SystemMessage(content=system),
            HumanMessage(content=human),
        ])
        raw = resp.content.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        return json.loads(raw)
    except Exception as e:
        print(f"  [warn] LLM JSON error: {e}")
        return None


# ----------------------------------------------------------------------------
# Métricas
# ----------------------------------------------------------------------------
async def metric_faithfulness(judge, answer: str, contexts: list[str]) -> float | None:
    """
    1. Extraer claims del answer.
    2. Juzgar cada claim contra contextos concatenados.
    """
    ctx = "\n\n".join(contexts)

    extracted = await _ainvoke_json(
        judge,
        system=(
            "Extrae los claims verificables del texto. Devuelve JSON: "
            '{"claims": ["claim1", "claim2", ...]}. Cada claim es una afirmación '
            "atómica y autónoma. Máximo 8 claims. Ignora saludos u opinión."
        ),
        human=f"Texto:\n{answer}",
    )
    if not extracted or "claims" not in extracted:
        return None
    claims = [str(c).strip() for c in extracted["claims"] if str(c).strip()]
    if not claims:
        return 1.0  # sin claims → no hay nada que pueda ser falso

    verdict = await _ainvoke_json(
        judge,
        system=(
            "Para cada claim, responde si está respaldado por el CONTEXTO. "
            'Devuelve JSON: {"verdicts": [{"claim": "...", "supported": true|false}, ...]}. '
            "Sé estricto: solo true si el contexto lo afirma explícitamente o lo implica directamente."
        ),
        human=f"CONTEXTO:\n{ctx}\n\nCLAIMS:\n" + "\n".join(f"- {c}" for c in claims),
    )
    if not verdict or "verdicts" not in verdict:
        return None

    verdicts = verdict["verdicts"]
    if not verdicts:
        return None
    supported = 0
    for v in verdicts:
        if isinstance(v, dict):
            if v.get("supported") is True:
                supported += 1
        elif isinstance(v, bool) and v:
            supported += 1
    return round(supported / len(verdicts), 3)


async def metric_answer_relevancy(gen, embedder, question: str, answer: str) -> float | None:
    """
    1. LLM genera N preguntas sintéticas a partir del answer.
    2. Embed original question + preguntas sintéticas.
    3. Promedio de similitudes coseno.
    """
    synth = await _ainvoke_json(
        gen,
        system=(
            f"Dada una respuesta, genera exactamente {ANSWER_RELEVANCY_N} preguntas "
            "diferentes que esa respuesta contestaría. Devuelve JSON: "
            '{"questions": ["q1", "q2"]}. Las preguntas deben ser en español y específicas.'
        ),
        human=f"Respuesta:\n{answer}",
    )
    if not synth or "questions" not in synth:
        return None
    qs = [str(q).strip() for q in synth["questions"] if str(q).strip()]
    if not qs:
        return None

    # Embed
    embs_q = await embedder.aembed_documents([question] + qs)
    orig = np.array(embs_q[0])
    others = np.array(embs_q[1:])

    def cosine(a, b):
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    sims = [cosine(orig, e) for e in others]
    return round(float(np.mean(sims)), 3)


async def metric_context_precision(judge, question: str, ground_truth: str, contexts: list[str]) -> float | None:
    """
    Para cada chunk, LLM decide si es útil para responder. Precisión posicional ponderada
    (chunks más relevantes arriba tienen mayor peso).
    """
    if not contexts:
        return 0.0

    payload = "\n\n".join(f"[Chunk {i+1}]\n{c}" for i, c in enumerate(contexts))
    verdict = await _ainvoke_json(
        judge,
        system=(
            "Dada una PREGUNTA y una RESPUESTA CORRECTA, decide para cada CHUNK "
            "si es útil para responder. Devuelve JSON: "
            '{"verdicts": [{"useful": true|false}, ...]} en el MISMO ORDEN de los chunks.'
        ),
        human=f"PREGUNTA: {question}\nRESPUESTA CORRECTA: {ground_truth}\n\nCHUNKS:\n{payload}",
    )
    if not verdict or "verdicts" not in verdict:
        return None
    vs = verdict["verdicts"]
    useful = []
    for v in vs:
        if isinstance(v, dict):
            useful.append(bool(v.get("useful")))
        elif isinstance(v, bool):
            useful.append(v)
    if not useful:
        return None

    # AP@k style: Σ (P@k × rel_k) / total_rel
    total_rel = sum(useful)
    if total_rel == 0:
        return 0.0
    precision_at_k = []
    hits = 0
    for k, u in enumerate(useful, 1):
        if u:
            hits += 1
            precision_at_k.append(hits / k)
    return round(sum(precision_at_k) / total_rel, 3)


async def metric_context_recall(judge, ground_truth: str, contexts: list[str]) -> float | None:
    """
    Break ground_truth en sentencias. Para cada una, juzgar si es atribuible al contexto.
    """
    ctx = "\n\n".join(contexts)
    extracted = await _ainvoke_json(
        judge,
        system=(
            "Parte el texto en sentencias atómicas. Devuelve JSON: "
            '{"sentences": ["s1", "s2", ...]}. Máximo 8 sentencias.'
        ),
        human=f"Texto:\n{ground_truth}",
    )
    if not extracted or "sentences" not in extracted:
        return None
    sents = [str(s).strip() for s in extracted["sentences"] if str(s).strip()]
    if not sents:
        return 1.0

    verdict = await _ainvoke_json(
        judge,
        system=(
            "Para cada SENTENCIA, responde si está respaldada por el CONTEXTO. "
            'Devuelve JSON: {"verdicts": [{"sentence": "...", "attributable": true|false}, ...]}. '
            "Sé estricto."
        ),
        human=f"CONTEXTO:\n{ctx}\n\nSENTENCIAS:\n" + "\n".join(f"- {s}" for s in sents),
    )
    if not verdict or "verdicts" not in verdict:
        return None
    vs = verdict["verdicts"]
    if not vs:
        return None
    attr = 0
    for v in vs:
        if isinstance(v, dict):
            if v.get("attributable") is True:
                attr += 1
        elif isinstance(v, bool) and v:
            attr += 1
    return round(attr / len(vs), 3)


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
                row["answer_relevancy"] = await metric_answer_relevancy(
                    gen, embedder, q["question"], answer
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
                for k in ("faithfulness", "answer_relevancy", "context_precision", "context_recall")
            )
            print(f"Q{qid:02d} [{q['module']}/{q['type']:12s}/{q['difficulty']:6s}] "
                  f"{row['elapsed_s']:5.1f}s  {metrics_str}  ·  {q['question'][:50]}")

    # Summary
    def avg(key):
        vals = [r[key] for r in results if isinstance(r[key], (int, float))]
        return round(sum(vals) / len(vals), 3) if vals else None

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
            "embed": settings.OLLAMA_EMBED_MODEL,
        },
        "global": {
            "faithfulness": avg("faithfulness"),
            "answer_relevancy": avg("answer_relevancy"),
            "context_precision": avg("context_precision"),
            "context_recall": avg("context_recall"),
        },
        "thresholds": {
            "faithfulness_required": 0.75,
            "answer_relevancy_required": 0.70,
        },
        "pass": {
            "faithfulness": (avg("faithfulness") or 0) >= 0.75,
            "answer_relevancy": (avg("answer_relevancy") or 0) >= 0.70,
        },
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
            }
        summary[f"by_{dim}"] = breakdown

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*70}")
    print("RESUMEN")
    print(f"{'='*70}")
    print(json.dumps(summary["global"], indent=2))
    print(f"\nfaithfulness ≥ 0.75  ·  {'✓' if summary['pass']['faithfulness'] else '✗'}")
    print(f"answer_relevancy ≥ 0.70  ·  {'✓' if summary['pass']['answer_relevancy'] else '✗'}")
    print(f"\nCSV:     {out_csv}")
    print(f"Summary: {out_json}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=None, help="Limitar número de preguntas")
    parser.add_argument("--iter", dest="label", type=str, default="baseline", help="Etiqueta iteración")
    args = parser.parse_args()
    asyncio.run(main(args.max, args.label))
