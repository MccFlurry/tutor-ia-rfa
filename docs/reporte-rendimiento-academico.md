# Reporte de Rendimiento Académico — OE4

**Tesis:** Tutor con IA generativa para Aplicaciones Móviles — IESTP "República Federal de Alemania"
**Autor:** Roger Alessandro Zavaleta Marcelo · **Asesora:** Mg. Reyes Burgos, Karla (USAT)
**Objetivo (OE4):** Contrastar la mejora del rendimiento académico mediante diseño pre-experimental con pretest y postest aplicado al grupo piloto.

> **Estado al 04-jun-2026:** **APLICADO.** Pretest y postest administrados al grupo (n = 49) tras un período de uso del tutor durante el curso. Resultados reales en la §6. **OE4 validado:** mejora estadísticamente significativa (t pareada p < 0.001; Wilcoxon p < 0.001; d de Cohen = 2.12). Reproducible con `backend/scripts/analyze_pretest_postest.py` y `backend/notebooks/pretest_postest_analysis.ipynb` sobre `docs/datos-pretest-postest.csv`.

---

## 1. Diseño

Pre-experimental, **un solo grupo con pretest y postest** (`O1 → X → O2`), donde `X` = uso del tutor con IA generativa durante el curso de Aplicaciones Móviles.

- **Hipótesis:** H1: μ(postest) > μ(pretest); H0: μ(postest) = μ(pretest).
- **Contraste:** **t de Student para muestras relacionadas (pareada), α = 0.05** + tamaño del efecto **d de Cohen**; alternativa no paramétrica **Wilcoxon** si no se cumple normalidad.

## 2. Instrumento

Prueba de conocimientos de 20 ítems (4 por módulo M1–M5), opción múltiple, calificación dicotómica, escala 0–20. Detalle completo, clave, validez (juicio de expertos / V de Aiken) y confiabilidad (KR-20) en **`docs/instrumento-pretest-postest-OE4.md`**.

- **Validez:** ≥3 jueces expertos, se aceptan ítems con **V de Aiken ≥ 0.80**.
- **Confiabilidad:** **KR-20 ≥ 0.70** sobre muestra piloto.

## 3. Muestra

- **Población:** estudiantes matriculados en la unidad didáctica *Aplicaciones Móviles*, periodo 2026-I, IESTP RFA (secciones mañana + noche; **49 matriculados** registrados y con cuenta creada en el sistema).
- **Muestra evaluada:** **49 estudiantes** con pretest y postest completos (censo de la cohorte, no submuestra). Supera el mínimo planificado de 10–15 → mayor potencia estadística. Códigos `M01–M24` (24, mañana) y `N01–N25` (25, noche).

## 4. Procedimiento

1. **Pretest** (semana 1, antes del tratamiento).
2. **Tratamiento:** uso del tutor IA durante el curso (M1–M5).
3. **Postest** (última semana, mismo instrumento).
4. **Análisis** con `backend/notebooks/pretest_postest_analysis.ipynb`.

## 5. Plan de análisis estadístico

| Paso | Prueba | Criterio |
|------|--------|----------|
| Normalidad de las diferencias | Shapiro-Wilk | p ≥ 0.05 → t pareada |
| Contraste principal | t de Student pareada | **p < 0.05** |
| Tamaño del efecto | d de Cohen | 0.2 / 0.5 / 0.8 |
| Alternativa | Wilcoxon de rangos con signo | si no normal |

## 6. Resultados (n = 49)

### 6.1 Estadística descriptiva (escala 0–20)

| Medida | Pretest | Postest |
|--------|---------|---------|
| Media | 10.45 | 14.43 |
| Desviación estándar | 2.76 | 3.11 |
| Mínimo | 5 | 7 |
| Máximo | 17 | 20 |

- **Ganancia media:** **+3.98 puntos** (DE = 1.88); **IC 95% [3.44, 4.52]**.
- **Distribución de cambios:** **46/49 estudiantes mejoraron (94 %)**, 2 sin cambio, 1 retrocedió.

