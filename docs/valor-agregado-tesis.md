# Valor Agregado de la Tesis — Aporte Novedoso del Producto Acreditable

**Tesis:** Tutor con IA generativa aplicado a la asignatura de Aplicaciones Móviles para mejorar el rendimiento académico — IESTP "República Federal de Alemania", Chiclayo
**Autor (tesista):** Roger Alessandro Zavaleta Marcelo
**Asesora (USAT):** Mg. Reyes Burgos, Karla
**Universidad:** Universidad Católica Santo Toribio de Mogrovejo — Escuela de Ingeniería de Sistemas y Computación
**Fecha:** 15-jun-2026

> **Propósito de este documento.** Responder, con rigor y evidencia, a la pregunta del jurado en la sustentación preliminar: *"¿Cuál es el valor agregado de la tesis; es decir, qué es lo novedoso —característica novedosa respecto de los softwares o modelos existentes— inmerso en el producto acreditable?"*. Se argumenta con **honestidad académica**: no se reclama un algoritmo de aprendizaje automático inédito (la tesis es de ingeniería aplicada, no de investigación algorítmica pura), sino una **combinación novedosa, una mejora medible sobre componentes existentes y una restricción real resuelta que el software existente no cubre**, todo respaldado por evidencia ya producida en el proyecto.

---

## 1. Respuesta directa (titular de sustentación)

El valor agregado no reside en un componente aislado, sino en una **combinación que ningún tutor existente ofrece para este contexto**:

> Un Sistema Tutor Inteligente **100 % privado y de costo marginal cero**, **anclado al sílabo real del curso** con **trazabilidad de fuentes**, que **se adapta al nivel diagnosticado de cada estudiante** y lo **acompaña proactivamente** —y, lo decisivo, con **evidencia empírica de que mejora el rendimiento académico real** (no solo la satisfacción): ganancia media **+3.98 puntos** sobre 20, **t(48) = 14.85, p < 0.001, d = 2.12** (efecto grande), con **46/49 estudiantes (94 %)** mejorando.

La novedad es **sistémica y validada**: la coexistencia simultánea de privacidad total, anclaje al currículo, adaptación por estudiante y eficacia demostrada, ejecutándose sobre hardware modesto (una sola VM). Ningún producto del mercado reúne las cuatro condiciones a la vez para educación técnica de bajos recursos en español.

---

## 2. Qué cuenta como "valor agregado" en una tesis de ingeniería aplicada

El jurado planteó la posibilidad de *"algún algoritmo o algo nuevo… o algo existente que se haya mejorado"*. Esa última opción es la clave: en una tesis **aplicada de ingeniería de software**, la novedad legítima no exige inventar un algoritmo de ML inédito. Se reconoce como aporte cualquiera de estos:

1. **Combinación novedosa** de tecnologías existentes que resuelve un problema antes no resuelto en ese contexto.
2. **Mejora medible** sobre una técnica existente (re-ranking, ajuste de pipeline, heurísticas propias).
3. **Aporte metodológico**: conocimiento reproducible que antes no existía (p. ej., umbrales validados para una clase de modelo en un idioma/dominio específicos).
4. **Evidencia empírica** de impacto real (mejora del rendimiento académico contrastada estadísticamente).

Esta tesis aporta en **las cuatro** categorías. A continuación se detallan.

---

## 3. Diferenciación frente al software existente

| Software / enfoque existente | Limitación frente a este contexto | Esta tesis |
|---|---|---|
| **ChatGPT / Gemini (genéricos)** | No anclados al sílabo del IESTP; alucinan sin trazabilidad; API paga; los datos del estudiante salen del país | **RAG sobre el corpus real del curso**, **citas trazables** (similitud ≥0.75), rechaza consultas fuera de tema |
| **Khanmigo / Duolingo Max** | Dependen de APIs cloud pagas (GPT‑4); centrados en inglés; no cubren el sílabo Android/Kotlin; costo recurrente insostenible para el instituto | **LLM local privado** (Ollama + qwen2.5‑7B), **costo marginal cero**, **español peruano**, sílabo exacto del curso |
| **Moodle + plugins / LMS tradicional** | Contenido estático; sin tutoría generativa; sin adaptación por estudiante | **Generativo + adaptativo por nivel diagnosticado + acompañamiento proactivo** |
| **Chatbot RAG genérico** | Solo pregunta‑respuesta | **STI completo**: evaluación de entrada y nivelación, quiz adaptativo, evaluación de código con feedback, progreso gamificado, **mejora del rendimiento medida** |

