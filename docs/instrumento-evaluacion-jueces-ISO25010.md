# Instrumento de Evaluación por Juicio de Expertos — Adecuación Funcional ISO/IEC 25010:2023 [OE5]

**Tesis:** Tutor con IA generativa para Aplicaciones Móviles — IESTP "República Federal de Alemania" (Chiclayo)
**Autor (tesista):** Roger Alessandro Zavaleta Marcelo · **Asesora:** Mg. Reyes Burgos, Karla (USAT)
**Objetivo asociado:** OE5 — *Validar la adecuación funcional del sistema conforme a ISO/IEC 25010:2023.*
**Norma de medición:** ISO/IEC 25023:2016 (métricas de calidad del producto software).

> **Estado (04-jun-2026):** Instrumento **diseñado y listo para aplicación**. Las columnas de evaluación están **en blanco**: las completa cada juez experto. Las métricas finales (X) se consolidan **únicamente con los dictámenes reales de ≥2 jueces** — no se reportan valores aquí hasta recibirlos. Las métricas de **completitud** y **corrección** cuentan además con evidencia objetiva automatizada (396 tests, 0 fallos) que se anexa como respaldo a la evaluación.

---

## 1. Propósito

Recoger el juicio independiente de **≥2 expertos** sobre la **adecuación funcional** (Functional Suitability, ISO/IEC 25010:2023 §4.1) del sistema, en sus tres subcaracterísticas:

| Subcaracterística | Definición (ISO/IEC 25010:2023) | Métrica (ISO/IEC 25023:2016) | Umbral OE5 |
|---|---|---|---|
| **Completitud funcional** | Grado en que el conjunto de funciones cubre todas las tareas y objetivos especificados del usuario. | X = A / B | **≥ 0.95** |
| **Corrección funcional** | Grado en que el sistema entrega resultados correctos con la precisión necesaria. | X = 1 − (A / B) | **≥ 0.90** |
| **Pertinencia funcional** | Grado en que las funciones facilitan la realización de las tareas y objetivos especificados. | X = A / B | **≥ 0.90** |

Donde, sobre el conjunto de **33 requisitos funcionales (RF) priorizados** del ERS:
- **Completitud:** A = nº de RF presentes y operativos; B = 33 (RF especificados).
- **Corrección:** A = nº de RF que producen resultados incorrectos; B = 33 (RF evaluados).
- **Pertinencia:** A = nº de RF juzgados pertinentes (adecuados a la tarea); B = 33 (RF evaluados).

Complementariamente, sobre la dimensión subjetiva (pertinencia) se calcula la **V de Aiken** (validez de contenido) a partir de la escala Likert 1–4; se aceptan ítems con **V ≥ 0.80**.

---

## 2. Objeto de evaluación

Sistema **Tutor IA RFA** desplegado y operativo (backend FastAPI + frontend React + RAG privado sobre Ollama). Alcance: los **33 RF priorizados** del ERS (de 52 RF totales). El recorte corresponde al flujo del piloto: *registro → estudiar → autoevaluación → consultar tutor IA → seguir progreso → logros*, más la gestión administrativa del corpus, usuarios y contenido.

### Evidencia puesta a disposición del juez
- `docs/matriz-trazabilidad-ISO25010.md` — matriz RF ↔ endpoint ↔ caso de prueba.
- `docs/reporte-ISO25010.md` — reporte de validación funcional.
- Acceso al sistema en producción (`https://tutor-ia-rfa.web.app`) con cuenta de prueba.
- Suite automatizada de respaldo: **396 casos de prueba, 100 % aprobados**, cobertura de código **88 %** (corte 04-jun-2026).

---

## 3. Datos del juez experto

*(A completar por el evaluador.)*

| Campo | Dato |
|---|---|
| Nombres y apellidos | __________________________________________ |
| Grado académico | ☐ Bachiller ☐ Título ☐ Magíster ☐ Doctor |
| Profesión / especialidad | __________________________________________ |
| Años de experiencia profesional | __________ |
| Cargo / institución | __________________________________________ |
| Fecha de evaluación | _____ / _____ / 2026 |

