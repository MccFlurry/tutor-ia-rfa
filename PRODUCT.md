# Product

## Register

product

## Users

**Primary — the piloto students.** 10–15 students at IESTP "República Federal de Alemania" (Chiclayo, Perú), enrolled in the *Aplicaciones Móviles* (Android/Kotlin) course. Technical-institute level: capable adults, not children and not university CS majors. Mixed entry skill — the system assesses each one and levels them `beginner / intermediate / advanced`, then adapts. Spanish (peruano) speakers. Their context: studying on their own time and in guided sessions, often on modest hardware or a phone, reaching for the private tutor when they get stuck, self-checking through quizzes and coding challenges, watching their progress. The job to be done: **learn to build Android apps and raise their academic performance** — the thesis measures that gain with a pre/post test.

**Secondary — the instructor/admin.** The tesista (as admin) and the IESTP coordinator manage the RAG corpus, course content, the fallback question bank, and user levels through the Admin surface. They need control and trust in what the tutor will say, not flourish.

## Product Purpose

An intelligent tutoring system (STI) built on a **100% private RAG** — Ollama self-hosted, never a paid API — over the official course syllabus. It teaches 5 modules of Android/Kotlin, answers domain questions with **traceable citations**, generates level-adapted quizzes and coding challenges scored by the LLM, assesses entry level and re-levels students dynamically, and surfaces gamified progress plus proactive, deterministic nudges.

It exists as a USAT undergraduate thesis testing one question: **does a generative-AI tutor improve academic performance for IESTP RFA students?** Success is evidence, not vibes — measured learning gain (pre/post, paired t-test p<0.05), validated retrieval and generation quality (RAGAS), and functional adequacy (ISO/IEC 25010). The interface's job is to make that learning happen and never get in its way.

## Brand Personality

**Warm institutional confidence.** Three words: **trustworthy, encouraging, focused** — finished with a modern hand.

The four traits chosen resolve into one voice rather than four competing ones:
- **Institutional & trustworthy** is the foundation — this is a real institute and a thesis-grade system, carried visually by the navy + heritage-gold identity. It earns belief.
- **Encouraging & motivating** is the texture — progress, achievements, and nudges keep a student moving, framed like a patient instructor who notices effort.
- **Focused & technical** is the working mode — a quiet surface to read lessons, think, and write code without noise.
- **Modern & current** is the finish — it feels like 2026 software, not a dated school portal.

Voice/tone: español peruano, claro y cercano. Explain like a good instructor — never condescending, never hype. The tutor **admits uncertainty and never invents** (the RAG rule is also the personality). Celebrate progress without infantilizing; these are adults.

Emotional goals: *confidence* ("I can build this"), *momentum* (progress that genuinely motivates), *calm focus* (room to think), on a base of *institutional credibility*.

## Anti-references

- **Not a cluttered Moodle-style LMS** (the explicit anti-reference). No busy everything-everywhere navigation, no content buried under nested tabs and breadcrumbs, no dated academic-portal density. Each screen surfaces one clear next action.
- **Not generic template SaaS / "AI made this" slop.** No hero-metric template (big number + small label + supporting stats), no endless identical icon-heading-text card grids, no gradient text. (The shared absolute bans hold here.)
- **Not childish, loud gamification.** "Encouraging" must never tip into cartoon mascots, neon badges, or confetti spam. The students are tertiary-level technical learners; motivation is respectful, tied to real progress.

## Design Principles

1. **El tutor no inventa — trust through traceability.** Every domain answer cites its source and admits uncertainty rather than fabricating. Credibility *is* the product; the UI must always make the source visible and the limits honest.
2. **Meet the student where they are.** Level (beginner/intermediate/advanced) shapes difficulty, feedback, and recommendations. The interface guides the next step and never dead-ends a learner.
3. **Momentum over decoration.** Gamification exists to keep students moving, not to entertain. Every motivational element must map to a real unit of progress — if it doesn't, it's noise.
4. **The tool disappears into the task.** Reading a lesson, asking the tutor, writing code — each screen has one primary job. Institutional polish serves focus, not flourish.
5. **Resilient by design.** AI is best-effort. Every AI path has a graceful fallback (quiz → DB bank, coding → catalog, assessment → docente bank, dashboard → degraded cache). A student is never blocked because Ollama is down, and the UI must make a fallback feel intentional, not broken.

## Accessibility & Inclusion

Target **WCAG 2.1 AA**, in both light and dark themes:
- Body text ≥4.5:1 contrast, large text ≥3:1; placeholders held to the same body bar.
- Fully keyboard-operable; visible `:focus-visible` rings; skip-link to main content.
- `prefers-reduced-motion` honored — animations collapse to instant/crossfade (already wired globally).
- Semantic feedback never relies on hue alone — pair color with icon and text (success/warning/info/error).
- Touch targets ≥44px; mobile-first down to 375px, since many students work from a phone on modest hardware.
- UI language is Spanish (peruano); plain, non-jargony phrasing for a mixed-skill cohort.
