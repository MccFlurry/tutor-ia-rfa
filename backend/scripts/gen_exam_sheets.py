"""Genera las hojas de examen pretest/postest, una por estudiante (version alumno,
sin respuestas), a partir de docs/roster-codigos.csv. Salida imprimible en .docx.

Las hojas llevan el nombre real del estudiante -> PII -> NO versionar (gitignored).

Uso (desde la raiz del repo):
    python backend/scripts/gen_exam_sheets.py
"""
from __future__ import annotations

import csv
import os

import pypandoc

ROSTER = "docs/roster-codigos.csv"
OUT_MD = "docs/examen-pretest-postest-hojas.md"
OUT_DOCX = "docs/examen-pretest-postest-hojas.docx"

MODULES = [
    ("Módulo 1 — Fundamentos y entorno", [
        ("¿Cuál es el IDE oficial para el desarrollo de aplicaciones Android?",
         ["Eclipse", "NetBeans", "Android Studio", "Visual Studio"]),
        ("¿Qué archivo declara los componentes, permisos y la configuración general de la app?",
         ["AndroidManifest.xml", "build.gradle", "strings.xml", "MainActivity.kt"]),
        ("¿Qué sistema de construcción (build) utiliza Android de forma predeterminada?",
         ["Maven", "Ant", "Make", "Gradle"]),
        ("¿En qué carpeta del proyecto se ubican los recursos (layouts, strings, imágenes)?",
         ["src", "res", "assets", "lib"]),
    ]),
    ("Módulo 2 — Lógica de programación en Kotlin", [
        ("¿Qué palabra clave declara una variable inmutable (solo lectura) en Kotlin?",
         ["var", "val", "let", "const fun"]),
        ("¿Cuál es el operador de llamada segura que evita NullPointerException?",
         ["!!", "?:", "?.", "=="]),
        ("¿Qué tipo de clase genera automáticamente equals(), hashCode() y toString()?",
         ["sealed class", "object", "data class", "abstract class"]),
        ("¿Qué estructura de control recorre cada elemento de una colección?",
         ["when", "try", "for", "object"]),
    ]),
    ("Módulo 3 — Interfaces de usuario (UI)", [
        ("¿Qué componente muestra listas largas de forma eficiente reciclando vistas?",
         ["ListView", "ScrollView", "RecyclerView", "LinearLayout"]),
        ("En la vista clásica de Android, ¿en qué lenguaje se definen los layouts?",
         ["JSON", "YAML", "XML", "HTML"]),
        ("¿Qué ViewGroup organiza los elementos en una sola fila o columna?",
         ["ConstraintLayout", "LinearLayout", "FrameLayout", "TableLayout"]),
        ("¿Qué método registra la acción a ejecutar cuando se pulsa un botón?",
         ["onCreate()", "findViewById()", "setOnClickListener()", "onResume()"]),
    ]),
    ("Módulo 4 — Componentes Android y gestión de datos", [
        ("¿Qué método del ciclo de vida de una Activity se invoca al crearse?",
         ["onStart()", "onPause()", "onCreate()", "onDestroy()"]),
        ("¿Qué objeto se usa para comunicar componentes o abrir otra Activity?",
         ["Intent", "Bundle", "Service", "Fragment"]),
        ("¿Qué biblioteca recomendada por Android envuelve SQLite con un ORM?",
         ["Realm", "Retrofit", "Room", "Gson"]),
        ("¿Qué biblioteca se usa comúnmente para consumir APIs REST en Android?",
         ["Room", "Glide", "Retrofit", "Dagger"]),
    ]),
    ("Módulo 5 — Funcionalidades avanzadas y despliegue", [
        ("¿Qué mecanismo de Kotlin ejecuta tareas asíncronas sin bloquear el hilo principal?",
         ["Thread manual", "bucles while", "Corrutinas", "for anidados"]),
        ("¿Qué formato de paquete recomienda Google Play para la distribución?",
         ["APK clásico", "Android App Bundle (AAB)", "JAR", "ZIP"]),
        ("¿Qué herramienta ofusca y optimiza el código en compilaciones release?",
         ["Logcat", "Lint", "ProGuard / R8", "Gradle"]),
        ("En Android 6+ (API 23+), ¿cómo se solicitan los permisos peligrosos?",
         ["Solo en el Manifest", "No se solicitan",
          "En tiempo de ejecución con requestPermissions()", "En strings.xml"]),
    ]),
]
LETTERS = ["a", "b", "c", "d"]
PAGEBREAK = '\n\n```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```\n\n'


def sheet(codigo: str, seccion: str, nombre: str) -> str:
    s = [
        '**IESTP "REPÚBLICA FEDERAL DE ALEMANIA" — Aplicaciones Móviles**',
        "",
        "### Prueba de conocimientos (Kotlin / Android)",
        "",
        f"**Estudiante:** {nombre}  ",
        f"**Código:** {codigo}    **Sección:** {seccion}    **Fecha:** ____ / ____ / 2026  ",
        "**Momento:**  ☐ Pretest    ☐ Postest",
        "",
        "*Instrucciones: marca UNA sola alternativa por pregunta. 20 preguntas, 1 punto cada una.*",
        "",
    ]
    n = 0
    for mod_title, qs in MODULES:
        s += [f"**{mod_title}**", ""]
        for q, opts in qs:
            n += 1
            s.append(f"**{n}.** {q}  ")
            s.append("    ".join(f"{LETTERS[i]}) {opt}" for i, opt in enumerate(opts)) + "  ")
            s.append("")
    s += ["---", "", "*Uso docente — Puntaje:* **____ / 20**"]
    return "\n".join(s)


def main() -> None:
    roster = list(csv.DictReader(open(ROSTER, encoding="utf-8-sig")))
    parts = []
    for i, r in enumerate(roster):
        if i > 0:
            parts.append(PAGEBREAK)
        parts.append(sheet(r["codigo"], r["seccion"], r["nombre"]))
    md = "\n".join(parts)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    pypandoc.convert_text(md, "docx", format="markdown", outputfile=OUT_DOCX)
    print(f"Hojas generadas: {len(roster)}")
    print(f"MD:   {OUT_MD}")
    print(f"DOCX: {OUT_DOCX} ({os.path.getsize(OUT_DOCX)} bytes)")


if __name__ == "__main__":
    main()
