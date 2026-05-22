# Corpus — Aplicaciones Móviles · IESTP RFA

Material docente fuente para el pipeline RAG del tutor IA. **No se versiona en git** (≈1.1 GB de PDF/DOCX/PPTX/TXT). Esta carpeta vive sólo en clones locales y se reconstruye desde el Drive del curso.

## Estructura esperada

```
corpus/
├── README.md            (este archivo · único versionado)
├── _raw/                Drive export originales (rollback) — opcional
├── recursos-kotlin/     PDFs/PPTX sueltos Kotlin (refuerzo M2)
└── semana-XX/           XX ∈ {01..16}
    ├── sesion-01/
    │   ├── antes/       material pre-clase
    │   ├── durante/     PDF/PPTX clase + apuntes docente
    │   └── despues/     material post-clase
    └── sesion-02/...
```

## Origen

Carpeta Drive del curso (acceso restringido docente IESTP RFA):
`https://drive.google.com/drive/folders/1f4VOgr6tfp_-4XJsvPReaKL7QWldfNVM`

Descarga Google Takeout → 2 ZIPs `APLICACIONES MOVILES-...001/002` que se mergean según el script de reorganización aplicado el 2026-05-22.

## Reglas de limpieza aplicadas (2026-05-22)

Eliminado (off-topic / clutter):
- `gen APK/` — 1.2 GB de videos MP4 sobre KivyMD/Python (no Kotlin)
- `Notas/` — proyecto Android Studio binario + cache Gradle
- `Pirata cris/`, `Sonya Moviles/`, `pirata pollito/` — clutter personal

Conservado: 16 semanas × 1-2 sesiones × {antes,durante,despues} + 7 PDFs/PPTX Kotlin de refuerzo.

## Mapeo semana → módulo

Detalle en `docs/corpus-mapping.md`. Resumen:

| Módulo | Semanas | Tema |
|--------|---------|------|
| M1 Fundamentos | 01-02 | Herramientas, entornos, Android vs iOS |
| M2 Kotlin | 03-08 | Variables, control, funciones, POO |
| M3 UI | 09-10 | Interfaces, ciclo vida, Material Design |
| M4 Componentes/Datos | 11-13 | Componentes avanzados, validación, Retrofit/PokeAPI |
| M5 Avanzado/Despliegue | 14-16 | APK firmado, proyecto final |

## Ingesta a pgvector

```bash
docker exec tutor_backend python scripts/ingest_corpus.py --reset
```

Esto walk `corpus/`, parsea PDF/DOCX/PPTX/TXT/MD, genera embeddings con `mxbai-embed-large` y guarda chunks en `document_chunks` con metadata `{module_id, semana, sesion, fase, filename}`.

Resultado esperado (ingesta 2026-05-22):
- 152 documentos
- 3,381 chunks
- Distribución: M1=181 · M2=706 · M3=596 · M4=1065 · M5=833

## Volumen

| Carpeta | Tamaño aproximado |
|---------|-------------------|
| `_raw/` | 530 MB (Drive originales sin junk) |
| `semana-01..16/` | ~530 MB |
| `recursos-kotlin/` | 16 MB |
| **Total** | **~1.1 GB** |

Por eso queda fuera de git: ver `.gitignore` (`corpus/*` excluido, sólo este README versionado).