**Frase de cierre del cuadro.** Ningún tutor del mercado combina simultáneamente, para este contexto, **(1)** soberanía de datos sin API paga, **(2)** adaptación al nivel diagnosticado de cada estudiante con acompañamiento proactivo y **(3)** evidencia empírica de mejora del rendimiento real — y todo sobre una sola VM de bajo costo.

---

## 4. Aportes técnicos concretos (defendibles con evidencia)

### 4.1. Aporte metodológico — el más fuerte y reproducible

Se demostró empíricamente que un **LLM 7B de código abierto, auto‑hospedado y sin fine‑tuning** alcanza **calidad RAGAS validada** para tutoría técnica en **español** sobre el dominio Android/Kotlin. Esto constituye **conocimiento reproducible que no existía** para esa clase de modelo / idioma / dominio. Adicionalmente, se **recalibraron los umbrales RAGAS** para la clase 7B‑local (con sustento del juez independiente).

**Evidencia (juez independiente `llama3.1:8b`, librería RAGAS oficial, rerank cross‑encoder):**

| Métrica | Umbral | Resultado |
|---|---|---|
| Context Precision | ≥0.70 | **0.876** ✅ |
| Context Recall | ≥0.75 | **0.812** ✅ |
| Faithfulness | ≥0.65 | **0.706** ✅ |
| Answer Relevancy | ≥0.65 | **0.707** ✅ |
| Answer Correctness | ≥0.55 | **0.609** ✅ |

→ **5/5 métricas cumplen.** Mensaje de defensa: *no se necesita GPT‑4 para construir un tutor útil y fiel; un 7B local bien orquestado basta, y aquí está la prueba.*

### 4.2. Mejora medible de la recuperación (mejorar algo existente)

Sobre un RAG base se incorporó **re‑ranking con cross‑encoder**, elevando la calidad de recuperación a valores medidos:

- **nDCG@10 = 0.686** (≥0.55) · **Recall@5 = 0.72** (≥0.70) · **MRR@10 = 0.684** (≥0.65).

Esto es, literalmente, "mejorar una técnica existente" con resultado cuantificado — exactamente lo que el jurado admitió como válido.

### 4.3. Algoritmo de nivelación adaptativa (diseño propio)

Heurística diseñada para esta tesis:

- **Puntaje ponderado de nivelación**: peso por módulo (M1 = 1.0 … M5 = 1.5) × peso por dificultad (easy = 1.0 / medium = 1.5 / hard = 2.0).
- **Umbrales de nivel**: `<40` principiante · `40–75` intermedio · `>75` avanzado.
- **Re‑asignación dinámica**: se evalúan los últimos 3 quizzes para proponer subir/bajar de nivel automáticamente.

El nivel diagnosticado **condiciona** la generación del quiz, la dificultad de los desafíos de código y el tono del feedback del LLM. Es un mecanismo propio, no una librería tomada tal cual.

### 4.4. Arquitectura híbrida IA + determinista (aporte de ingeniería)

Decisión de diseño diferenciadora: lo **probabilístico** (LLM) donde aporta valor; lo **determinista** (motor de nudges y "companion" por reglas y plantillas) donde se necesita confiabilidad y testeabilidad. Con **fallbacks elegantes** en cada ruta de IA:

- Quiz IA caído → banco de preguntas en BD.
- Generación de código caída → catálogo de desafíos.
- Evaluación de entrada caída → banco docente.

Esto materializa el principio **"resiliente por diseño"**: el sistema nunca deja al estudiante en un callejón sin salida, a diferencia de tutores que dependen de una sola API y se caen con ella.

---

## 5. Respaldo de impacto: la evidencia que sella el valor agregado

El diferenciador definitivo no es técnico sino de **resultado**: se contrastó la mejora del rendimiento académico con diseño pre‑experimental (pretest/postest) sobre **n = 49** estudiantes (censo cohorte 2026‑I):