---

## 4. Instrucciones

1. Revise cada RF apoyándose en la matriz de trazabilidad y, de ser posible, ejercitándolo en el sistema en producción.
2. Para cada RF, marque:
   - **Completa** (¿la función está presente y cubre la tarea especificada?): **Sí = 1 / No = 0**.
   - **Correcta** (¿produce el resultado esperado con la precisión necesaria?): **Sí = 1 / No = 0**.
   - **Pertinencia** (¿la función facilita y es adecuada para la tarea del usuario?): escala **1 = Nada · 2 = Poco · 3 = Bastante · 4 = Totalmente**.
3. Registre cualquier observación en la columna correspondiente.
4. Firme el **dictamen global** (§7).

Leyenda subcaracterística primaria: **C** = Completitud · **Co** = Corrección · **P** = Pertinencia.

---

## 5. Matriz de evaluación (33 RF)

| RF | Descripción | Subcar. | Completa (1/0) | Correcta (1/0) | Pertinencia (1–4) | Observación |
|----|-------------|:------:|:--:|:--:|:--:|---|
| RF-01 | Registro de usuarios | C | ☐ | ☐ | ☐ | |
| RF-02 | Inicio de sesión | Co | ☐ | ☐ | ☐ | |
| RF-03 | Cierre de sesión | C | ☐ | ☐ | ☐ | |
| RF-04 | Recuperación de contraseña | C | ☐ | ☐ | ☐ | |
| RF-05 | Gestión de roles (admin/estudiante) | P | ☐ | ☐ | ☐ | |
| RF-06 | Perfil de usuario | C | ☐ | ☐ | ☐ | |
| RF-07 | Visualización del progreso general | C | ☐ | ☐ | ☐ | |
| RF-08 | Resumen de módulos recientes | P | ☐ | ☐ | ☐ | |
| RF-09 | Recomendaciones del tutor IA | P | ☐ | ☐ | ☐ | |
| RF-10 | Notificaciones / avisos | C | ☐ | ☐ | ☐ | |
| RF-11 | Listado de módulos | C | ☐ | ☐ | ☐ | |
| RF-12 | Detalle de módulo | C | ☐ | ☐ | ☐ | |
| RF-13 | Control de acceso secuencial | P | ☐ | ☐ | ☐ | |
| RF-14 | Estado de completitud de temas | Co | ☐ | ☐ | ☐ | |
| RF-15 | Visualización de contenido multimedia | C | ☐ | ☐ | ☐ | |
| RF-16 | Registro de progreso de lectura | Co | ☐ | ☐ | ☐ | |
| RF-17 | Marcado manual de tema | C | ☐ | ☐ | ☐ | |
| RF-18 | Autoevaluación por tema | Co | ☐ | ☐ | ☐ | |
| RF-19 | Interfaz de chat con el tutor IA | C | ☐ | ☐ | ☐ | |
| RF-20 | Respuestas basadas en corpus (RAG) | Co | ☐ | ☐ | ☐ | |
| RF-21 | Contexto de conversación (últimas 5 rondas) | P | ☐ | ☐ | ☐ | |
| RF-22 | Historial de conversaciones | C | ☐ | ☐ | ☐ | |
| RF-23 | Indicador "escribiendo" | P | ☐ | ☐ | ☐ | |
| RF-24 | Límite de consultas (rate limit) | Co | ☐ | ☐ | ☐ | |
| RF-25 | Panel de progreso por módulo | C | ☐ | ☐ | ☐ | |
| RF-26 | Métricas de tiempo de estudio | Co | ☐ | ☐ | ☐ | |
| RF-27 | Historial de autoevaluaciones | C | ☐ | ☐ | ☐ | |
| RF-28 | Otorgamiento automático de logros | Co | ☐ | ☐ | ☐ | |
| RF-29 | Visualización de logros | C | ☐ | ☐ | ☐ | |
| RF-30 | Carga de documentos al corpus RAG | C | ☐ | ☐ | ☐ | |
| RF-31 | Gestión del corpus de documentos | C | ☐ | ☐ | ☐ | |
| RF-32 | Gestión de usuarios (admin) | C | ☐ | ☐ | ☐ | |
| RF-33 | Gestión de contenido del curso (admin) | C | ☐ | ☐ | ☐ | |

