# Reporte de Rendimiento Académico — OE4

**Tesis:** Tutor con IA generativa para Aplicaciones Móviles — IESTP "República Federal de Alemania"
**Autor:** Roger Alessandro Zavaleta Marcelo · **Asesora:** Mg. Reyes Burgos, Karla (USAT)
**Objetivo (OE4):** Contrastar la mejora del rendimiento académico mediante diseño pre-experimental con pretest y postest aplicado al grupo piloto.

> **Estado al 02-jun-2026:** diseño e instrumento **listos**; cuentas del piloto **aprovisionadas**; **aplicación al piloto programada para el Sprint 8 (29-jun – 10-jul-2026)**. Las secciones de resultados se completan con datos reales tras el piloto. Mientras tanto, el pipeline de análisis está validado (ver notebook).

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
- **Grupo piloto:** **10–15 estudiantes** (submuestra por conveniencia, consentimiento informado).

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

## 6. Resultados

> **PENDIENTE — se completa con los datos reales del piloto (Sprint 8).**

| Métrica | Valor |
|---------|-------|
| n (piloto) | _por registrar_ |
| Media pretest (0–20) | _por registrar_ |
| Media postest (0–20) | _por registrar_ |
| Diferencia media | _por registrar_ |
| t (gl = n−1) | _por registrar_ |
| p (unilateral) | _por registrar_ |
| d de Cohen | _por registrar_ |
| Decisión sobre H0 | _por registrar_ |

## 7. Estado y trazabilidad

- ✅ Diseño metodológico definido (pre-experimental, t pareada p<0.05).
- ✅ Instrumento construido (20 ítems M1–M5) — `docs/instrumento-pretest-postest-OE4.md`.
- ✅ Pipeline de análisis validado — `backend/notebooks/pretest_postest_analysis.ipynb`.
- ✅ Plantilla de captura — `docs/datos-pretest-postest.csv`.
- ✅ 49 cuentas de estudiantes aprovisionadas en producción.
- ⏳ Validación del instrumento por jueces (V de Aiken) — antes del piloto.
- ⏳ Aplicación pretest/postest al piloto + cómputo de resultados — **Sprint 8**.

---

*La conclusión sobre el OE4 queda condicionada a la ejecución del piloto. No se reportan resultados antes de obtener datos reales.*
