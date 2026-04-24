# Benchmark LLM + Embeddings — Sprint 2 CRISP-DM

Kit completo para ejecutar la evaluación comparativa de 3 LLMs y 2 modelos de embeddings que respalda el **reporte-LLM.docx** y evidencia el cumplimiento del **Objetivo Específico 2** de la tesis.

**Autor:** Roger Alessandro Zavaleta Marcelo
**Sprint:** 2 · CRISP-DM Business/Data Understanding
**Produce:** datos cuantitativos reales para generar `docs/reporte-LLM.docx`

---

## 🎯 Objetivo

Generar datos reales y defensibles académicamente para:

1. **Benchmark LLM** — comparar `qwen2.5:7b`, `llama3:8b` y `mistral:7b` en: latencia promedio, consumo de VRAM, tokens/segundo y calidad subjetiva sobre 50 prompts en español.
2. **Benchmark embeddings** — comparar `mxbai-embed-large` vs `nomic-embed-text` en: Recall@5, MRR y dimensionalidad sobre tu corpus real M1-M3.

---

## 📋 Protocolo completo (≈ 2 horas)

### Prerrequisitos

- Windows con Ollama corriendo nativamente (según tu CLAUDE.md)
- GPU con ≥8 GB VRAM (tu RTX 4070 16 GB es ideal)
- Python 3.11+ con `pip install httpx asyncpg`
- Tu base de datos PostgreSQL corriendo con el corpus indexado
- **Deja este kit en `docs/benchmarks/` dentro de tu repo** (al final Claude Code leerá los resultados desde ahí)

### Paso 1 — Descargar los modelos (≈ 15 min, una sola vez)

```bash
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama pull llama3:8b-instruct-q4_K_M
ollama pull mistral:7b-instruct-q4_K_M
ollama pull mxbai-embed-large
ollama pull nomic-embed-text
```

### Paso 2 — Ejecutar benchmark LLM (≈ 30-45 min)

```bash
cd docs/benchmarks
python run_llm_benchmark.py
```

**Qué hace:** corre los 50 prompts del `prompts_llm.json` sobre los 3 LLMs, mide latencia por consulta, tokens generados, tokens/segundo y VRAM ocupada. Guarda salvadas incrementales en `results/llm_benchmark.json`.

**Qué esperar en tu hardware:** ~3–8 s por respuesta en RTX 4070. Total ≈ 10–13 min por modelo × 3 = 30–45 min.

### Paso 3 — Calificar las respuestas (≈ 45-60 min)

```bash
python score_responses.py
```

**Qué hace:** te muestra cada respuesta (150 en total) y te pide calificar en 4 criterios con escala 1–5:

1. **Exactitud técnica** (¿es correcta respecto a Android/Kotlin?)
2. **Fluidez en español** (gramática, vocabulario natural)
3. **Ausencia de alucinaciones** (no inventa APIs ni clases)
4. **Pertinencia pedagógica** (tono didáctico, nivel IESTP)

**Importante:** puedes salir con `q` en cualquier momento; guarda el progreso. Puedes calificar en varias sesiones.

**Tiempo por respuesta:** ~20–30 segundos leyendo + calificando = ~60 min total.

**Tip metodológico:** el reporte documentará explícitamente que es evaluación mono-evaluador con rúbrica pre-registrada. Esto es honesto y defendible ante tu asesora Mg. Reyes Burgos. No infla, no miente.

### Paso 4 — Exportar el corpus (≈ 30 s)

```bash
# si tu DB no está en la URL por defecto, exporta la variable primero:
$env:DATABASE_URL="postgresql://user:pass@host:5432/tutor_db"   # PowerShell
# o
export DATABASE_URL="postgresql://user:pass@host:5432/tutor_db" # bash

python export_corpus.py
```

**Qué hace:** extrae el texto de todos tus chunks desde PostgreSQL a `results/corpus_chunks.json`. No exporta los vectores (los vamos a recalcular con ambos modelos).

### Paso 5 — Benchmark de embeddings (≈ 10-20 min)

```bash
python run_embeddings_benchmark.py
```

**Qué hace:** embebe todo tu corpus con cada modelo, luego evalúa las 20 queries del `golden_set_embeddings.json` calculando Recall@5 y MRR. Guarda en `results/embeddings_benchmark.json`.

