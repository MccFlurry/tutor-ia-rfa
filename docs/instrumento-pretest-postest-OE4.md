# Instrumento Pretest / Postest — OE4 (Rendimiento académico)

**Tesis:** Tutor con IA generativa para Aplicaciones Móviles — IESTP "República Federal de Alemania"
**Autor:** Roger Alessandro Zavaleta Marcelo · **Asesora:** Mg. Reyes Burgos, Karla (USAT)
**Objetivo asociado:** OE4 — *Contrastar la mejora del rendimiento académico mediante diseño pre-experimental con pretest y postest aplicado al grupo piloto.*

> **Estado (02-jun-2026):** Instrumento **diseñado y listo para validación/aplicación**. La aplicación real al grupo piloto está programada para el **Sprint 8 (29-jun – 10-jul-2026)**. Las cifras de resultados NO se reportan aquí hasta ejecutar el piloto.

---

## 1. Diseño metodológico

- **Tipo:** pre-experimental, **un solo grupo con pretest y postest** (`O1 → X → O2`).
- **Variable dependiente:** rendimiento académico en Aplicaciones Móviles (Kotlin/Android).
- **Tratamiento (X):** uso del tutor con IA generativa (RAG privado) durante el curso.
- **Población/muestra:** estudiantes matriculados en la unidad didáctica *Aplicaciones Móviles* (secciones mañana + noche, 2026-I). **Grupo piloto: 10–15 estudiantes** (submuestra por conveniencia, consentimiento informado).
- **Contraste estadístico:** **prueba t de Student para muestras relacionadas (pareada), α = 0.05**; tamaño del efecto **d de Cohen**. Si la diferencia no es normal (Shapiro-Wilk p<0.05), se usa la prueba de **Wilcoxon de rangos con signo** como alternativa no paramétrica.

### Hipótesis
- **H0:** μ(postest) = μ(pretest) — el tutor IA no mejora el rendimiento.
- **H1:** μ(postest) > μ(pretest) — el tutor IA mejora el rendimiento (contraste unilateral).

---

## 2. Marco / antecedentes del instrumento

No existe un inventario de conceptos **validado y estandarizado** para *desarrollo móvil Android/Kotlin*. Para programación introductoria sí existen instrumentos validados que sirven de **precedente metodológico** sobre cómo construir y validar una prueba de conceptos:

- **FCS1** (Foundational CS1) — primer instrumento validado de conceptos de programación introductoria, agnóstico al lenguaje.
- **SCS1** (Second CS1 Assessment) — versión isomorfa validada del FCS1, de uso abierto para investigación.

Dado que estos miden CS introductorio (en inglés) y no la unidad de Aplicaciones Móviles, se construye una **prueba de conocimientos propia** alineada al sílabo (M1–M5), siguiendo la práctica estándar en tesis peruanas: **validez por juicio de expertos** y **confiabilidad por KR-20** (ítems dicotómicos correcto/incorrecto).

---

## 3. Estructura del instrumento

- **Formato:** 20 ítems de opción múltiple (4 alternativas, 1 correcta).
- **Calificación:** dicotómica (1 = correcto, 0 = incorrecto). Puntaje total **0–20** (escala vigesimal peruana). Conversión a porcentaje = puntaje × 5.
- **Cobertura:** 4 ítems por cada uno de los 5 módulos del curso.
- **Equivalencia pretest/postest:** se aplica **la misma prueba** en ambos momentos (mismo instrumento → comparabilidad directa). Se recomienda **aleatorizar el orden** de ítems y alternativas en la aplicación digital para mitigar efecto de memoria/orden.

| Módulo | Tema | Ítems |
|--------|------|-------|
| M1 | Fundamentos y preparación del entorno | 1–4 |
| M2 | Lógica de programación en Kotlin | 5–8 |
| M3 | Elaboración de interfaces de usuario (UI) | 9–12 |
| M4 | Componentes Android y gestión de datos | 13–16 |
| M5 | Funcionalidades avanzadas y despliegue | 17–20 |

---

## 4. Ítems

### Módulo 1 — Fundamentos y entorno

**1.** ¿Cuál es el IDE oficial para el desarrollo de aplicaciones Android?
a) Eclipse  b) NetBeans  **c) Android Studio**  d) Visual Studio

**2.** ¿Qué archivo declara los componentes, permisos y la configuración general de la app?
**a) AndroidManifest.xml**  b) build.gradle  c) strings.xml  d) MainActivity.kt

**3.** ¿Qué sistema de construcción (build) utiliza Android de forma predeterminada?
a) Maven  b) Ant  c) Make  **d) Gradle**

**4.** ¿En qué carpeta del proyecto se ubican los recursos (layouts, strings, imágenes)?
a) `src`  **b) `res`**  c) `assets`  d) `lib`

### Módulo 2 — Lógica de programación en Kotlin

**5.** ¿Qué palabra clave declara una variable **inmutable** (solo lectura) en Kotlin?
a) `var`  **b) `val`**  c) `let`  d) `const fun`

**6.** ¿Cuál es el operador de **llamada segura** que evita `NullPointerException`?
a) `!!`  b) `?:`  **c) `?.`**  d) `==`

**7.** ¿Qué tipo de clase genera automáticamente `equals()`, `hashCode()` y `toString()`?
a) `sealed class`  b) `object`  **c) `data class`**  d) `abstract class`

**8.** ¿Qué estructura de control recorre cada elemento de una colección?
a) `when`  b) `try`  **c) `for`**  d) `object`

### Módulo 3 — Interfaces de usuario (UI)

**9.** ¿Qué componente muestra listas largas de forma eficiente **reciclando** vistas?
a) `ListView`  b) `ScrollView`  **c) `RecyclerView`**  d) `LinearLayout`

