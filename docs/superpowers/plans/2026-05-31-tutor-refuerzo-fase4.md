# Refuerzo en Evaluaciones (Fase 4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refuerzo del tutor tras responder: nudges deterministas por puntaje en quiz/coding/evaluación de entrada, reusando el motor de Fase 1. Sin LLM.

**Architecture:** Los contextos `quiz_result|coding_result|assessment_result` (ya declarados en `build_nudges`) reciben reglas por bandas de `score` (0-100). `get_nudges` corta para esos contextos SIN consultar BD (sólo dependen del `score` recién enviado). Frontend monta `<TutorNudgeList context="*_result" score=...>` en las pantallas de resultado.

**Tech Stack:** FastAPI + pytest (backend); React + TS + Vitest (frontend).

**Scores (verificado, todos 0-100):** quiz `QuizSubmitResponse.score = round(score*100,1)`; coding `CodingEvaluation.score` 0-100; assessment `AssessmentSubmitResponse.score` 0-100. Aprobado quiz = ≥60.

**Convención:** rama `feat/tutor-refuerzo` desde `main`. Backend desde `C:\tutor-ia-rfa\backend`, frontend desde `C:\tutor-ia-rfa\frontend`.

---

### Task 0: Crear rama

- [ ] **Step 1:**
```bash
git checkout main
git checkout -b feat/tutor-refuerzo
```

---

### Task 1: Reglas de resultado en el motor + corte en `get_nudges`

**Files:**
- Modify: `backend/app/services/tutor_service.py`
- Test: `backend/tests/unit/test_tutor_service.py` (agregar tests)

- [ ] **Step 1: Agregar tests que fallan** — añadir al final de `backend/tests/unit/test_tutor_service.py`:

```python
# --- Fase 4: contextos de resultado (independientes del snapshot) ---
from app.services.tutor_service import build_nudges as _bn


def test_quiz_result_high_score():
    n = _bn(None, "quiz_result", topic_id=5, score=90)
    assert len(n) == 1 and n[0].id == "quiz_result_high" and n[0].tone == "success"


def test_quiz_result_pass_band():
    n = _bn(None, "quiz_result", topic_id=5, score=70)
    assert n[0].id == "quiz_result_pass"
    assert n[0].cta_route == "/topics/5"


def test_quiz_result_low_score_warns_and_links_topic():
    n = _bn(None, "quiz_result", topic_id=8, score=40)
    assert n[0].id == "quiz_result_low" and n[0].tone == "warning"
    assert n[0].cta_route == "/topics/8"


def test_coding_result_bands():
    assert _bn(None, "coding_result", score=85)[0].id == "coding_result_high"
    assert _bn(None, "coding_result", score=65)[0].id == "coding_result_mid"
    assert _bn(None, "coding_result", score=30)[0].id == "coding_result_low"


def test_assessment_result_levels_link_modules():
    beginner = _bn(None, "assessment_result", score=20)[0]
    assert beginner.id == "assessment_result" and beginner.cta_route == "/modules"
    assert _bn(None, "assessment_result", score=60)[0].cta_route == "/modules"
    assert _bn(None, "assessment_result", score=90)[0].cta_route == "/modules"


def test_result_context_without_score_is_empty():
    assert _bn(None, "quiz_result", score=None) == []
```

- [ ] **Step 2: Correr para verificar que fallan**

Run (desde `backend/`): `pytest tests/unit/test_tutor_service.py -v`
Expected: los nuevos tests FALLAN (hoy los contextos de resultado devuelven `[]`).

- [ ] **Step 3: Implementar las reglas de resultado.**

En `backend/app/services/tutor_service.py`:

(a) Agregar el helper (antes de `build_nudges` o después; pura función):

