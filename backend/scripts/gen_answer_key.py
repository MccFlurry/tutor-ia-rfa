"""Genera la hoja de CLAVE DE CORRECCIÓN (respuestas 1-20) del instrumento OE4.
Documento docente para corregir rápido. Sin datos personales (versionable).

Uso (desde la raiz del repo):
    python backend/scripts/gen_answer_key.py
"""
from __future__ import annotations

import os
import pypandoc

OUT_MD = "docs/clave-correccion-OE4.md"
OUT_DOCX = "docs/clave-correccion-OE4.docx"

# (numero, letra correcta, texto de la alternativa correcta, modulo)
KEY = [
    (1, "c", "Android Studio", "M1"),
    (2, "a", "AndroidManifest.xml", "M1"),
    (3, "d", "Gradle", "M1"),
    (4, "b", "res", "M1"),
    (5, "b", "val", "M2"),
    (6, "c", "?.", "M2"),
    (7, "c", "data class", "M2"),
    (8, "c", "for", "M2"),
    (9, "c", "RecyclerView", "M3"),
    (10, "c", "XML", "M3"),
    (11, "b", "LinearLayout", "M3"),
    (12, "c", "setOnClickListener()", "M3"),
    (13, "c", "onCreate()", "M4"),
    (14, "a", "Intent", "M4"),
    (15, "c", "Room", "M4"),
    (16, "c", "Retrofit", "M4"),
    (17, "c", "Corrutinas", "M5"),
    (18, "b", "Android App Bundle (AAB)", "M5"),
    (19, "c", "ProGuard / R8", "M5"),
    (20, "c", "requestPermissions() en tiempo de ejecución", "M5"),
]


def main() -> None:
    quick = " ".join(f"{n}{letra}" for n, letra, _, _ in KEY)
    lines = [
        "# Clave de corrección — Prueba pretest / postest (OE4)",
        "",
        "**IESTP \"República Federal de Alemania\" — Aplicaciones Móviles (Kotlin/Android)**",
        "",
        "**Calificación:** 1 punto por respuesta correcta · total **0–20** · "
        "porcentaje = puntaje × 5 · nota vigesimal directa.",
        "",
        f"**Cadena rápida:** `{quick}`",
        "",
        "| # | Resp. | Alternativa correcta | Módulo |",
        "|---|:-----:|----------------------|:------:|",
    ]
    for n, letra, texto, mod in KEY:
        lines.append(f"| {n} | **{letra}** | {texto} | {mod} |")
    lines += [
        "",
        "---",
        "",
        "**Cómo corregir:** por cada hoja, cuenta las respuestas correctas según esta "
        "clave → ese número (0–20) es el puntaje. Anótalo en `roster-codigos.csv` "
        "(columna `pretest_0a20` o `postest_0a20` según el momento marcado en la hoja).",
        "",
        "*Documento docente — no entregar a los estudiantes.*",
    ]
    md = "\n".join(lines)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    pypandoc.convert_text(md, "docx", format="gfm", outputfile=OUT_DOCX)
    print(f"Clave generada -> {OUT_DOCX} ({os.path.getsize(OUT_DOCX)} bytes)")


if __name__ == "__main__":
    main()
