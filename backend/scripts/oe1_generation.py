"""oe1_generation.py — Métricas de generación OE1 sobre el golden set.

Mide las métricas oficiales de OE1 que faltaban en el reporte-LLM original, para el/los
LLM indicados (por defecto el modelo SELECCIONADO qwen2.5):

  - ROUGE-L (F1)        ≥ 0.35   answer vs ground_truth
  - BLEU                ≥ 0.25   answer vs ground_truth (sacrebleu, tokenize=intl, corpus)
  - Accuracy            ≥ 0.70   juez independiente llama3.1 → consistencia factual
  - Likert media        ≥ 4.0    juez independiente (4 criterios 1-5)
  - Cohen's κ           ≥ 0.60   concordancia inter-juez (llama3.1 vs llama3) sobre Likert

Arquitectura POR FASES para minimizar swapping de modelos en GPU (clave de estabilidad):
  Fase 0: recuperar contexto de las 50 preguntas (mxbai + cross-encoder rerank), una sola vez.
  Fase 1: generar respuestas agrupando por modelo generador (1 carga por modelo).
  Fase 2: ROUGE-L / BLEU (CPU, sin modelo).
  Fase 3: juzgar agrupando por juez (1 carga por juez). Cada llamada LLM con try/except.
  Fase 4: agregación + Cohen's κ.

Respuestas generadas con el pipeline RAG de producción (config idéntica a rag_service),
contexto compartido entre modelos para comparación justa.

Ejecutar:
    docker exec -e RAG_RERANK=cross_encoder tutor_backend \
        python scripts/oe1_generation.py [--max N] [--models m1,m2]

Salida: docs/oe1_generation_results.json + docs/oe1_generation_log.jsonl
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import settings
from app.database import AsyncSessionLocal as async_session_maker, engine
from app.services.embed_service import embed_query
from app.services.rag_service import _semantic_search, _build_context, SYSTEM_PROMPT

import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
engine.echo = False

from rouge_score import rouge_scorer
import sacrebleu
from sklearn.metrics import cohen_kappa_score

GOLDEN = BASE_DIR / "tests" / "fixtures" / "golden_set.json"
OUT_JSON = BASE_DIR / "docs" / "oe1_generation_results.json"
LOG = BASE_DIR / "docs" / "oe1_generation_log.jsonl"

DEFAULT_MODELS = ["qwen2.5:7b-instruct-q4_K_M"]   # modelo seleccionado (OE1)
JUDGE_A = "llama3.1:8b"                            # juez independiente (≠ generador)
JUDGE_B = "llama3:8b-instruct-q4_K_M"             # 2º juez para Cohen's κ

THRESHOLDS = {"rougeL": 0.35, "bleu": 0.25, "accuracy": 0.70, "likert": 4.0, "kappa": 0.60}
_CRIT = ("exactitud", "fluidez", "sin_alucinacion", "pedagogia")
_rouge = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False)

JUDGE_PROMPT = """Eres un evaluador experto del curso Aplicaciones Móviles (Android/Kotlin).
Evalúa la RESPUESTA del estudiante frente a la RESPUESTA DE REFERENCIA.

PREGUNTA:
{question}

RESPUESTA DE REFERENCIA (correcta):
{reference}

RESPUESTA DEL ESTUDIANTE:
{answer}

Califica con una rúbrica Likert 1-5 (5=excelente) en cuatro criterios y emite un veredicto
de corrección factual. Devuelve SOLO un objeto JSON con esta forma exacta:
{{"razon": "<una frase>", "exactitud": <1-5>, "fluidez": <1-5>, "sin_alucinacion": <1-5>, "pedagogia": <1-5>, "correcto": <true|false>}}