```python
RESULT_CONTEXTS = ("quiz_result", "coding_result", "assessment_result")


def _result_nudges(context: str, score: float | None, topic_id: int | None) -> list[Nudge]:
    """Refuerzo determinista por banda de puntaje (0-100). Fase 4."""
    if score is None:
        return []

    if context == "quiz_result":
        if score >= 80:
            return [Nudge(
                id="quiz_result_high", tone="success", icon="trophy",
                title="¡Excelente trabajo!",
                message="Dominas este tema. Mantén el ritmo y sigue avanzando.",
            )]
        if score >= 60:
            return [Nudge(
                id="quiz_result_pass", tone="success", icon="check",
                title="¡Aprobaste!",
                message="Buen trabajo. Repasa los puntos que fallaste para afianzar lo aprendido.",
                cta_label="Repasar el tema" if topic_id else None,
                cta_route=f"/topics/{topic_id}" if topic_id else None,
            )]
        return [Nudge(
            id="quiz_result_low", tone="warning", icon="repeat",
            title="Casi lo logras",
            message="No alcanzaste el 60%. Repasa el contenido y vuelve a intentarlo; cada intento te acerca.",
            cta_label="Repasar el tema" if topic_id else None,
            cta_route=f"/topics/{topic_id}" if topic_id else None,
        )]

    if context == "coding_result":
        if score >= 80:
            return [Nudge(
                id="coding_result_high", tone="success", icon="trophy",
                title="¡Código sólido!",
                message="Gran solución. Anímate con un desafío de mayor dificultad.",
            )]
        if score >= 60:
            return [Nudge(
                id="coding_result_mid", tone="encourage", icon="rocket",
                title="Buen avance",
                message="Tu código funciona; revisa las mejoras sugeridas para pulirlo aún más.",
            )]
        return [Nudge(
            id="coding_result_low", tone="warning", icon="repeat",
            title="Sigamos puliendo",
            message="Revisa la retroalimentación y las pistas, ajusta tu código y vuelve a enviarlo.",
        )]

    if context == "assessment_result":
        if score < 40:
            msg = "Empezarás por las bases. Sigue el orden de los módulos desde el M1, a tu ritmo."
        elif score <= 75:
            msg = "Tienes buenas bases. Enfócate en los temas que más se te dificulten."
        else:
            msg = "¡Gran dominio! Reta tus habilidades con los módulos más avanzados."
        return [Nudge(
            id="assessment_result", tone="info", icon="compass",
            title="Tu ruta de aprendizaje",
            message=msg, cta_label="Ver módulos", cta_route="/modules",
        )]

    return []
```

(b) En `build_nudges`, manejar los contextos de resultado **al inicio** (antes del guard `if not snap.has_level`), porque sólo dependen del `score`, no del snapshot:

```python
def build_nudges(snap, context, *, topic_id=None, module_id=None, score=None):
    # Fase 4 — contextos de resultado: deterministas por score, sin snapshot
    if context in RESULT_CONTEXTS:
        return _result_nudges(context, score, topic_id)

    nudges: list[Nudge] = []
    # R1 — sin evaluación de entrada...
    if not snap.has_level:
        ...
```
Y ELIMINAR el comentario/`return nudges` final que decía "contextos de resultado ... → Fase 4" (ya no se alcanza para esos contextos). El `return nudges` final para contextos desconocidos puede quedarse.

(c) En `get_nudges`, evitar la consulta a BD para contextos de resultado:

```python
async def get_nudges(user, db, context, *, topic_id=None, module_id=None, score=None):
    if context in RESULT_CONTEXTS:
        # No requieren estado de BD; sólo el score recién enviado.
        return build_nudges(None, context, topic_id=topic_id, module_id=module_id, score=score)
    snap = await gather_snapshot(user, db, topic_id=topic_id)
    return build_nudges(snap, context, topic_id=topic_id, module_id=module_id, score=score)
```

> Nota: `build_nudges` con `snap=None` SÓLO es válido para contextos de resultado (no tocan `snap`). Para otros contextos `get_nudges` siempre pasa un snapshot real.

