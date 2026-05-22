# Mapeo Corpus → Módulos STI (M1-M5)

Fuente: extracción primera página de cada `XX.02-Clase.pdf` en `corpus/semana-XX/sesion-YY/durante/`. Cruce con esquema 5 módulos de `CLAUDE.md` y schema `seed_db.py`.

Fecha: 2026-05-22 · Curso: Aplicaciones Móviles · IESTP RFA · 16 semanas · 31 clases efectivas.

## Tabla resumen

| Módulo | Semanas | Sesiones | Tema | Tags ingesta |
|--------|---------|----------|------|--------------|
| **M1 — Fundamentos** | 1–2 | 4 | Herramientas, entornos, lenguajes para apps móviles, Android vs iOS | `modulo:1`, `tema:fundamentos` |
| **M2 — Kotlin** | 3–8 | 12 | Variables, estructuras de control (condicionales + repetitivas), funciones, clases/objetos, POO avanzada | `modulo:2`, `tema:kotlin` |
| **M3 — UI / Interfaces** | 9–10 | 2–3 | Creación de interfaces gráficas, ciclo de vida Android, maquetación de vistas, Material Design, depuración inalámbrica | `modulo:3`, `tema:ui` |
| **M4 — Componentes / Datos** | 11–13 | 6 | Componentes avanzados (Spinner, RecyclerView, etc.), validación de entrada, consumo de API REST (Poke API) | `modulo:4`, `tema:componentes-datos` |
| **M5 — Avanzado / Despliegue** | 14–16 | 5 | Generación de APK, integración API, proyecto final del curso, examen práctico | `modulo:5`, `tema:despliegue` |

## Detalle por semana → módulo

| Sem | Sesión | Archivo clase | Tema (primera página) | Módulo |
|-----|--------|---------------|----------------------|--------|
| 01 | S1 | 01.02-Clase.pdf | Preparación de herramientas e interfaces de desarrollo | **M1** |
| 01 | S2 | 02.02-Clase.pdf | Preparación del entorno de trabajo | **M1** |
| 02 | S1 | 03.02-Clase.pdf | Herramientas para desarrollo de Apps móviles | **M1** |
| 02 | S2 | 04.02-Clase.pdf | Lenguajes para desarrollo de Apps móviles | **M1** |
| 03 | S1 | 05.02-Clase.pdf | Buenas prácticas, declaración de variables | **M2** |
| 03 | S2 (feriado) | 06.02 | Actividad práctica variables | **M2** |
| 04 | S1 | 07.02-Clase.pdf | Variables Kotlin (presentación) | **M2** |
| 04 | S2 | 08.02-Clase.pdf | Estructuras de control Kotlin | **M2** |
| 05 | S1 | 09.02-Clase.pdf | Estructuras de control repetitivas | **M2** |
| 05 | S2 | 10.02-Clase.pdf | Preparación entorno (refuerzo) | **M2** |
| 06 | S1 | 11.02-Clase.pdf | Implementación de funciones en Kotlin | **M2** |
| 06 | S2 | 12.02-Clase.pdf | Implementación de funciones en Kotlin (cont.) | **M2** |
| 07 | S1 | 13.01-Clase.pdf | Clases y objetos en Kotlin | **M2** |
| 07 | S2 | 14.01-Clase.pdf | Clases y objetos (cont.) | **M2** |
| 08 | S1 | 15.01-Clase.pdf | POO características avanzadas de las clases · Examen Capacidad 1 | **M2** |
| 08 | S2 | 16.02-Clase.pdf | Aplicación de clases en Kotlin | **M2** |
| 09 | S1 | 17.02-Clase.pdf | Creación de interfaces gráficas · ciclo de vida Android · Material Design | **M3** |
| 10 | S1 | 19.02-Clase.pdf | Maquetación de vistas en Android Studio · depuración inalámbrica | **M3** |
| 11 | S1 | 21.02-Clase.pdf | Uso de componentes avanzados | **M4** |
| 11 | S2 | 22.02-Clase.pdf | Implementación de validación de entrada de datos | **M4** |
| 12 | S1 | 23.02-Clase.pdf | Uso de componentes avanzados | **M4** |
| 12 | S2 | 24.02-Clase.pdf | Componentes avanzados · evaluación práctica | **M4** |
| 13 | S1 | 25.02-Clase.pdf | Uso de componentes avanzados | **M4** |
| 13 | S2 | — | Poke Api · consumo de API REST | **M4** |
| 14 | S1 | 27.02-Clase.pdf | Proyecto: Generar APK + Poke Api | **M5** |
| 14 | S2 | (suspensión) | — | — |
| 15 | S1 | 29.02-Clase.pdf | Componentes avanzados (cont.) · inicio proyecto final | **M5** |
| 15 | S2 | 30.02-Clase.pdf | Proyecto final del curso | **M5** |
| 16 | S1 | 31.02-Clase.pdf | Aplicación con componentes avanzados | **M5** |
| 16 | S2 | 30.02-Clase.pdf | Proyecto final + examen práctico | **M5** |

## Recursos transversales

| Carpeta | Contenido | Destino RAG |
|---------|-----------|-------------|
| `recursos-kotlin/` | `Curso_de_Kotlin_-_PPT.pdf`, `platzislides-kotlin*.pdf`, `slides-del-curso-de-kotlin-desde-cero.{pdf,pptx}`, `Sesión 05 ATI.pptx` | **M2 (refuerzo Kotlin)** |
| `recursos-kotlin/Esperamos que carge.docx` | Material complementario disperso | A revisar manualmente; probable M2 |
| `corpus/_raw/` | Drive originales (rollback) | **Excluir** de ingesta y de git |

## Notas sobre cobertura RAGAS / módulos seed

- `seed_db.py` actual define 5 módulos × 22 temas. Tras esta ingesta, los temas tendrán material fuente real, no solo Markdown sintético.
- Golden set RAGAS S4 cubre **M1–M3 (30 preguntas)**. Tras ingesta del corpus completo, considerar ampliar golden set para M4 y M5 antes de re-correr RAGAS (Sprint 8 pre-SUS).
- Archivos `Examen*`, `Banco*`, `EVALUACION*` → marcar metadata `is_assessment: true` para opcionalmente excluir de respuestas al estudiante (RAG puede filtrar fuentes sensibles).

## Próximos pasos

1. ✅ Mapeo módulo↔semana documentado.
2. ⏭ Cargar corpus a pgvector: `python backend/scripts/ingest_course_docs.py --root corpus/ --module-map docs/corpus-mapping.md`
   - Ajustar script para leer este mapping y propagar `metadata.modulo`, `metadata.semana`, `metadata.sesion`, `metadata.fase` (antes/durante/despues).
3. ⏭ Verificar `document_chunks` count por módulo (esperado ≥30 chunks/módulo).
4. ⏭ Re-correr RAGAS v4 con corpus completo (Sprint 8 pre-SUS).
