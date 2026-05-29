# Docs · Tutor IA RFA — Entregables de tesis

Documentación formal para sustentación USAT. Cada archivo `.docx` debe incluir:

- **Portada:** título del proyecto, autor (Roger Alessandro Zavaleta Marcelo), asesora (Mg. Reyes Burgos, Karla), USAT · Escuela de Ingeniería de Sistemas y Computación, fecha.
- **Índice:** automático, numerado.
- **Secciones y subsecciones:** numeradas jerárquicamente.
- **Tipografía:** Times New Roman 11-12, interlineado 1.5.
- **Tablas y figuras:** leyenda numerada, referenciadas en texto.

## Tabla de entregables (8 — mapeados a los 5 OE oficiales)

> Fuente única de verdad: `CLAUDE.md` §DOCS ENTREGABLES (v3.2). **SUS retirado** del
> alcance oficial (no figura en el mapeo). El reporte de usabilidad ya no es entregable.

| # | Archivo | Sprint | OE | Estado | Descripción |
|---|---------|--------|----|--------|-------------|
| 1 | `ERS.docx` *(archivo: `ESPECIFICACIÓN DE REQUISITOS DEL SOFTWARE.docx`)* | S1 | base | ✅ | 52 RF en 8 módulos; 33 priorizados ISO/IEC 25010 |
| 2 | `reporte-LLM.docx` + `reporte-OE1-metricas-oficiales.docx` | S2 | OE1 | ✅ | reporte-LLM = comparativa Sprint 2 (Likert/latencia/VRAM; nota: portada dice "OE2", etiqueta pre-v3.2). El anexo de métricas oficiales (2026-05-29) mide los 9 indicadores: **5/9 cumplen** (Accuracy 0.72, Likert 4.325, Recall@5 0.72, MRR@10 0.684, nDCG@10 0.686; ROUGE-L/BLEU/κ/STS por debajo → encuadre con asesora) |
| 3 | `arquitectura.docx` | S3 | OE3 | ✅ | Diagramas C4 + justificación stack + despliegue |
| 4 | `reporte-RAGAS.docx` | S4/S7 | OE2 | ✅ | Golden set 50 ítems · librería ragas oficial + juez independiente llama3.1 + rerank · precision 0.876 / recall 0.812 / faithfulness 0.706 / relevancy 0.707 / correctness 0.609 · **5/6 cumplen** (umbrales generación recalibrados, asesora aprobó 2026-05-29) |
| 5 | `matriz-trazabilidad-ISO25010.docx` | S7 | OE5 | ✅ | 33 RF × endpoint × casos de prueba + subcaracterísticas ISO |
| 6 | `reporte-ISO25010.docx` | S7 | OE5 | ✅ | Completitud ≥0.95 / corrección ≥0.90 / pertinencia ≥0.90 + defectos + remediación · falta dictamen ≥2 jueces |
| 7 | `reporte-rendimiento-academico.docx` | S8 | OE4 | ⏳ | Pretest/postest + **t de Student pareada (p<0.05)** + tamaño del efecto (bloqueado por piloto, 29-jun+) |
| 8 | `reporte-validacion-final.docx` | S8 | — | ⏳ | Consolidación OE2 + OE3 + OE4 + OE5 (bloqueado por OE4) |

> **Modelos STI** (`modelos-STI/modelo-{dominio,pedagogico,estudiante,interaccion}.docx`):
> documentación interna de diseño, **insumo de OE3**. Ya **no** son entregables formales
> (ningún OE los produce como resultado), pero los `.docx` se conservan en `modelos-STI/`.

## Referencias

- Cronograma: `1_03_Cronograma_de_actividades_Zavaleta_scrum.xlsx` (raíz)
- Sílabo oficial: `corpus/silabo-2025-I.md`
- CLAUDE.md (raíz) · `docs/CLAUDE-archive.md` (historial Fases 1–7.5 + S4)
- Justificación recalibración OE2: `docs/oe2-recalibracion-umbrales-propuesta.md`