**10.** En la vista clásica de Android, ¿en qué lenguaje se definen los *layouts*?
a) JSON  b) YAML  **c) XML**  d) HTML

**11.** ¿Qué `ViewGroup` organiza los elementos en **una sola fila o columna**?
a) `ConstraintLayout`  **b) `LinearLayout`**  c) `FrameLayout`  d) `TableLayout`

**12.** ¿Qué método registra la acción a ejecutar cuando se pulsa un botón?
a) `onCreate()`  b) `findViewById()`  **c) `setOnClickListener()`**  d) `onResume()`

### Módulo 4 — Componentes Android y gestión de datos

**13.** ¿Qué método del ciclo de vida de una `Activity` se invoca al **crearse**?
a) `onStart()`  b) `onPause()`  **c) `onCreate()`**  d) `onDestroy()`

**14.** ¿Qué objeto se usa para comunicar componentes o abrir otra `Activity`?
**a) `Intent`**  b) `Bundle`  c) `Service`  d) `Fragment`

**15.** ¿Qué biblioteca recomendada por Android envuelve SQLite con un ORM?
a) Realm  b) Retrofit  **c) Room**  d) Gson

**16.** ¿Qué biblioteca se usa comúnmente para consumir **APIs REST** en Android?
a) Room  b) Glide  **c) Retrofit**  d) Dagger

### Módulo 5 — Funcionalidades avanzadas y despliegue

**17.** ¿Qué mecanismo de Kotlin ejecuta tareas asíncronas sin bloquear el hilo principal?
a) `Thread` manual  b) bucles `while`  **c) Corrutinas**  d) `for` anidados

**18.** ¿Qué formato de paquete recomienda Google Play para la distribución?
a) APK clásico  **b) Android App Bundle (AAB)**  c) JAR  d) ZIP

**19.** ¿Qué herramienta ofusca y optimiza el código en compilaciones *release*?
a) Logcat  b) Lint  **c) ProGuard / R8**  d) Gradle

**20.** En Android 6+ (API 23+), ¿cómo se solicitan los permisos **peligrosos**?
a) Solo en el Manifest  b) No se solicitan  **c) En tiempo de ejecución con `requestPermissions()`**  d) En `strings.xml`

---

## 5. Clave de respuestas

| Ítem | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
|------|---|---|---|---|---|---|---|---|---|----|----|----|----|----|----|----|----|----|----|----|
| **Resp.** | c | a | d | b | b | c | c | c | c | c | b | c | c | a | c | c | c | b | c | c |

---

## 6. Validez — Juicio de expertos

Antes de aplicar, ≥3 jueces expertos evalúan cada ítem en **claridad, coherencia, relevancia y suficiencia**. Se cuantifica con **V de Aiken** (se aceptan ítems con **V ≥ 0.80**).

**Ficha de validación (por juez):**

| Ítem | Claridad (1-4) | Coherencia (1-4) | Relevancia (1-4) | Observaciones |
|------|----------------|------------------|------------------|---------------|
| 1 …  |                |                  |                  |               |

V de Aiken por ítem: `V = (Σ(s)) / (n · (c − 1))`, donde `s` = valor asignado − 1, `n` = nº jueces, `c` = nº de categorías (4).

> Los 2 jueces de la validación ISO/IEC 25010 (OE5) pueden actuar también como jueces de este instrumento, reutilizando el panel de expertos.

---

## 7. Confiabilidad — KR-20

Aplicar a una **muestra piloto** (estudiantes equivalentes, no del grupo final). Coeficiente **Kuder-Richardson 20** (apropiado para ítems dicotómicos):

`KR-20 = (k / (k−1)) · (1 − (Σ p·q) / Var_total)`

donde `k` = nº ítems (20), `p` = proporción de aciertos del ítem, `q = 1−p`, `Var_total` = varianza de los puntajes totales. **Se acepta KR-20 ≥ 0.70.**

---

## 8. Procedimiento de aplicación

1. **Pretest** (semana 1, antes del tratamiento): aplicar el instrumento al grupo piloto. Registrar puntaje 0–20 por estudiante (código anónimo, no nombre).
2. **Tratamiento:** los estudiantes usan el tutor IA durante el curso (módulos M1–M5).
3. **Postest** (última semana): aplicar **el mismo instrumento**.
4. **Análisis:** ver `backend/notebooks/pretest_postest_analysis.ipynb` (t pareada + d de Cohen + Wilcoxon de respaldo).

**Plantilla de captura de datos** (`docs/datos-pretest-postest.csv`):

```csv
codigo_estudiante,pretest,postest
E01,,
E02,,
...
```

---

## 9. Plan de análisis estadístico

| Paso | Prueba | Criterio |
|------|--------|----------|
| Normalidad de las diferencias | Shapiro-Wilk | p ≥ 0.05 → usar t pareada |
| Contraste principal | **t de Student pareada** (`scipy.stats.ttest_rel`) | **p < 0.05** → mejora significativa |
| Tamaño del efecto | **d de Cohen** (media de diferencias / DE de diferencias) | 0.2 pequeño · 0.5 medio · 0.8 grande |
| Alternativa no paramétrica | Wilcoxon de rangos con signo | si no se cumple normalidad |

---

## 10. Ética

- Consentimiento informado por escrito.
- Datos anonimizados (código, no nombre).
- Participación voluntaria; no afecta la nota oficial del curso.

---

*Documento generado el 02-jun-2026 como insumo del OE4. La aplicación al piloto y el reporte de resultados corresponden al Sprint 8. Exportar a `.docx` antes de la sustentación.*