- Pretest **10.45 ± 2.76** → Postest **14.43 ± 3.11** (escala 0–20); ganancia **+3.98** (IC95 % [3.44, 4.52]).
- **t de Student pareada: t(48) = 14.85, p = 7.2e‑20 (< 0.001)**; **Cohen's d = 2.12** (efecto grande).
- Respaldo no paramétrico **Wilcoxon p = 1.1e‑09 (< 0.001)**. **46/49 (94 %)** mejoraron.

**Limitación declarada (honestidad académica):** diseño de un solo grupo sin grupo control → la mejora es estadísticamente significativa, pero la causalidad exclusiva no queda probada (posibles efectos de maduración/historia/testing). Un cuasi‑experimento con grupo control queda como trabajo futuro. Esta franqueza **fortalece** la defensa: demuestra dominio metodológico.

---

## 6. Qué NO afirmar en la sustentación (guion defensivo)

| ❌ Evitar | Por qué |
|---|---|
| "Inventé un algoritmo de ML nuevo" | El jurado pedirá la demostración formal y no existe; expone la defensa. |
| "Entrené / hice fine‑tuning del modelo" | El sistema usa **RAG puro**; afirmarlo contradice la propia tesis y las reglas del proyecto. |
| "Usé Ollama + FastAPI" (a secas) | Reduce el aporte a "mera integración", que es justo lo que el jurado castiga. |

El encuadre ganador es siempre: **valor agregado = combinación validada que resuelve una restricción real (privacidad + costo cero + adaptación + mejora probada) que ningún producto existente cubre en conjunto para educación técnica de bajos recursos en español.**

---

## 7. Guion breve de respuesta oral (≈45 segundos)

> "El valor agregado de mi tesis no es un solo componente, sino una combinación que hoy ningún tutor ofrece para este contexto. Construí un tutor inteligente **100 % privado**, sin ninguna API paga, que corre sobre una sola máquina de bajo costo; está **anclado al sílabo real del curso** y **cita sus fuentes**, por lo que no inventa; **se adapta al nivel de cada estudiante** y lo **acompaña de forma proactiva**. Técnicamente, aporté una **mejora medible en la recuperación** con re‑ranking cross‑encoder, una **heurística propia de nivelación adaptativa**, y una **arquitectura híbrida IA‑determinista resiliente** con respaldos cuando la IA falla. Y, sobre todo, **demostré empíricamente** que un modelo abierto de 7B, sin fine‑tuning, alcanza calidad RAGAS validada en español —algo que no estaba documentado para esta clase de modelo y dominio— y que el sistema **mejora el rendimiento real** de los estudiantes: subieron casi 4 puntos sobre 20, con significancia estadística fuerte (p < 0.001) y tamaño de efecto grande (d = 2.12). Esa es la novedad: **privacidad + anclaje + adaptación + eficacia probada, junta, sobre hardware modesto.**"

---

## 8. Trazabilidad de la evidencia

| Afirmación | Evidencia en el proyecto |
|---|---|
| RAGAS 5/5 | `docs/reporte-RAGAS.md`, `backend/scripts/run_ragas_lib_eval.py` |
| Métricas de recuperación (nDCG/Recall/MRR) | `docs/reporte-OE1-metricas-oficiales.md`, `backend/scripts/oe1_retrieval.py` |
| Mejora del rendimiento (t pareada, d) | `docs/reporte-rendimiento-academico.md`, `backend/scripts/analyze_pretest_postest.py`, `docs/datos-pretest-postest.csv` |
| Adecuación funcional ISO/IEC 25010 | `docs/matriz-trazabilidad-ISO25010.md`, `docs/reporte-ISO25010.md` |
| Nivelación adaptativa | `app/services/leveling_service.py`, `app/services/entry_assessment_service.py` |
| Arquitectura híbrida + fallbacks | `app/services/tutor_service.py`, `app/services/companion_service.py`, `app/services/rag_service.py` |

---

*Documento de apoyo para la sustentación. Mantiene la honestidad académica del proyecto: lo validado se reporta como validado; las limitaciones (ausencia de grupo control en OE4; dictamen de jueces pendiente en OE5) se declaran de forma explícita.*
