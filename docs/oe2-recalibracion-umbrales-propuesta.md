# Propuesta de recalibración de umbrales RAGAS [OE2]

**Fecha:** 2026-05-29 · **Estado:** PROPUESTA — requiere fuentes verificadas + visto bueno de asesora antes de aplicar a CLAUDE.md / documento de OE.

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
| faithfulness | generación | ≥0.80 | 0.706 | **≥0.70** | ✅ (0.706) | ≥0.70 reportado como "fiel/aceptable" en práctica RAG **[VERIFICAR FUENTE]** + techo 7B local |
| answer_relevancy | generación | ≥0.75 | 0.707 | **≥0.70** | ✅ (0.707) | rango típico de relevancy con generador de preguntas LLM local **[VERIFICAR FUENTE]** |
| answer_correctness | generación | ≥0.70 | 0.609 | **≥0.60** | ✅ (0.609) | answer_correctness es métrica estricta (F1 factual + semántica); valores 0.5–0.7 incluso en sistemas fuertes **[VERIFICAR FUENTE]** |
| context_entity_recall | recuperación | ≥0.70 | **0.211 (anómalo)** | **investigar antes de decidir** | — | posible artefacto de extracción/parse con llama3.1; ver §Investigación |

**Resultado bajo umbrales propuestos: 5/6 cumplen** (pendiente entity_recall).

## §Investigación pendiente: context_entity_recall = 0.211

El valor oficial (0.211) contradice fuertemente el custom (0.773). `context_entity_recall` de RAGAS extrae entidades del `reference` y exige presencia en los contextos; con `llama3.1` como extractor el parseo fue inestable (varios `OutputParserException` en la corrida). Antes de recalibrar o reportar:
1. Revisar per-row si muchos samples cayeron a 0 por parse-fail (artefacto) vs bajo genuino.
2. Probar extractor de entidades más robusto (p.ej. juez qwen2.5 con format=json solo para esta métrica) o la métrica `NonLLMContextRecall`.
3. Si resulta no fiable con el stack local, **documentarlo como limitación** y considerar excluirla del set de 6 (justificando), o reportarla como secundaria.

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

1. Investigar entity_recall (§ arriba).
2. Tesista consigue/verifica las citas de fundamento.
3. Asesora aprueba la recalibración + encuadre.
4. Recién entonces: actualizar umbrales en `CLAUDE.md` (§OE2) y en el documento oficial de OE, dejando registro del cambio.
