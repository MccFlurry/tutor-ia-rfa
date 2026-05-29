"""ragas_metrics.py — métricas RAGAS-style con juez LLM local. Sin dependencias de DB."""
from __future__ import annotations

import json
import re

import numpy as np
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings

ANSWER_RELEVANCY_N = 2


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
    return ChatOllama(
        base_url=settings.OLLAMA_BASE_URL,
        model=settings.OLLAMA_MODEL,
        temperature=0.7,
        num_ctx=4096,
        num_predict=256,
        timeout=settings.OLLAMA_TIMEOUT,
        format="json",
    )


async def _ainvoke_json(llm, system: str, human: str) -> dict | None:
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


async def metric_faithfulness(judge, answer: str, contexts: list[str]) -> float | None:
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
        return 1.0
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


async def metric_context_entities_recall(judge, ground_truth: str, contexts: list[str]) -> float | None:
    """Fracción de entidades del ground_truth presentes en el contexto recuperado."""
    ctx = "\n\n".join(contexts)
    extracted = await _ainvoke_json(
        judge,
        system=(
            "Extrae las entidades clave del texto: términos técnicos, nombres de "
            "clases/funciones/APIs, conceptos propios del dominio. Devuelve JSON: "
            '{"entities": ["e1", "e2", ...]}. Máximo 10 entidades. Sin duplicados.'
        ),
        human=f"Texto:\n{ground_truth}",
    )
    if not extracted or "entities" not in extracted:
        return None
    entities = [str(e).strip() for e in extracted["entities"] if str(e).strip()]
    if not entities:
        return 1.0
    verdict = await _ainvoke_json(
        judge,
        system=(
            "Para cada ENTIDAD, responde si aparece (literalmente o por sinónimo "
            'directo) en el CONTEXTO. Devuelve JSON: {"verdicts": '
            '[{"entity": "...", "present": true|false}, ...]}.'
        ),
        human=f"CONTEXTO:\n{ctx}\n\nENTIDADES:\n" + "\n".join(f"- {e}" for e in entities),
    )
    if not verdict or "verdicts" not in verdict:
        return None
    vs = verdict["verdicts"]
    if not vs:
        return None
    present = sum(1 for v in vs if isinstance(v, dict) and v.get("present") is True)
    return round(present / len(vs), 3)


async def metric_answer_correctness(judge, embedder, answer: str, ground_truth: str) -> float | None:
    """RAGAS-style: 0.75·F1_factual + 0.25·coseno(answer, ground_truth)."""
    classified = await _ainvoke_json(
        judge,
        system=(
            "Compara una RESPUESTA con la RESPUESTA CORRECTA. Cuenta las afirmaciones:\n"
            "- TP: presentes en RESPUESTA y respaldadas por RESPUESTA CORRECTA\n"
            "- FP: presentes en RESPUESTA pero NO en RESPUESTA CORRECTA\n"
            "- FN: presentes en RESPUESTA CORRECTA pero ausentes en RESPUESTA\n"
            'Devuelve JSON: {"tp": n, "fp": n, "fn": n} (enteros).'
        ),
        human=f"RESPUESTA:\n{answer}\n\nRESPUESTA CORRECTA:\n{ground_truth}",
    )
    if not classified:
        return None
    try:
        tp = int(classified.get("tp", 0))
        fp = int(classified.get("fp", 0))
        fn = int(classified.get("fn", 0))
    except (TypeError, ValueError, AttributeError):
        return None
    denom = tp + 0.5 * (fp + fn)
    f1 = (tp / denom) if denom > 0 else 0.0
    embs = await embedder.aembed_documents([answer, ground_truth])
    a, g = np.array(embs[0]), np.array(embs[1])
    na, ng = np.linalg.norm(a), np.linalg.norm(g)
    sem = float(np.dot(a, g) / (na * ng)) if na and ng else 0.0
    return round(0.75 * f1 + 0.25 * sem, 3)