**Totales del juez:** Completa = ____ / 33 · Correcta = ____ / 33 · Pertinencia (suma de Likert) = ____ / 132.

---

## 6. Cálculo de métricas (por juez)

| Métrica | Fórmula | Cálculo | Umbral | Resultado |
|---|---|---|---|---|
| Completitud funcional | X = (RF completos) / 33 | ____ / 33 | ≥ 0.95 | ______ |
| Corrección funcional | X = 1 − (RF incorrectos) / 33 | 1 − (____/33) | ≥ 0.90 | ______ |
| Pertinencia funcional | X = (RF con Likert ≥ 3) / 33 | ____ / 33 | ≥ 0.90 | ______ |
| Pertinencia — V de Aiken | V = (Σ Likert − n) / (n·(c−1)), n=33, c=4 | (____ − 33) / 99 | ≥ 0.80 | ______ |

---

## 7. Dictamen global del juez

**Resultado de la evaluación de adecuación funcional:**

☐ **Aplicable / Aprobado** — el sistema cumple la adecuación funcional.
☐ **Aplicable con observaciones** — cumple con ajustes menores (detallar abajo).
☐ **No aplicable / Desaprobado** — no cumple (detallar abajo).

**Observaciones generales y recomendaciones:**

```
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

<br>

| | |
|---|---|
| __________________________________ | _____ / _____ / 2026 |
| Firma del juez experto | Fecha |
| DNI / CIP: ____________________ | |

---

## 8. Hoja de consolidación (≥2 jueces) — *PENDIENTE de aplicación*

> Se completa una vez recibidos los dictámenes de los jueces. Mientras tanto, los valores quedan **en blanco** (no se simulan).

| Métrica | Juez 1 | Juez 2 | (Juez 3) | Promedio | Umbral | Veredicto |
|---|:--:|:--:|:--:|:--:|:--:|:--:|
| Completitud funcional | ____ | ____ | ____ | ____ | ≥ 0.95 | ⏳ |
| Corrección funcional | ____ | ____ | ____ | ____ | ≥ 0.90 | ⏳ |
| Pertinencia funcional | ____ | ____ | ____ | ____ | ≥ 0.90 | ⏳ |
| V de Aiken (pertinencia) | ____ | ____ | ____ | ____ | ≥ 0.80 | ⏳ |

**Criterio de cierre de OE5:** las tres métricas ≥ umbral **y** acuerdo de **≥2 jueces** ⇒ adecuación funcional validada.

**Acuerdo inter-juez** (porcentaje de coincidencia ítem a ítem, opcional): ______ %.

---

## Anexo — Respaldo objetivo (evidencia automatizada, ya disponible)

La completitud y la corrección funcionales cuentan con evidencia objetiva independiente del juicio experto, que el juez puede usar como soporte:

| Indicador | Valor (corte 04-jun-2026) | Fuente |
|---|---|---|
| RF priorizados implementados | 33 / 33 (100 %) | matriz de trazabilidad |
| RF con caso(s) de prueba automatizado(s) | 33 / 33 (100 %) | `test_iso25010.py` (guardian) |
| Casos de prueba ejecutados / aprobados | 396 / 396 (100 %) | `pytest` |
| Cobertura de código backend | 88 % | `pytest-cov` |
| Degradación elegante ante caída de Ollama | 4/4 escenarios | tests de fallback |

> Esta evidencia respalda **completitud** (X=33/33=1.00) y **corrección** (X=1−0/396=1.00) como medidas objetivas; el juicio de expertos las **confirma** y aporta la medida primaria de **pertinencia**.
