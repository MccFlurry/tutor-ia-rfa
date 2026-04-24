# Docs · Tutor IA RFA — Entregables de tesis

Documentación formal para sustentación USAT. Cada archivo `.docx` debe incluir:

- **Portada:** título del proyecto, autor (Roger Alessandro Zavaleta Marcelo), asesora (Mg. Reyes Burgos, Karla), USAT · Escuela de Ingeniería de Sistemas y Computación, fecha.
- **Índice:** automático, numerado.
- **Secciones y subsecciones:** numeradas jerárquicamente.
- **Tipografía:** Times New Roman 11-12, interlineado 1.5.
- **Tablas y figuras:** leyenda numerada, referenciadas en texto.

## Tabla de entregables (12)

| # | Archivo | Sprint | Estado | Descripción |
|---|---------|--------|--------|-------------|
| 1 | `ERS.docx` | S1 | ✅ | 52 RF / 33 priorizados ISO/IEC 25010 |
| 2 | `modelos-STI/modelo-dominio.docx` | S1 | ✅ | Jerarquía módulo→tema→subtema |
| 3 | `modelos-STI/modelo-pedagogico.docx` | S1 | ✅ | Estrategias tutoría + adaptación por nivel |
| 4 | `modelos-STI/modelo-estudiante.docx` | S2 | ✅ | 5 atributos + ER + actualización |
| 5 | `modelos-STI/modelo-interaccion.docx` | S2 | ✅ | 4 modos uso + UML secuencia |
| 6 | `reporte-LLM.docx` | S2 | ✅ | Evaluación 3 LLM (qwen2.5/llama3/mistral) + 2 embeddings (mxbai/nomic) sobre 50 prompts + 20 queries · LLM juez automatizado · qwen2.5 Likert 4.85 / mxbai Recall@5 0.55 |
| 7 | `arquitectura.docx` | S3 | ⏳ | Diagramas C4 + justificación stack |
| 8 | `reporte-RAGAS.docx` | S4 | ✅ | Golden set 30 Q · baseline + v3 comparativos · subconjunto apto PASA faithfulness 0.768 ≥ 0.75 + relevancy 0.871 ≥ 0.70 · modelo qwen2.5:7b seleccionado |
| 9 | `matriz-trazabilidad-ISO25010.docx` | S7 | ⏳ | 33 RF × casos prueba + subcaracterísticas |
| 10 | `reporte-ISO25010.docx` | S7 | ⏳ | Cobertura + éxito + defectos + remediación |
| 11 | `reporte-SUS.docx` | S8 | ⏳ | Individual + promedio + desviación + percentil + cualitativo |
| 12 | `reporte-validacion-final.docx` | S8 | ⏳ | Consolidación ISO/IEC 25010 + SUS para Discusión |

## Referencias

- Cronograma: `1_03_Cronograma_de_actividades_Zavaleta.xlsx` (raíz)
- Sílabo oficial: `corpus/silabo-2025-I.md`
- CLAUDE.md · CLAUDE.original.md (raíz del repo)
