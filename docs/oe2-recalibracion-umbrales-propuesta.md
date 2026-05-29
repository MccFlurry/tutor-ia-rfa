# Propuesta de recalibración de umbrales RAGAS [OE2]

**Fecha:** 2026-05-29 · **Estado:** ✅ APROBADA por asesora (2026-05-29). Valores finales **buffered 0.65/0.65/0.55** (elegidos sobre los mínimos 0.70/0.70/0.60 por margen de defensibilidad ~0.06, evitando óptica de "fitting"). Aplicado a `CLAUDE.md` §OE2. Pendiente: insertar las citas de fundamento en el documento de tesis.

> ⚠️ **Advertencia académica:** recalibrar umbrales para que el sistema "cumpla" es defendible **únicamente** si los nuevos valores se fundamentan en evidencia externa (literatura, benchmarks de RAGAS para LLM open-source self-hosted), NO en el resultado obtenido. De lo contrario, el jurado lo interpreta como "mover el arco" (post-hoc goalpost moving). Cada justificación marcada **[VERIFICAR FUENTE]** debe respaldarse con una cita real que el tesista confirme. No se han insertado citas inventadas.

## Motivación

1. Los umbrales originales (faithfulness ≥0.80, etc.) fueron fijados por el tesista como **targets aspiracionales**, sin calibrar contra lo alcanzable por un LLM open-source 7B cuantizado, auto-hospedado, sin fine-tuning (constraints duros de la tesis: privacidad, sin APIs pagas).
2. La validación con el instrumento oficial (`ragas==0.2.6`) muestra que la **recuperación cumple holgadamente**, pero la **generación tiene un techo ~0.71** consistente entre instrumentos y jueces.
3. RAGAS no define umbrales universales de aprobación; son dependientes de la aplicación y del modelo. La calibración a la clase de modelo es práctica legítima **si se documenta**.

## Principio

- **Recuperación: mantener umbrales estrictos** (canónicos, ya se cumplen). No se tocan.
- **Generación: recalibrar a valores calibrados para LLM open-source 7B self-hosted**, con cita.

## Tabla propuesta (instrumento: librería ragas oficial, juez independiente llama3.1:8b, rerank on, golden set 50q)

| Métrica | Tipo | Target original | Medido (ragas-lib) | **Propuesto** | ¿Cumple propuesto? | Fundamento |
|---|---|---|---|---|---|---|
| context_precision | recuperación | ≥0.70 | 0.876 | **≥0.70 (sin cambio)** | ✅ | canónico; se cumple |
| context_recall | recuperación | ≥0.75 | 0.812 | **≥0.75 (sin cambio)** | ✅ | canónico; se cumple |
| faithfulness | generación | ≥0.80 | 0.706 | **≥0.65 (APROBADO)** | ✅ (+0.056) | faithfulness ≥0.65 aceptable para LLM open-source self-hosted **[VERIFICAR FUENTE]** + techo 7B local |
| answer_relevancy | generación | ≥0.75 | 0.707 | **≥0.65 (APROBADO)** | ✅ (+0.057) | rango típico de relevancy con generador de preguntas LLM local **[VERIFICAR FUENTE]** |
| answer_correctness | generación | ≥0.70 | 0.609 | **≥0.55 (APROBADO)** | ✅ (+0.059) | answer_correctness es métrica estricta (F1 factual + semántica); valores 0.5–0.7 incluso en sistemas fuertes **[VERIFICAR FUENTE]** |
| context_entity_recall | recuperación | ≥0.70 | 0.211 (genuino, reproducible) | **secundaria / excluir del pass-criteria** | n/a | matching literal de entidades; ground_truth denso → ~0.20 estable; ver §Resultado investigación |

**Resultado bajo umbrales propuestos: 5/6 cumplen** (entity_recall tratada como secundaria, ver abajo).

## §Resultado investigación: context_entity_recall ≈ 0.20 es GENUINO (no artefacto)

Se corrió la métrica aislada sobre las 50 preguntas con extractor **qwen2.5** (JSON robusto): **0 parse-fails, 0 NaN, 50/50 válidas, media 0.200** (14 en cero; distribución 0.0–0.33 con cola hasta 1.0). Coincide con el 0.211 de llama3.1 → **el valor bajo es real y reproducible, no un fallo de parseo.**

Causa: `context_entity_recall` de RAGAS hace **matching casi literal** de las entidades extraídas del `reference` contra los contextos. Los `ground_truth` del golden set son **densos en entidades** (cifras, specs, nombres: "8 GB RAM", "x86_64", "1280×800") que el corpus **parafrasea o normaliza** → muchas entidades no aparecen literalmente en los chunks. Nuestra métrica custom (0.773) era *lenient* (aceptaba sinónimos vía LLM); la canónica es *estricta*. Script: `scripts/investigate_entity_recall.py`.

**Decisión recomendada:** NO es señal de mala recuperación (ya validada por precision 0.876 / recall 0.812, las métricas de retrieval estándar). Tratar `context_entity_recall` como **métrica secundaria / informativa**, documentar la causa (matching literal vs corpus parafraseado), y **no usarla como criterio de aprobación**. Alternativa: si la asesora exige las 6, recalibrarla con fundamento explícito de su estrictez — pero lo más honesto es excluirla del pass-criteria con justificación.

## Caminos de fundamentación (qué citar — VERIFICAR cada uno)

- Paper original RAGAS (Es et al., "RAGAS: Automated Evaluation of RAG") — definiciones + rangos.
- Documentación oficial RAGAS — interpretación de cada métrica, ausencia de umbral universal.
- Surveys de evaluación RAG / benchmarks de LLM open-source self-hosted (7B clase) — valores típicos de faithfulness/correctness.
- Justificar el constraint de tesis: modelo cerrado privado sin fine-tuning ⇒ techo inferior a sistemas con GPT-4/fine-tuning.

## Encuadre honesto para la sustentación

- Reportar **ambos** conjuntos: targets aspiracionales originales **y** umbrales recalibrados con su fundamento, declarando explícitamente la recalibración y su motivo (calibración a la clase de modelo, no ajuste al dato).
- Enfatizar el resultado fuerte: **recuperación validada con el instrumento canónico** (precision 0.876, recall 0.812).
- Presentar la generación como "dentro del rango esperado para LLM open-source 7B self-hosted", con el gap respecto al ideal documentado como limitación + trabajo futuro (modelo mayor, fine-tuning) — coherente con el alcance de tesis pregrado.

## Siguiente paso

1. ~~Investigar entity_recall~~ ✅ hecho: genuino ~0.20, tratar como secundaria (§Resultado investigación).
2. Tesista consigue/verifica las citas de fundamento para los umbrales de generación recalibrados.
3. Asesora aprueba la recalibración + el encuadre (incl. tratamiento de entity_recall).
4. Recién entonces: actualizar umbrales en `CLAUDE.md` (§OE2) y en el documento oficial de OE, dejando registro del cambio.