### 6.2 Verificación de supuestos

| Prueba | Estadístico | p | Lectura |
|--------|-------------|---|---------|
| Shapiro-Wilk (diferencias) | W = 0.947 | 0.027 | Las diferencias se desvían levemente de la normalidad. |

La desviación es leve (W = 0.947, cercano a 1). Con n = 49 la prueba t para muestras relacionadas es **robusta** ante desviaciones moderadas de la normalidad por el teorema del límite central; aun así, se reporta la prueba no paramétrica de **Wilcoxon** como respaldo, la cual **no asume normalidad** y confirma el mismo resultado (§6.3).

### 6.3 Contraste de hipótesis

| Prueba | Estadístico | gl | p (unilateral) | Decisión |
|--------|-------------|----|----------------|----------|
| **t de Student pareada** (oficial OE4) | t = 14.85 | 48 | **7.2 × 10⁻²⁰ (< 0.001)** | **Se rechaza H0** |
| Wilcoxon rangos con signo (respaldo) | W = 1126.5 | — | **1.1 × 10⁻⁹ (< 0.001)** | **Se rechaza H0** |

Ambas pruebas coinciden: el postest es significativamente mayor que el pretest (**p ≪ 0.05**).

### 6.4 Tamaño del efecto

| Medida | Valor | Interpretación |
|--------|-------|----------------|
| **d de Cohen (pareado)** | **2.12** | Efecto **grande** (referencia Cohen: ≥0.8). |
| IC 95% de la ganancia media | [3.44, 4.52] puntos | No incluye 0 → mejora consistente. |

### 6.5 Conclusión OE4

Se evidencia **estadísticamente** la mejora del rendimiento académico tras el uso del tutor con IA generativa: la media subió de **10.45 a 14.43** (+3.98 ptos), con **t pareada t(48)=14.85, p<0.001** y efecto **grande (d=2.12)**, confirmado por Wilcoxon (p<0.001). **OE4 validado.**

## 7. Limitaciones (validez interna)

El diseño es **pre-experimental de un solo grupo** (`O1 → X → O2`), **sin grupo de control**. En consecuencia:

- La mejora observada **no se atribuye exclusivamente** al tutor IA. Amenazas a la validez interna no descartables: **maduración** (aprendizaje propio del curso), **historia** (otros recursos/clases), **efecto de testing** (repetir el mismo instrumento) y **regresión a la media**.
- Lo que el diseño permite afirmar con rigor: **hubo una mejora significativa y de gran magnitud** en el periodo de uso del sistema. Establecer **causalidad exclusiva** requeriría un diseño cuasi-experimental o experimental con grupo de control, propuesto como **trabajo futuro**.
- El efecto observado (d = 2.12) es elevado para un estudio educativo; es coherente con el diseño de un solo grupo, que tiende a sobreestimar el tamaño del efecto respecto a diseños con control.

## 8. Estado y trazabilidad

- ✅ Diseño metodológico definido (pre-experimental, t pareada p<0.05).
- ✅ Instrumento construido (20 ítems M1–M5) — `docs/instrumento-pretest-postest-OE4.md`.
- ✅ Pipeline de análisis validado — `backend/notebooks/pretest_postest_analysis.ipynb` + `backend/scripts/analyze_pretest_postest.py`.
- ✅ Datos reales capturados — `docs/datos-pretest-postest.csv` (n = 49).
- ✅ **Aplicación pretest/postest ejecutada (04-jun-2026)** y resultados computados — §6.
- ✅ **OE4 validado:** p < 0.001 (t pareada y Wilcoxon), d = 2.12.
- ⏳ Validación del instrumento por jueces (V de Aiken / KR-20) — documentar dictamen en `docs/instrumento-pretest-postest-OE4.md`.

---

*Resultados computados sobre datos reales de n = 49 estudiantes (`docs/datos-pretest-postest.csv`). Reproducible: `cd backend && python scripts/analyze_pretest_postest.py`.*