- razon: una sola frase justificando el veredicto de corrección.
- exactitud: corrección técnica respecto a la referencia y al dominio Android/Kotlin.
- fluidez: español natural, gramatical, no traducción literal.
- sin_alucinacion: no inventa APIs/clases/comportamientos ausentes de la referencia.
- pedagogia: tono didáctico, claridad para nivel técnico-superior.
- correcto: evalúa CONSISTENCIA FACTUAL, no coincidencia literal. Marca true si la respuesta
  transmite correctamente el hecho central de la referencia, SIN errores ni contradicciones
  graves. TOLERA: paráfrasis, sinónimos, detalles adicionales correctos, omisiones menores,
  mayor o menor extensión. Marca false SOLO si hay un error factual claro, una contradicción
  con la referencia, una alucinación, o si se omite el hecho central."""


def _parse_judge(raw: str) -> dict | None:
    import re
    txt = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        obj = json.loads(txt)
    except Exception:
        m = re.search(r"\{.*\}", txt, re.DOTALL)
        if not m:
            return None
        try:
            obj = json.loads(m.group(0))
        except Exception:
            return None
    if isinstance(obj, dict) and isinstance(obj.get("questions"), list) and obj["questions"]:
        obj = obj["questions"][0]
    if not isinstance(obj, dict):
        return None
    out = {}
    for k in _CRIT:
        try:
            v = float(obj.get(k))
            out[k] = max(1.0, min(5.0, v))
        except (TypeError, ValueError):
            out[k] = None
    c = obj.get("correcto")
    if isinstance(c, str):
        c = c.strip().lower() in ("true", "sí", "si", "1", "verdadero")
    out["correcto"] = bool(c)
    return out


def _overall_int(score: dict) -> int | None:
    crit = [score[c] for c in _CRIT if score.get(c) is not None]
    return int(round(sum(crit) / len(crit))) if crit else None


async def main(max_q: int | None, models: list[str]):
    golden = json.load(open(GOLDEN, encoding="utf-8"))["questions"]
    if max_q:
        golden = golden[:max_q]
    qids = [q["id"] for q in golden]
    gmap = {q["id"]: q for q in golden}

    LOG.parent.mkdir(parents=True, exist_ok=True)
    log_f = open(LOG, "w", encoding="utf-8")

    def logw(rec):
        log_f.write(json.dumps(rec, ensure_ascii=False) + "\n"); log_f.flush()

    print(f"OE1 generación · {len(golden)} preguntas × {len(models)} modelos · "
          f"jueces={JUDGE_A}|{JUDGE_B} · rerank={settings.RAG_RERANK}")

    # ---- Fase 0: contexto compartido (mxbai + rerank), una sola vez ----
    contexts: dict[int, str] = {}
    async with async_session_maker() as db:
        for q in golden:
            try:
                qvec = await embed_query(q["question"])
                chunks = await _semantic_search(qvec, db, query_text=q["question"])
                contexts[q["id"]] = _build_context(chunks) if chunks else "Sin contexto recuperado."
            except Exception as e:
                contexts[q["id"]] = "Sin contexto recuperado."
                print(f"  [err retrieve] Q{q['id']}: {e}")
    print(f"Fase 0 ✓ contextos: {len(contexts)}")

    # ---- Fase 1: generación, agrupada por modelo ----
    answers: dict[tuple[str, int], str] = {}
    for m in models:
        llm = ChatOllama(base_url=settings.OLLAMA_BASE_URL, model=m, temperature=0.1,
                         num_ctx=8192, num_predict=2048, timeout=settings.OLLAMA_TIMEOUT)
        ok = 0
        for qid in qids:
            q = gmap[qid]
            sysc = SYSTEM_PROMPT.format(context=contexts[qid], history="Sin historial previo.")
            try:
                resp = await llm.ainvoke([SystemMessage(content=sysc), HumanMessage(content=q["question"])])
                answers[(m, qid)] = resp.content
                ok += 1
                logw({"phase": "gen", "model": m, "qid": qid, "answer": resp.content[:600]})
            except Exception as e:
                logw({"phase": "gen", "model": m, "qid": qid, "error": str(e)[:200]})
                print(f"  [err gen] Q{qid} {m}: {str(e)[:120]}")
        print(f"Fase 1 ✓ {m}: {ok}/{len(qids)} respuestas")

    # ---- Fase 2: ROUGE-L + BLEU (CPU) ----
    rouge = {m: [] for m in models}
    bleu_h = {m: [] for m in models}
    bleu_r = {m: [] for m in models}
    for m in models:
        for qid in qids:
            ans = answers.get((m, qid))
            if ans is None:
                continue
            ref = gmap[qid]["ground_truth"]
            rouge[m].append(_rouge.score(ref, ans)["rougeL"].fmeasure)
            bleu_h[m].append(ans)
            bleu_r[m].append(ref)
    print("Fase 2 ✓ ROUGE-L/BLEU")

    # ---- Fase 3: jueces, agrupados por juez ----
    scores: dict[tuple[str, str, int], dict] = {}  # (judge, model, qid) -> parsed
    for j in (JUDGE_A, JUDGE_B):
        jl = ChatOllama(base_url=settings.OLLAMA_BASE_URL, model=j, temperature=0,
                        num_ctx=8192, format="json", timeout=settings.OLLAMA_TIMEOUT)
        done = 0
        for m in models:
            for qid in qids:
                ans = answers.get((m, qid))
                if ans is None:
                    continue
                q = gmap[qid]
                prompt = JUDGE_PROMPT.format(question=q["question"], reference=q["ground_truth"], answer=ans[:4000])
                try:
                    resp = await jl.ainvoke([HumanMessage(content=prompt)])
                    parsed = _parse_judge(resp.content)
                    if parsed:
                        scores[(j, m, qid)] = parsed
                        done += 1
                        logw({"phase": "judge", "judge": j, "model": m, "qid": qid,
                              "likert": round(sum(parsed[c] for c in _CRIT if parsed[c]) /
                                              max(1, len([c for c in _CRIT if parsed[c]])), 2),
                              "correcto": parsed["correcto"]})
                except Exception as e:
                    logw({"phase": "judge", "judge": j, "model": m, "qid": qid, "error": str(e)[:200]})
                    print(f"  [err judge {j}] Q{qid} {m}: {str(e)[:120]}")
        print(f"Fase 3 ✓ juez {j}: {done} evaluaciones")

    # ---- Fase 4: agregación ----
    def mean(xs):
        return round(sum(xs) / len(xs), 4) if xs else None

    results = {"models": {}, "thresholds": THRESHOLDS,
               "config": {"judge_A": JUDGE_A, "judge_B": JUDGE_B, "rerank": settings.RAG_RERANK,
                          "n_questions": len(golden), "answer_config": "RAG-augmented (producción)",
                          "accuracy_judge": JUDGE_A, "likert_judge": JUDGE_A}}
    for m in models:
        corr = [1 if scores[(JUDGE_A, m, qid)]["correcto"] else 0
                for qid in qids if (JUDGE_A, m, qid) in scores]
        likert_overall = []
        by_crit = {c: [] for c in _CRIT}
        for qid in qids:
            s = scores.get((JUDGE_A, m, qid))
            if not s:
                continue
            crit = [s[c] for c in _CRIT if s[c] is not None]
            if crit:
                likert_overall.append(sum(crit) / len(crit))
                for c in _CRIT:
                    if s[c] is not None:
                        by_crit[c].append(s[c])
        corpus_bleu = (sacrebleu.corpus_bleu(bleu_h[m], [bleu_r[m]], tokenize="intl").score / 100.0) if bleu_h[m] else None
        results["models"][m] = {
            "rougeL": mean(rouge[m]),
            "bleu": round(corpus_bleu, 4) if corpus_bleu is not None else None,
            "accuracy": mean(corr),
            "likert_media": mean(likert_overall),
            "by_criterion": {c: mean(v) for c, v in by_crit.items()},
            "n_answers": len(rouge[m]),
            "n_judged": len(likert_overall),
        }

    # Cohen's κ inter-juez (cuadrático), global sobre todos los (model,qid) con ambos jueces
    ka, kb = [], []
    for m in models:
        for qid in qids:
            sa, sb = scores.get((JUDGE_A, m, qid)), scores.get((JUDGE_B, m, qid))
            if sa and sb:
                oa, ob = _overall_int(sa), _overall_int(sb)
                if oa and ob:
                    ka.append(oa); kb.append(ob)
    kappa = None
    if len(ka) >= 2 and len(set(ka + kb)) > 1:
        try:
            kappa = round(float(cohen_kappa_score(ka, kb, weights="quadratic", labels=[1, 2, 3, 4, 5])), 4)
        except Exception as e:
            kappa = f"error: {e}"
    results["kappa_interjudge"] = kappa
    results["kappa_n"] = len(ka)

    log_f.close()
    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n=== OE1 GENERACIÓN ===")
    for m, r in results["models"].items():
        print(f"{m}: ROUGE-L={r['rougeL']} BLEU={r['bleu']} Acc={r['accuracy']} "
              f"Likert={r['likert_media']} (n_judged={r['n_judged']})")
    print(f"Cohen's κ inter-juez (n={len(ka)}): {kappa}")
    print(f"Guardado: {OUT_JSON}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--max", type=int, default=None)
    p.add_argument("--models", type=str, default=",".join(DEFAULT_MODELS))
    a = p.parse_args()
    asyncio.run(main(a.max, [m.strip() for m in a.models.split(",") if m.strip()]))