- [ ] **Step 4: Correr tests** → todos los de `test_tutor_service.py` pasan (los 8 originales + los nuevos). Luego `pytest -q` (full) sin regresiones (los tests de integración de `quiz_result` en `test_router_tutor.py`, si existieran, no aplican — el endpoint sigue igual).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/tutor_service.py backend/tests/unit/test_tutor_service.py
git commit -m "feat(tutor): refuerzo por score en contextos de resultado (Fase 4)"
```

---

### Task 2: Montar refuerzo en pantallas de resultado + iconos faltantes

**Files:**
- Modify: `frontend/src/components/tutor/TutorNudge.tsx` (agregar iconos trophy/check)
- Modify: `frontend/src/pages/QuizPage.tsx`
- Modify: `frontend/src/pages/CodingChallengePage.tsx`
- Modify: `frontend/src/pages/EntryAssessmentPage.tsx`

- [ ] **Step 1: Agregar iconos al mapa de `TutorNudge`** — en `frontend/src/components/tutor/TutorNudge.tsx`, importar `Trophy` y `CheckCircle2` de lucide-react y agregarlos al `ICONS`:
```tsx
import { Compass, Rocket, Hand, Flag, Flame, Repeat, Sparkles, Trophy, CheckCircle2 } from 'lucide-react'
// ...
const ICONS: Record<string, LucideIcon> = {
  compass: Compass, rocket: Rocket, hand: Hand,
  flag: Flag, flame: Flame, repeat: Repeat,
  trophy: Trophy, check: CheckCircle2,
}
```

- [ ] **Step 2: QuizPage** — en `frontend/src/pages/QuizPage.tsx`, importar `TutorNudgeList` y montarlo dentro del branch de resultado, encima de `<QuizResults .../>`:
```tsx
import TutorNudgeList from '@/components/tutor/TutorNudgeList'
// ...
{result ? (
  <div className="space-y-6">
    <TutorNudgeList context="quiz_result" topicId={tid} score={result.score} />
    <QuizResults result={result} onRetry={handleRetry} onBack={() => navigate(`/topics/${tid}`)} />
  </div>
) : (
```
(Envolver `QuizResults` y el nudge en un contenedor; ajustar al JSX real sin romper el `: (` del ternario.)

- [ ] **Step 3: CodingChallengePage** — importar `TutorNudgeList` y montarlo dentro de `{result && (...)}` (sección de resultados, ~línea 312), arriba del bloque de score:
```tsx
import TutorNudgeList from '@/components/tutor/TutorNudgeList'
// ...dentro de {result && ( ... )}, como primer hijo:
<TutorNudgeList context="coding_result" score={result.score} />
```

- [ ] **Step 4: EntryAssessmentPage** — importar `TutorNudgeList` y montarlo dentro de `if (result) { return (...) }` (~línea 130), cerca del encabezado del resultado:
```tsx
import TutorNudgeList from '@/components/tutor/TutorNudgeList'
// ...dentro del bloque de resultado:
<TutorNudgeList context="assessment_result" score={result.score} />
```

- [ ] **Step 5: Verificar** — desde `frontend/`: `npx tsc --noEmit && npx vitest run` → limpio + toda la suite pasa.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/tutor/TutorNudge.tsx frontend/src/pages/QuizPage.tsx frontend/src/pages/CodingChallengePage.tsx frontend/src/pages/EntryAssessmentPage.tsx
git commit -m "feat(tutor): refuerzo del tutor en resultados de quiz/coding/evaluacion"
```

---

### Task 3: Documentación

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/matriz-trazabilidad-ISO25010.md`

- [ ] **Step 1: CLAUDE.md** — tras el bullet "**ACOMPAÑAMIENTO PROACTIVO (Fase 3) ✅** ...", agregar:

```
- **ACOMPAÑAMIENTO PROACTIVO (Fase 4) ✅** Refuerzo post-respuesta en quiz/coding/evaluación de entrada: nudges deterministas por banda de puntaje (`*_result` en `tutor_service`), `<TutorNudgeList context="*_result" score=...>` montado en QuizPage/CodingChallengePage/EntryAssessmentPage. Reusa el motor de Fase 1, sin nuevas llamadas LLM. Cierra el acompañamiento proactivo (Fases 1-4).
```

Y en `### /tutor` (API REST) añadir nota: los contextos `*_result` reciben `score` y no consultan BD (refuerzo inmediato).

- [ ] **Step 2: matriz ISO** — agregar `RF-NEW-TUTOR-04`: "Refuerzo del tutor en resultados de evaluación (quiz/coding/entrada)" ↔ `tutor_service._result_nudges` + montajes en pantallas de resultado ↔ Tests `test_tutor_service.py` (bandas de resultado) ↔ "Pertinencia funcional / Operabilidad" ↔ implementado. Mismo formato; NO renumerar RF-01..33.

- [ ] **Step 3: guardian** — `pytest tests/integration/test_iso25010.py -v` (desde `backend/`). Reconciliar si rompe.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md docs/matriz-trazabilidad-ISO25010.md
git commit -m "docs(tutor): registrar Fase 4 refuerzo en evaluaciones y RF en matriz ISO"
```

---

## Verificación final de Fase 4

- [ ] `pytest -q` (backend) verde; nuevos tests de bandas de resultado pasan.
- [ ] `npx tsc --noEmit` y `npx vitest run` (frontend) verde.
- [ ] Al enviar un quiz/coding/evaluación, aparece el nudge de refuerzo según el puntaje.
- [ ] CLAUDE.md + matriz ISO actualizados.

Cierra el acompañamiento proactivo (Fases 1-4). Tras el merge, push de `main` a origin.