**Un chunk se considera "relevante"** si contiene al menos 2 de las palabras clave esperadas (substring match, case-insensitive). Si tu corpus usa terminología distinta, edita las `expected_keywords` en el golden set.

### Paso 6 — Generar el reporte-LLM.docx con Claude Code

Con los tres archivos de resultados listos (`llm_benchmark.json`, `llm_scores.json`, `embeddings_benchmark.json`), abre Claude Code en tu repo y pégale el contenido de `CLAUDE_CODE_PROMPT.md`. Él leerá los datos y generará el documento final en `docs/reporte-LLM.docx` siguiendo el formato USAT.

---

## 📁 Estructura del kit

```
benchmarks/
├── README.md                      ← este archivo
├── CLAUDE_CODE_PROMPT.md          ← prompt final para Claude Code
├── prompts_llm.json               ← 50 prompts en español (M1-M3 + off-topic)
├── run_llm_benchmark.py           ← benchmark LLM (paso 2)
├── score_responses.py             ← calificación interactiva (paso 3)
├── export_corpus.py               ← exporta corpus desde pgvector (paso 4)
├── golden_set_embeddings.json     ← 20 queries con keywords esperadas
├── run_embeddings_benchmark.py    ← benchmark embeddings (paso 5)
└── results/
    ├── llm_benchmark.json         ← salida del paso 2
    ├── llm_scores.json            ← salida del paso 3
    ├── corpus_chunks.json         ← salida del paso 4
    └── embeddings_benchmark.json  ← salida del paso 5
```

---

## 🧪 Justificación metodológica (para la tesis)

### LLM Benchmark

- **50 prompts representativos en español** distribuidos en:
  - 12 M1 (Fundamentos Android)
  - 18 M2 (Lógica Kotlin / POO)
  - 15 M3 (Interfaces de usuario)
  - 5 off-topic (para evaluar capacidad de rechazo)
- **Tipos:** conceptual (discriminación teórica), code (generación/análisis de Kotlin) y application (escenarios prácticos).
- **Evaluación mono-evaluador con rúbrica Likert pre-registrada** sobre 4 criterios (exactitud, fluidez, alucinaciones, pedagogía). Limitación reconocida en el documento; trabajo futuro contempla evaluación multi-evaluador.
- **Parámetros de inferencia idénticos** para los 3 modelos: temperature=0.3, num_ctx=4096, num_predict=1024, mismo system prompt.
- **Warmup previo** a cada modelo para eliminar cold-start del tiempo medido.

### Embeddings Benchmark

- **Tarea:** recuperación semántica sobre el corpus real del curso (mismo que usará el sistema en producción).
- **Métrica principal:** Recall@5 — alineada con `top_k=5` del pipeline en producción baseline; interpretable ("el modelo recuperó un chunk relevante en los top-5 en X% de las queries").
- **Métrica secundaria:** MRR — captura calidad del ranking, no solo presencia.
- **20 queries representativas** cubriendo los 3 módulos. Limitación del tamaño de la muestra reconocida como trabajo futuro.

---

## ⚠ Consideraciones

- **Tiempo absoluto de las mediciones:** dependen del hardware. Los valores reportados son sobre Windows + RTX 4070 16 GB con Ollama nativo. Documentar el hardware en el reporte.
- **Variabilidad:** con `temperature=0.3` las respuestas no son deterministas. Si quieres máxima reproducibilidad, fija `seed` en el payload de `/api/generate`.
- **VRAM reportada:** proviene de `ollama /api/ps` (tamaño del modelo cargado). No incluye VRAM temporal durante la inferencia, que puede ser mayor.
- **Rechazo de off-topic:** los 5 prompts OFF evalúan si el system prompt frena correctamente. Cuentan en la media global; reporta también los promedios excluyendo OFF para transparencia.

---

## ✅ Checklist antes de correr

- [ ] Ollama activo: `curl http://localhost:11434/api/tags`
- [ ] 3 LLMs + 2 embeddings descargados: `ollama list`
- [ ] PostgreSQL corriendo con el corpus indexado
- [ ] `pip install httpx asyncpg`
- [ ] Kit copiado a `docs/benchmarks/` dentro de tu repo
