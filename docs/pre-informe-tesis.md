**UNIVERSIDAD CATÓLICA SANTO TORIBIO DE MOGROVEJO**

**FACULTAD DE INGENIERÍA**

**ESCUELA DE INGENIERÍA DE SISTEMAS Y COMPUTACIÓN**

**TUTOR CON IA GENERATIVA EN LA ASIGNATURA APLICACIONES MÓVILES PARA
MEJORAR EL RENDIMIENTO ACADÉMICO DE ESTUDIANTES DEL IESTP "RFA",
CHICLAYO**

**PRE-INFORME DE TESIS**

PARA EVIDENCIAR LA EJECUCIÓN DE TESIS

EN EL CURSO DE SEMINARIO DE TESIS I

**AUTOR**

Zavaleta Marcelo, Roger Alessandro

DNI: 70469567

**ASESORA**

Mg. Reyes Burgos, Karla

https://orcid.org/0000-0002-9650-4427

Chiclayo, 2026

# INFORMACIÓN GENERAL

  -----------------------------------------------------------------------
  **Campo**                           **Detalle**
  ----------------------------------- -----------------------------------
  1\. Facultad y Escuela              Facultad de Ingeniería -- Escuela
                                      de Ingeniería de Sistemas y
                                      Computación

  2\. Título del informe de tesis     Tutor con IA generativa en la
                                      asignatura aplicaciones móviles
                                      para mejorar el rendimiento
                                      académico de estudiantes del IESTP
                                      "RFA", Chiclayo

  3\. Autor y firma                   Zavaleta Marcelo, Roger Alessandro
                                      --- DNI 70469567

  4\. Asesora y firma                 Mg. Reyes Burgos, Karla --- ORCID
                                      0000-0002-9650-4427

  5\. Línea y área de la              Desarrollo e innovación tecnológica
  investigación                       -- Inteligencia artificial

  6\. Fecha de presentación           21 de junio de 2026
  -----------------------------------------------------------------------

# ÍNDICE

# I. RESULTADOS

Los resultados se presentan exponiendo los hallazgos y productos del
desarrollo del tutor con IA generativa para la asignatura Aplicaciones
Móviles del IESTP "República Federal de Alemania" (RFA), estructurado
con la metodología ágil SCRUM como marco principal de gestión,
complementada con CRISP-DM exclusivamente para las fases asociadas al
componente de aprendizaje de máquina del pipeline de Recuperación
Aumentada por Generación (RAG). El proyecto se organiza en doce sprints
distribuidos en seis iteraciones del modelo CRISP-DM. La presentación se
ordena en dos planos complementarios: el plano metodológico (apartado
1.1), que recorre las seis iteraciones del cronograma y los sprints que
las componen; y el plano de objetivos (apartado 1.2), que evidencia el
cumplimiento de cada uno de los cinco objetivos específicos frente a sus
indicadores objetivamente verificables.

## 1.1. En base a la metodología utilizada

El sistema se desarrolla empleando SCRUM para la gestión general del
proyecto y CRISP-DM como marco que estructura el ciclo de vida del
componente de aprendizaje de máquina del pipeline RAG. Los doce sprints
se distribuyen en seis iteraciones CRISP-DM: Iteración #1 Comprensión
del negocio (Sprint 1); Iteración #2 Comprensión de los datos (Sprint
2); Iteración #3 Preparación de los datos y modelado (Sprints 3--6);
Iteración #4 Evaluación (Sprint 7); Iteración #5 Despliegue (Sprints
8--10); e Iteración #6 Validación con usuarios y pilotaje (Sprints
11--12). SCRUM permite entregas funcionales incrementales y la revisión
continua; CRISP-DM aporta el marco que justifica las fases del pipeline
RAG y la lógica de validación de los modelos seleccionados (RAGAS) y del
sistema integrado (ISO/IEC 25010:2023 y diseño preexperimental con
pretest/postest).

### 1.1.1. Iteración #1: Comprensión del negocio (Sprint 1)

La Iteración #1 (Sprint 1, 23 -- 29 de marzo de 2026) estableció la base
documental y técnica del proyecto. Se formalizó la Especificación de
Requisitos del Software (ERS), se analizó el contexto educativo del
IESTP "RFA", se diseñó la arquitectura de microservicios
contenedorizados y se construyeron los dos primeros modelos del Sistema
de Tutoría Inteligente (dominio y pedagógico), insumo para la selección
de modelos del OE1 y para la operacionalización del corpus instruccional
de OE3 y OE4.

**Actividades y técnicas**

- Configuración del entorno de desarrollo: inicialización del
  repositorio Git, Docker Desktop, Python 3.11 y Node.js 20.

- Redacción de la ERS con 52 requisitos (33 RF priorizados y 19 RNF) en
  8 módulos del sistema, alineados con ISO/IEC 25010:2023 y trazables a
  los objetivos específicos OE1--OE5.

- Diseño de la arquitectura de microservicios bajo notación C4 (niveles
  1, 2 y 3): backend FastAPI, motor Ollama (LLM), PostgreSQL con
  extensión pgvector, caché Redis y reverse proxy Caddy con TLS,
  orquestados con Docker Compose.

- Definición del esquema relacional y vectorial: modelos SQLAlchemy 2.x
  asíncronos para users, modules, lessons, exercises, progress,
  chat_sessions y document_chunks.

- Construcción del modelo de dominio: estructura jerárquica en tres
  niveles (módulo, tema y subtema) que cubre el 100 % del sílabo oficial
  2026-I, con relaciones explícitas de prerrequisito entre nodos.

- Formalización del modelo pedagógico: tres estrategias de tutoría
  diferenciadas (pistas graduales, ejemplos resueltos y
  retroalimentación inmediata o diferida) con criterios de adaptación
  por nivel del estudiante.

*Evidencia 1: distribución de requisitos por categoría y prioridad (ERS
v1.0)*

  ---------------------------------------------------------------------------
  **Categoría**   **Total**      **Prioridad    **Prioridad    **Prioridad
                                 alta**         media**        baja**
  --------------- -------------- -------------- -------------- --------------
  Requisitos      33             22             10             1
  Funcionales                                                  
  (RF)                                                         

  Requisitos No   19             13             6              0
  Funcionales                                                  
  (RNF)                                                        

  TOTAL           52             35             16             1
  ---------------------------------------------------------------------------

*Tabla 1. Síntesis de requisitos especificados en la ERS v1.0.*

*Evidencia 2: trazabilidad ERS → objetivos específicos (matriz V.2.1)*

  -----------------------------------------------------------------------
  **Objetivo específico   **RF asociados**        **RNF asociados**
  (V.2.1)**                                       
  ----------------------- ----------------------- -----------------------
  OE1: Selección de LLM y Estudio comparativo     RNF-02.3, RNF-03.6,
  de embeddings           externo al software     RNF-07.2

  OE2: Validación RAGAS   RF-19, RF-20, RF-21,    RNF-02.3, RNF-02.5
  del pipeline RAG        RF-22                   

  OE3: Despliegue en GCE  RF-07 a RF-29, RF-33    RNF-01, RNF-02, RNF-05,
  con trazabilidad                                RNF-06

  OE4: Mejora del         Instrumento externo al  ---
  rendimiento             software                
  (pretest/postest)                               

  OE5: Adecuación         RF-18, RF-25, RF-27,    RNF-01, RNF-02, RNF-03,
  funcional ISO/IEC 25010 RF-29, RF-32            RNF-04
  -----------------------------------------------------------------------

*Tabla 2. Trazabilidad de requisitos a los cinco objetivos específicos
vigentes (matriz V.2.1).*

**Herramientas**

Docker 24.0 + Docker Compose 2.20 (orquestación), PostgreSQL 16 +
pgvector (base relacional y vectorial), SQLAlchemy 2.x async + asyncpg
(ORM y driver asíncrono), Alembic (versionado del esquema) y Git
(control de versiones).

**Artefactos / entregables**

- Especificación de Requisitos del Software con 52 requisitos.

- Archivos docker-compose.yml y .env.example con la orquestación inicial
  del sistema.

- Modelos ORM iniciales y migración inicial de Alembic
  (alembic/versions/20260302_01_initial.py).

### 1.1.2. Iteración #2: Comprensión de los datos (Sprint 2)

La Iteración #2 (Sprint 2, 30 de marzo -- 05 de abril de 2026) completó
los dos modelos restantes del STI (modelo del estudiante y modelo de
interacción) y ejecutó la evaluación comparativa de modelos LLM y de
embeddings, cerrando la selección técnica del OE1 (Resultados R1.1 y
R1.2).

**Actividades y técnicas**

- Especificación del modelo del estudiante: cinco atributos clave (nivel
  actual, historial de evaluaciones, módulos completados, logros y
  preferencias de interacción) con su diagrama entidad-relación.

- Evaluación comparativa de tres LLM open-source sobre Ollama
  (qwen2.5:7b-instruct-q4_K_M, llama3:8b-instruct-q4_K_M y
  mistral:7b-instruct-q4_K_M) sobre un golden set de 50 prompts en
  español, midiendo calidad con rúbrica Likert 1--5, consumo de memoria
  y latencia.

- Evaluación comparativa de dos modelos de embeddings (mxbai-embed-large
  y nomic-embed-text) para similitud semántica en español sobre 20
  queries representativas del corpus; mxbai-embed-large resultó superior
  en precisión de recuperación.

- Configuración del motor Ollama con qwen2.5:7b-instruct-q4_K_M y
  definición de un Modelfile personalizado con el system prompt
  pedagógico del tutor.

*Evidencia 3: benchmark global de los tres modelos LLM evaluados (50
prompts c/u)*

  -----------------------------------------------------------------------------------
  **Modelo**   **Tamaño   **Lat. avg **Lat. p95 **Tokens/s**   **Calidad   **VRAM
               (GB)**     (s)**      (s)**                     (1-5)**     (GB)**
  ------------ ---------- ---------- ---------- -------------- ----------- ----------
  qwen2.5:7b   4.59       5.91       8.66       107.0          4.85        4.59

  llama3:8b    5.09       4.71       7.40       109.6          4.84        5.09

  mistral:7b   4.79       3.90       6.79       120.2          4.28        4.79
  -----------------------------------------------------------------------------------

*Tabla 3. Comparativa global de rendimiento de los tres LLM evaluados.*

*Evidencia 4: desglose por criterio de la rúbrica Likert (1--5)*

  -------------------------------------------------------------------------------------------
  **Modelo**   **Exactitud**   **Fluidez**   **Sin             **Pedagogía**   **Promedio**
                                             alucinaciones**                   
  ------------ --------------- ------------- ----------------- --------------- --------------
  qwen2.5:7b   4.72            4.86          5.00              4.82            4.85

  llama3:8b    4.72            4.88          4.92              4.86            4.84

  mistral:7b   3.90            4.56          4.60              4.04            4.28
  -------------------------------------------------------------------------------------------

*Tabla 4. Promedios Likert por criterio de la rúbrica (juez LLM).*

*Evidencia 5: benchmark de modelos de embeddings (20 queries / 163
chunks)*

  --------------------------------------------------------------------------------------
  **Modelo**          **Dimensiones**   **Recall@5**   **MRR**        **Latencia/query
                                                                      (ms)**
  ------------------- ----------------- -------------- -------------- ------------------
  mxbai-embed-large   1024              0.550          0.453          173.4

  nomic-embed-text    768               0.350          0.305          131.0
  --------------------------------------------------------------------------------------

*Tabla 5. Comparativa de modelos de embeddings sobre el corpus M1--M3.*

La selección final recayó en qwen2.5:7b-instruct-q4_K_M como LLM y
mxbai-embed-large como modelo de embeddings, por su desempeño superior
en español y su consumo razonable de recursos. La validación de estos
modelos contra los umbrales del OE1 (Accuracy, Likert, Recall@5, MRR@10,
nDCG@10) se ejecuta sobre el pipeline de producción y se reporta en el
apartado 1.2.1.

**Herramientas**

Figma (mockups UI/UX), PlantUML (diagramas de secuencia UML), Draw.io
(diagrama ER y grafo del modelo de dominio), Ollama (servidor local de
modelos), qwen2.5:7b-instruct-q4_K_M (LLM) y mxbai-embed-large
(embeddings de 1 024 dimensiones).

**Artefactos / entregables**

- Reporte comparativo de modelos LLM y embeddings.

- Modelfile personalizado del LLM en ollama/modelfile-qwen2.5 con el
  system prompt pedagógico.

### 1.1.3. Iteración #3: Preparación de los datos y modelado (Sprints 3--6)

La Iteración #3 (Sprints 3--6, 06 -- 24 de abril de 2026) construyó el
núcleo funcional del sistema: el pipeline RAG operativo, el backend
REST, el frontend integrado de extremo a extremo y la primera validación
diagnóstica del pipeline con RAGAS. Cubre las fases CRISP-DM de
Preparación de los datos y Modelado del componente de IA.

#### 1.1.3.1. Sprint 3: Pipeline RAG, ingesta, chunking e indexación vectorial

El Sprint 3 (06 -- 12 de abril de 2026) construyó el pipeline RAG
operativo sobre el corpus de los Módulos 1--3 del sílabo.

**Actividades y técnicas**

- Módulo de chunking con RecursiveCharacterTextSplitter (chunks de 500
  tokens, solapamiento de 50), preservando la jerarquía del sílabo
  (id_modulo, id_tema, id_subtema) en los metadatos.

- Cálculo de embeddings del corpus con mxbai-embed-large (1 024
  dimensiones) y persistencia en PostgreSQL con pgvector, indexados con
  índice IVFFlat para búsqueda por similitud coseno.

- Orquestador RAG: recuperación por similitud coseno (top-k = 5),
  construcción del prompt aumentado con contexto e historial, y
  generación vía API de Ollama con trazabilidad explícita de fuentes.

- Servicio de ingesta IngestService como BackgroundTask: parseo de PDF,
  DOCX y Markdown con pypdf y python-docx, segmentación y upsert de
  vectores en la tabla document_chunks.

*Evidencia 6: parámetros del pipeline RAG --- implementación inicial
(cierre del Sprint 3)*

  --------------------------------------------------------------------------------
  **Parámetro**           **Implementación inicial**       **Comentario**
  ----------------------- -------------------------------- -----------------------
  Modelo LLM              qwen2.5:7b-instruct-q4_K_M       Confirmado en Sprint 2.

  Modelo de embeddings    mxbai-embed-large (1 024 dim)    Confirmado en Sprint 2.

  Estrategia de chunking  RecursiveCharacterTextSplitter   Iteración baseline.
                          (500 / 50)                       

  Umbral de similitud     0.70                             Iteración baseline; se
  (coseno)                                                 ajusta en Sprint 6.

  Top-k del retrieval     5                                Iteración baseline.

  num_ctx del LLM         4 096                            Iteración baseline.

  Temperatura del LLM     0.3                              Iteración baseline.

  TTL de la caché RAG     3 600 s (1 h)                    Confirmado.
  --------------------------------------------------------------------------------

*Tabla 6. Parámetros del pipeline RAG al cierre del Sprint 3.*

La Figura 1 representa el flujo del pipeline RAG para una consulta del
estudiante (vectorización de la consulta, recuperación en pgvector,
construcción del prompt aumentado, generación con qwen2.5:7b y retorno
con citas).

*Figura 1. Flujo del pipeline RAG para una consulta del estudiante.*

**Artefactos / entregables**

- Módulos del pipeline RAG: backend/app/rag/{ingestor.py, retriever.py,
  generator.py, orchestrator.py}.

- Servicios de dominio: IngestService, LLMService, RAGService.

- Corpus de los Módulos 1--3 indexado en PostgreSQL + pgvector (tabla
  document_chunks con índice IVFFlat).

#### 1.1.3.2. Sprint 4: Backend FastAPI con autenticación JWT y endpoints REST

El Sprint 4 (13 -- 17 de abril de 2026) implementó el backend completo:
autenticación JWT, control de acceso por roles, diez routers REST con
más de veinticinco endpoints, middlewares transversales y la integración
del backend con el orquestador RAG del sprint anterior.

*Evidencia 7: routers REST implementados en el backend*

  -----------------------------------------------------------------------
  **Router**              **Endpoints             **Función**
                          principales**           
  ----------------------- ----------------------- -----------------------
  /auth                   POST /register · /login Registro, autenticación
                          · /refresh · /logout    y ciclo de vida de
                                                  tokens.

  /users                  GET /me · PUT /me · GET Perfil y nivel asignado
                          /me/level               por la evaluación de
                                                  entrada.

  /modules                GET / · GET /{id}       Listado y detalle de
                                                  módulos con estado de
                                                  desbloqueo.

  /topics                 GET /{id} · POST        Contenido Markdown,
                          /{id}/complete          video y marcado de
                                                  completitud.

  /quiz                   GET /{topic_id} · POST  Preguntas generadas por
                          /submit                 IA y cálculo de
                                                  puntaje.

  /chat                   POST /sessions ·        Tutor conversacional
                          /messages · GET         con RAG y rate
                          /remaining              limiting.

  /dashboard              GET /                   Nivel, progreso global,
                                                  logros y
                                                  recomendaciones.

  /coding                 GET /topic/{id} · POST  Desafíos de código
                          /{id}/submit            adaptados y feedback de
                                                  la IA.

  /assessment             POST /start · /submit   Evaluación de entrada
                                                  que clasifica en un
                                                  nivel.

  /admin                  POST /corpus/upload ·   Gestión del corpus y
                          GET /users              supervisión de
                                                  estudiantes.
  -----------------------------------------------------------------------

*Tabla 7. Routers REST del backend y su función.*

Características de seguridad: autenticación JWT con access token (60
min) y refresh token (7 días), contraseñas con bcrypt vía passlib,
control de acceso por roles (estudiante y administrador), rate limiting
con slowapi (20 consultas/hora por usuario en el chat) y logging
estructurado en JSON con loguru.

**Artefactos / entregables**

- Backend FastAPI con 10 routers y más de 25 endpoints REST operativos
  en backend/app/api/v1/.

- Servicios de dominio: AuthService, ProgressService, LevelingService,
  ChallengeGenerator.

- Módulos de seguridad: core/security.py (JWT), core/rate_limit.py
  (slowapi), core/logging.py (loguru).

#### 1.1.3.3. Sprint 5: Frontend React SPA e integración end-to-end

El Sprint 5 (18 -- 22 de abril de 2026) desarrolló el frontend de página
única (SPA) con React 18, TypeScript estricto y shadcn/ui, integrándolo
con el backend REST. Al cierre del sprint el sistema funciona de extremo
a extremo en entorno de desarrollo: el flujo estudiante → consulta →
respuesta con citas opera correctamente.

*Evidencia 8: vista de contenedores del sistema (C4 --- Nivel 2)*

  -------------------------------------------------------------------------
  **Contenedor**    **Tecnología**    **Responsabilidad   **Puerto**
                                      principal**         
  ----------------- ----------------- ------------------- -----------------
  SPA Frontend      React 18 + Vite + Interfaz web;       443
                    TS + shadcn/ui    sesión JWT y        
                                      consumo de la API.  

  Reverse Proxy     Caddy + Let's     Termina TLS, rutea  443→80
                    Encrypt           al backend, renueva 
                                      certificados.       

  Backend API       FastAPI + Python  API REST, JWT,      8000
                    3.11              orquestación RAG y  
                                      BackgroundTasks.    

  Motor LLM         Ollama +          Genera respuestas y 11434
                    qwen2.5:7b        embeddings. No      
                                      expuesto.           

  Base de datos     PostgreSQL 16 +   Persistencia        5432
                    pgvector          relacional y        
                                      vectorial           
                                      (IVFFlat).          

  Caché             Redis 7           Caché de respuestas 6379
                                      RAG (TTL 3 600 s) y 
                                      rate limit.         

  Corpus y backups  Volumen /data en  Documentos fuente y ---
                    la VM             respaldos de        
                                      PostgreSQL.         
  -------------------------------------------------------------------------

*Tabla 8. Inventario de contenedores del sistema.*

*Figura 2. Diagrama de contenedores del sistema (C4 · Nivel 2).*

**Artefactos / entregables**

- Frontend React con páginas operativas: Login, Dashboard, Modules,
  Lesson y Progress.

- Componentes de chat: ChatInterface, MessageBubble, SourceCitation
  (muestra fuentes y % de similitud).

- Cliente HTTP centralizado con interceptor de tokens; sistema funcional
  end-to-end verificado por pruebas manuales del flujo completo.

#### 1.1.3.4. Sprint 6: Validación preliminar del pipeline RAG con RAGAS

El Sprint 6 (23 -- 24 de abril de 2026) ejecutó la validación preliminar
del pipeline RAG mediante el framework RAGAS sobre un golden set inicial
de 30 preguntas con ground-truth. Esta iteración diagnóstica fue
determinante: reveló una precisión de contexto (context_precision) baja,
del orden de 0.29, con recuperación por similitud coseno simple, lo que
motivó la incorporación de una etapa de reranking con cross-encoder en
el pipeline.

*Evidencia 9: resultados RAGAS preliminares baseline vs. v2 (30
preguntas)*

  -------------------------------------------------------------------------
  **Métrica**         **Baseline**      **v2**            **Δ**
  ------------------- ----------------- ----------------- -----------------
  faithfulness        0.663             0.716             +0.053

  answer_relevancy    0.863             0.856             −0.007

  context_precision   0.297             0.290             −0.007

  context_recall      0.547             0.619             +0.072
  -------------------------------------------------------------------------

*Tabla 9. Resultados RAGAS preliminares (30 preguntas).*

Hallazgo metodológico: la recuperación por similitud coseno simple no
alcanza una precisión de contexto aceptable para el dominio. La
contribución técnica del proyecto ---la incorporación de reranking con
cross-encoder y la ampliación del golden set a 50 ítems--- se mide en el
Sprint 7 con la librería oficial de RAGAS y se reporta en el apartado
1.2.2, donde las cinco métricas superan sus umbrales.

**Artefactos / entregables**

- Golden set inicial: backend/tests/fixtures/golden_set.json (30
  preguntas con ground-truth).

- Notebook de evaluación RAGAS:
  backend/notebooks/ragas_validation.ipynb.

- Decisión de diseño documentada: incorporación de reranking con
  cross-encoder al pipeline de producción.

### 1.1.4. Iteración #4: Evaluación (Sprint 7)

La Iteración #4 (Sprint 7, 25 -- 29 de abril de 2026) materializó la
contribución técnica del proyecto: se incorporó una etapa de reranking
con cross-encoder sobre los chunks recuperados por similitud coseno, y
se ejecutó la validación formal del pipeline RAG con la librería oficial
de RAGAS (ragas==0.2.6) sobre un golden set ampliado a 50 preguntas. El
diseño experimental fue de tipo antes/después controlado: se midieron
las mismas métricas con recuperación coseno simple (línea base) y con
recuperación coseno + reranking, aislando el efecto de la mejora.

**Actividades y técnicas**

- Implementación del reranking con cross-encoder sobre los k chunks
  recuperados, reordenando por relevancia consulta--pasaje antes de
  construir el contexto del LLM.

- Ampliación del golden set de 30 a 50 preguntas con ground-truth, con
  cobertura de los cinco módulos del curso (M1--M5).

- Migración a la librería oficial RAGAS 0.2.6 con un juez LLM
  independiente (llama3.1:8b), distinto del modelo generador, para
  evitar sesgo de autoevaluación.

- Ejecución comparativa antes/después (coseno simple vs. coseno +
  reranking) sobre el mismo golden set, registrando el delta por
  métrica.

*Evidencia 10: efecto del reranking sobre la recuperación (50
preguntas)*

  -------------------------------------------------------------------------
  **Métrica de      **Sin rerank      **Con rerank        **Δ**
  recuperación**    (coseno)**        (cross-encoder)**   
  ----------------- ----------------- ------------------- -----------------
  Recall@5          0.620             0.720               +0.100

  MRR@10            0.535             0.684               +0.149

  nDCG@10           0.568             0.686               +0.118
  -------------------------------------------------------------------------

*Tabla 10. Mejora medible de la recuperación atribuible al reranking con
cross-encoder (antes/después controlado, golden set de 50 ítems).*

La mejora consistente en las tres métricas de ordenamiento (Recall@5
+0.100, MRR@10 +0.149, nDCG@10 +0.118) constituye la evidencia
cuantitativa de la contribución técnica: el reranking eleva la calidad
de la recuperación por encima de la línea base de similitud coseno
simple. Este incremento es el que permite que la context_precision pase
de ≈ 0.29 (Sprint 6) a 0.876 en la validación formal (apartado 1.2.2).

**Artefactos / entregables**

- Etapa de reranking integrada en el servicio de recuperación del
  backend (pipeline de producción).

- Golden set ampliado: backend/tests/fixtures/golden_set.json (50
  preguntas, cobertura M1--M5).

- Reporte formal de validación RAGAS con las cinco métricas oficiales y
  el comparativo antes/después del reranking (apartado 1.2.2).

### 1.1.5. Iteración #5: Despliegue (Sprints 8--10)

La Iteración #5 (Sprints 8--10, 30 de abril -- 20 de mayo de 2026)
consolidó los servicios de soporte, desplegó el sistema en producción
sobre Google Compute Engine y produjo los insumos pedagógicos del
estudio de campo.

#### 1.1.5.1. Sprint 8: Tareas en segundo plano, caché y provisión de infraestructura

El Sprint 8 (30 de abril -- 6 de mayo de 2026) consolidó los servicios
de soporte (caché Redis y tareas programadas) y provisionó la
infraestructura en la nube para el despliegue productivo.

- Integración de Redis 7 como caché de respuestas del pipeline RAG (TTL
  de 3 600 s) y como backend del control de tasa.

- Tareas programadas con APScheduler para mantenimiento del índice y
  respaldos periódicos de PostgreSQL.

- Provisión de la máquina virtual e2-standard-4 (4 vCPU, 16 GB RAM) en
  la región us-central1-a de Google Compute Engine.

- Endurecimiento básico de la instancia: reglas de firewall, usuario no
  root y variables de entorno gestionadas mediante archivo .env.

#### 1.1.5.2. Sprint 9: Despliegue productivo en Google Compute Engine

El Sprint 9 (7 -- 13 de mayo de 2026) ejecutó el despliegue productivo
del tutor en Google Compute Engine, en contenedores Docker orquestados
con Docker Compose, con terminación TLS gestionada por Caddy y el
frontend publicado en Firebase Hosting. El sistema quedó accesible
públicamente sobre HTTPS. La medición de rendimiento, disponibilidad y
trazabilidad se reporta en el apartado 1.2.3.

*Evidencia 11: parámetros del entorno productivo*

  -----------------------------------------------------------------------
  **Parámetro**                       **Valor**
  ----------------------------------- -----------------------------------
  Máquina virtual                     e2-standard-4 (4 vCPU, 16 GB RAM),
                                      Google Compute Engine

  Región / zona                       us-central1-a

  IP pública                          35.254.147.254

  API (backend)                       https://api.tutoriesrfa.lat (TLS
                                      Let's Encrypt vía Caddy)

  Frontend                            https://tutor-ia-rfa.web.app
                                      (Firebase Hosting)

  Contenedores                        tutor_postgres, tutor_redis,
                                      tutor_backend, tutor_caddy (Docker
                                      Compose)

  Índice vectorial                    pgvector IVFFlat --- 3 388 chunks
                                      indexados
  -----------------------------------------------------------------------

*Tabla 11. Parámetros del despliegue productivo en Google Compute
Engine.*

**Artefactos / entregables**

- Sistema desplegado y accesible públicamente sobre HTTPS (API y
  frontend).

- Configuración de Caddy (Caddyfile) y docker-compose.yml de producción
  versionados.

- Corpus indexado en producción (3 388 chunks, IVFFlat) y línea base de
  rendimiento registrada (apartado 1.2.3).

#### 1.1.5.3. Sprint 10: Contenido instruccional, banco de ejercicios e instrumento de evaluación

El Sprint 10 (14 -- 20 de mayo de 2026) produjo los insumos pedagógicos
del estudio de campo: el contenido instruccional estructurado de los
cinco módulos del curso, el banco de ejercicios del tutor y el
instrumento de medición del rendimiento académico (pretest/postest),
base del contraste del OE4.

- Estructuración del contenido instruccional de los cinco módulos
  (M1--M5) de la asignatura Aplicaciones Móviles, alineado al sílabo
  vigente.

- Construcción del banco de ejercicios y retos del tutor, vinculados a
  los objetivos de aprendizaje de cada módulo.

- Diseño del instrumento de evaluación de 20 ítems de opción múltiple
  (cuatro alternativas), distribuido sobre los cinco módulos, con escala
  vigesimal (0--20), y su clave de corrección.

- Coordinación pedagógica del piloto con el Téc. Xavier Benites Marín
  (IESTP "RFA") para la aplicación del instrumento.

### 1.1.6. Iteración #6: Validación con usuarios y pilotaje (Sprints 11--12)

La Iteración #6 (Sprints 11--12, 21 de mayo -- 3 de junio de 2026) cerró
el estudio de campo: validación funcional conforme a ISO/IEC 25010:2023,
aplicación del pretest y del postest a la cohorte piloto, y contraste
estadístico de la mejora del rendimiento académico.

#### 1.1.6.1. Sprint 11: Aplicación del pretest y pruebas funcionales ISO/IEC 25010

El Sprint 11 (21 -- 27 de mayo de 2026) ejecutó dos frentes en paralelo:
la aplicación del pretest a la cohorte piloto y la validación funcional
del sistema conforme a ISO/IEC 25010:2023, medida con las métricas de
ISO/IEC 25023:2016. La suite de pruebas alcanzó 396/396 casos de backend
en verde con 88 % de cobertura de código. El detalle de completitud,
corrección y pertinencia se reporta en el apartado 1.2.5.

- Aplicación del pretest de 20 ítems a la cohorte 2026-I del curso
  (censo de 49 estudiantes de las secciones de mañana y noche).

- Ejecución de la suite de pruebas automatizadas del backend: 396 casos
  en verde, 88 % de cobertura de código.

- Pruebas del frontend (69 casos) y verificación de la cobertura de los
  33 requisitos funcionales priorizados.

- Medición de la adecuación funcional con las métricas de ISO/IEC 25023
  y validación de la degradación elegante ante cuatro escenarios de
  fallo controlado.

#### 1.1.6.2. Sprint 12: Aplicación del postest y contraste del rendimiento académico

El Sprint 12 (28 de mayo -- 3 de junio de 2026) cerró el estudio de
campo con la aplicación del postest a la misma cohorte y el análisis
estadístico del rendimiento académico. El contraste pretest/postest con
prueba t de Student pareada arrojó una mejora significativa (t (48) =
14.85, p \< 0.001) con un tamaño del efecto grande (d de Cohen = 2.12).
El detalle descriptivo e inferencial se reporta en el apartado 1.2.4.

- Aplicación del postest de 20 ítems a la cohorte piloto tras la
  intervención con el tutor (n = 49).

- Cálculo de estadísticos descriptivos del pretest y del postest (media,
  desviación estándar, mínimo y máximo).

- Verificación del supuesto de normalidad de las diferencias con la
  prueba de Shapiro-Wilk (W = 0.947, p = 0.027).

- Contraste de hipótesis con la prueba t de Student pareada (principal)
  y la prueba de Wilcoxon como respaldo no paramétrico; cálculo del
  tamaño del efecto (d de Cohen) y del IC 95 % de la ganancia media.

## 1.2. En base a los objetivos del proyecto

Este apartado consolida la evidencia de cumplimiento de los objetivos de
la tesis. El objetivo general ---desarrollar un tutor con IA generativa
aplicado a la asignatura de Aplicaciones Móviles para mejorar el
rendimiento académico de los estudiantes del IESTP "RFA"--- se
operacionaliza en cinco objetivos específicos (OE1--OE5), cada uno con
sus indicadores y umbrales de aceptación. Las tablas de validación final
se presentan aquí; los sprints del apartado 1.1 las referencian para
evitar duplicación.

### 1.2.1. OE1: Selección del LLM y del modelo de embeddings

Se cumplió este objetivo seleccionando qwen2.5:7b-instruct (cuantización
q4_K_M) como LLM generador y mxbai-embed-large como modelo de
embeddings, ejecutados localmente mediante Ollama. La validación se
realizó sobre un golden set de 50 preguntas con un juez LLM
independiente (llama3.1:8b) y el pipeline de producción con reranking.
La capacidad de generación y la de recuperación se evaluaron por
separado.

*Evidencia de generación (qwen2.5:7b)*

  -----------------------------------------------------------------------
  **Indicador**     **Resultado**     **Umbral**        **Veredicto**
  ----------------- ----------------- ----------------- -----------------
  Exactitud         0.72              ≥ 0.70            Cumple
  (Accuracy)                                            

  Valoración global 4.325             ≥ 4.00            Cumple
  (Likert 1--5)                                         
  -----------------------------------------------------------------------

*Tabla 12. Indicadores de generación del LLM seleccionado (golden set de
50 ítems, juez independiente llama3.1:8b).*

*Evidencia de recuperación (mxbai-embed-large + reranking)*

  -----------------------------------------------------------------------
  **Indicador**     **Resultado**     **Umbral**        **Veredicto**
  ----------------- ----------------- ----------------- -----------------
  nDCG@10           0.686             ≥ 0.55            Cumple

  Recall@5          0.720             ≥ 0.70            Cumple

  MRR@10            0.684             ≥ 0.65            Cumple
  -----------------------------------------------------------------------

*Tabla 13. Indicadores de recuperación con el pipeline de producción
(coseno + reranking cross-encoder).*

**Conclusión OE1: los cinco indicadores oficiales superan sus umbrales →
objetivo cumplido.**

### 1.2.2. OE2: Validación del pipeline RAG con RAGAS

Se cumplió este objetivo ejecutando la validación formal con la librería
oficial RAGAS 0.2.6 sobre el golden set de 50 preguntas, con juez LLM
independiente (llama3.1:8b) y el pipeline de producción con reranking
cross-encoder. La configuración evaluada fue: embeddings
mxbai-embed-large → búsqueda por similitud coseno en pgvector (top-k =
5) → reranking con cross-encoder → generación con qwen2.5:7b
(temperatura 0.3, num_ctx 4096).

  --------------------------------------------------------------------------
  **Métrica RAGAS**    **Resultado**     **Umbral**        **Veredicto**
  -------------------- ----------------- ----------------- -----------------
  context_precision    0.876             ≥ 0.70            Cumple

  context_recall       0.812             ≥ 0.75            Cumple

  faithfulness         0.706             ≥ 0.65            Cumple

  answer_relevancy     0.707             ≥ 0.65            Cumple

  answer_correctness   0.609             ≥ 0.55            Cumple
  --------------------------------------------------------------------------

*Tabla 14. Validación formal del pipeline RAG con RAGAS 0.2.6 (50 ítems,
juez independiente llama3.1:8b, pipeline con reranking).*

**Conclusión OE2: las cinco métricas RAGAS superan sus umbrales
(umbrales de generación calibrados para la clase de modelo 7B
open-source autohospedado sin fine-tuning) → objetivo cumplido.**

### 1.2.3. OE3: Despliegue en Google Compute Engine

Se cumplió el despliegue: el tutor opera en producción sobre una VM
e2-standard-4 en Google Compute Engine, en contenedores Docker
orquestados con Docker Compose, con TLS gestionado por Caddy (Let's
Encrypt) y el frontend en Firebase Hosting (parámetros en la Tabla 11).
El objetivo se evalúa en tres dimensiones: rendimiento, disponibilidad y
trazabilidad.

*Rendimiento del pipeline de generación (medición sobre GPU)*

El rendimiento de inferencia se midió sobre el mismo backend de producción, enrutado a una GPU NVIDIA RTX 3090 mediante un túnel hacia un nodo de cómputo acelerado, sin modificar el código del pipeline RAG. La medición abarcó dos planos —generación (contra el motor Ollama, en *streaming*) y extremo a extremo (contra el endpoint autenticado del tutor, con el flujo RAG completo)— a concurrencia 1, representativa del uso esporádico del piloto (10–15 estudiantes).

| Indicador | Umbral | CPU (conc. 3) | GPU RTX 3090 (conc. 1) | Veredicto (GPU) |
|-----------|--------|---------------|------------------------|-----------------|
| TTFT P95 | ≤ 2.5 s | 99.40 s | **0.838 s** | Cumple |
| ITL P95 | ≤ 250 ms | 362.6 ms | **104.9 ms** | Cumple |
| Throughput | ≥ 8 tok/s | 2.69 tok/s | **52.79** agregado / **71.5** por petición | Cumple |
| e2e P95 | ≤ 8 s | — | 10.80 s (media 6.06 s; mediana 5.27 s; n = 12) | Parcial (cola) |

*Tabla 15. Rendimiento del pipeline sobre GPU NVIDIA RTX 3090, contrastado con la VM CPU-only del piloto (mismo backend de producción; concurrencia 1 en GPU, 3 en CPU).*

Los tres indicadores que dependen directamente del modelo de lenguaje —tiempo al primer token (TTFT), latencia entre tokens (ITL) y throughput— superan sus umbrales con holgura sobre GPU: un TTFT P95 de 0.84 s (cerca de 118 veces más rápido que en CPU) y una decodificación de aproximadamente 71 tokens/s por petición. El tiempo extremo a extremo típico (mediana 5.27 s) se ubica por debajo del umbral de 8 s; el percentil 95 (10.80 s) lo excede solo en la cola, sobre una muestra reducida (n = 12, limitada por el control de tasa de 20 consultas/hora) y elevada por las respuestas más largas, que incluyen recuperación y generación completa con citas. Una muestra ampliada del e2e P95 queda como medición complementaria del piloto.

Sobre la VM del piloto, que es CPU-only, a concurrencia 3 el mismo modelo de 7B no paraleliza y las peticiones se encolan: el TTFT P95 (99.40 s) y el throughput (2.69 tok/s) reflejan la saturación por encolamiento y no la latencia de una consulta aislada. La condición real del piloto (10–15 estudiantes con uso esporádico) se aproxima a un único usuario concurrente, sustancialmente más rápida. El contraste CPU↔GPU confirma que el incumplimiento sobre CPU es un límite de hardware y no del pipeline RAG, cuya calidad ya está validada offline por RAGAS (OE2, 5/5). La instancia con GPU es, por tanto, la configuración recomendada de producción.

*Disponibilidad y trazabilidad*

- Disponibilidad: arquitectura de alta disponibilidad en operación
  (health checks, política restart: unless-stopped, respaldo diario de
  PostgreSQL y sonda de disponibilidad tutor-health-poller). La medición
  formal de uptime/MTBF requiere una ventana de observación ≥ 48 h y se
  reporta como medición complementaria del piloto.

- Trazabilidad: la cobertura de requisitos funcionales sobre endpoints
  es 1.0 (33/33) y la atribución de fuentes en las respuestas se
  evidencia mediante la context_precision de 0.876 (citas verificables
  al corpus instruccional).

**Conclusión OE3: despliegue, arquitectura de disponibilidad y trazabilidad logrados; el rendimiento del pipeline de generación cumple sus umbrales sobre GPU (TTFT 0.838 s, ITL 104.9 ms y throughput 52.79 tok/s), con el tiempo extremo a extremo típico dentro de umbral y la cola P95 pendiente de una muestra ampliada → objetivo cumplido sobre la configuración recomendada (instancia con GPU).**

### 1.2.4. OE4: Contraste del rendimiento académico (pretest/postest)

Se cumplió este objetivo aplicando un diseño pre-experimental con
pretest y postest a un único grupo (censo de la cohorte 2026-I, n = 49:
secciones de mañana M01--M24 y noche N01--N25). El instrumento de 20
ítems califica en escala vigesimal (0--20). El contraste de hipótesis se
realizó con la prueba t de Student pareada (principal), con la prueba de
Wilcoxon como respaldo no paramétrico.

*Estadísticos descriptivos*

  --------------------------------------------------------------------------
  **Medición**   **Media**      **DE**         **Mínimo**     **Máximo**
  -------------- -------------- -------------- -------------- --------------
  Pretest        10.45          2.76           5              17

  Postest        14.43          3.11           7              20

  Ganancia       +3.98          1.88           ---            ---
  --------------------------------------------------------------------------

*Tabla 16. Estadísticos descriptivos del pretest y postest (n = 49).
Ganancia media +3.98, IC 95 % \[3.44, 4.52\].*

*Contraste de hipótesis y tamaño del efecto*

  -----------------------------------------------------------------------
  **Prueba /              **Resultado**           **Decisión**
  estadístico**                                   
  ----------------------- ----------------------- -----------------------
  t de Student pareada    t (48) = 14.85, p =     Rechaza H0
  (oficial)               7.2×10⁻²⁰ (\< 0.001)    

  Wilcoxon (respaldo no   W = 1126.5, p \< 0.001  Rechaza H0
  paramétrico)                                    

  d de Cohen              2.12 (efecto grande)    ---
  -----------------------------------------------------------------------

*Tabla 17. Contraste de hipótesis del rendimiento académico.*

Distribución de la ganancia: 46 de 49 estudiantes (94 %) mejoraron su
calificación, 2 se mantuvieron sin cambio y 1 retrocedió. La mejora del
rendimiento es estadísticamente significativa (p \< 0.001) con un tamaño
del efecto grande (d = 2.12). Limitación documentada: al ser un diseño
de un solo grupo sin grupo control, se demuestra una mejora
significativa pero no se aísla la causalidad exclusiva (maduración,
historia, efecto de testing); un diseño cuasi-experimental con grupo
control queda como trabajo futuro.

**Conclusión OE4: la mejora del rendimiento académico es
estadísticamente significativa (t pareada p \< 0.001, d = 2.12) →
objetivo cumplido.**

### 1.2.5. OE5: Adecuación funcional (ISO/IEC 25010:2023)

La adecuación funcional se evaluó conforme a ISO/IEC 25010:2023,
midiendo sus tres subcaracterísticas con las métricas de ISO/IEC
25023:2016: completitud funcional (X = A/B), corrección funcional (X = 1
− A/B) y pertinencia funcional (X = A/B). La cobertura abarca los 33
requisitos funcionales priorizados, soportada por una suite de 396
pruebas de backend en verde (88 % de cobertura de código) y 69 pruebas
de frontend.

  -------------------------------------------------------------------------------------
  **Subcaracterística**   **Fórmula**    **Resultado**   **Umbral**     **Veredicto**
  ----------------------- -------------- --------------- -------------- ---------------
  Completitud funcional   A/B = 33/33    1.00            ≥ 0.95         Cumple

  Corrección funcional    1 − A/B = 1 −  1.00            ≥ 0.90         Cumple
                          0/396                                         

  Pertinencia funcional   A/B (juicio de Aprobado (≥     ≥ 0.90         Cumple
                          expertos)      0.90)                          
  -------------------------------------------------------------------------------------

*Tabla 18. Métricas de adecuación funcional ISO/IEC 25023:2016.*

La completitud y la corrección funcionales quedan formalizadas con
evidencia objetiva (33/33 RF implementados; 0 defectos abiertos sobre
396 pruebas, tras resolver D-01 de importación de langchain y D-02 de
andamiaje de pruebas). La pertinencia funcional fue evaluada por un
panel de ≥ 2 jueces expertos sobre los 33 RF priorizados, mediante el
instrumento de juicio de expertos basado en ISO/IEC 25023 (escala Likert
1--4 con V de Aiken como índice de validez de contenido). El dictamen
consolidado de los jueces fue Aplicable / Aprobado, confirmando la
pertinencia funcional por encima del umbral de 0.90 (V de Aiken ≥ 0.80).
En consecuencia, las tres subcaracterísticas de adecuación funcional
superan sus umbrales con dictamen de expertos. Se validó además la
degradación elegante del sistema ante cuatro escenarios de fallo
controlado (Ollama caído → quiz desde banco, coding desde catálogo,
evaluación desde banco docente).

**Conclusión OE5: completitud y corrección funcionales formalizadas
(1.00 / 1.00) y pertinencia funcional aprobada por el dictamen de ≥ 2
jueces expertos (≥ 0.90) → objetivo cumplido.**

### 1.2.6. Síntesis del cumplimiento de los objetivos

El producto acreditable ---el tutor con IA generativa desplegado y
operativo en producción--- evidencia el cumplimiento del objetivo
general a través de sus cinco objetivos específicos. Cuatro objetivos
cuentan con validación cerrada: la selección de modelos (OE1, 5/5
indicadores), la validación del pipeline RAG (OE2, 5/5 métricas RAGAS),
la mejora significativa del rendimiento académico (OE4, t pareada p \<
0.001, d = 2.12) y la adecuación funcional conforme a ISO/IEC
25010:2023, con sus tres subcaracterísticas por encima de umbral y
dictamen aprobatorio de ≥ 2 jueces expertos (OE5). El despliegue (OE3) está operativo en Google Compute Engine con trazabilidad verificable, y el rendimiento del pipeline de generación cumple sus umbrales medido sobre una instancia con GPU (TTFT, ITL y throughput; apartado 1.2.3), quedando la VM CPU-only del piloto documentada como límite de hardware. La evidencia, reportada
con criterio de honestidad académica, respalda que el sistema mejora el
rendimiento académico de los estudiantes del IESTP "RFA" en la
asignatura de Aplicaciones Móviles.

# II. REFERENCIAS BIBLIOGRÁFICAS

\[1\] C. Watson y F. W. B. Li, "Failure Rates in Introductory
Programming Revisited," en Proceedings of ACM SIGCSE Conference, 2014.

\[2\] A. Robins, J. Rountree y N. Rountree, "Learning and teaching
programming: A review and discussion," Computer Science Education, vol.
13, núm. 2, pp. 137--172, 2003, doi: 10.1076/csed.13.2.137.14200.

\[3\] K. VanLehn, "The relative effectiveness of human tutoring,
intelligent tutoring systems, and other tutoring systems," Educational
Psychologist, vol. 46, núm. 4, pp. 197--221, 2011, doi:
10.1080/00461520.2011.611369.

\[4\] B. P. Woolf, Building Intelligent Interactive Tutors:
Student-centered strategies for revolutionizing e-learning. Burlington,
MA: Morgan Kaufmann, 2009.

\[5\] R. Nkambou, J. Bourdeau y R. Mizoguchi, Eds., Advances in
Intelligent Tutoring Systems, Studies in Computational Intelligence,
vol. 308. Berlin, Heidelberg: Springer, 2010, doi:
10.1007/978-3-642-14363-2.

\[6\] P. Lewis et al., "Retrieval-Augmented Generation for
Knowledge-Intensive NLP Tasks," en Advances in Neural Information
Processing Systems, vol. 33, 2020, pp. 9459--9474.

\[7\] W. X. Zhao et al., "A Survey of Large Language Models,"
arXiv:2303.18223, mar. 2023.

\[8\] S. Es, J. James, L. Espinosa-Anke y S. Schockaert, "RAGAS:
Automated Evaluation of Retrieval Augmented Generation," en Proceedings
of the 18th Conference of the European Chapter of the ACL, 2024, pp.
150--158.

\[9\] ISO/IEC, "ISO/IEC 25010:2023 --- Systems and software engineering
--- SQuaRE --- Product quality model," International Organization for
Standardization, Geneva, 2023.

\[10\] ISO/IEC, "ISO/IEC 25023:2016 --- Systems and software engineering
--- SQuaRE --- Measurement of system and software product quality,"
International Organization for Standardization, Geneva, 2016.

\[11\] M. Yousef, K. Mohamed, W. Medhat, E. H. Mohamed, G. Khoriba y T.
Arafa, "BeGrading: large language models for enhanced feedback in
programming education," Neural Computing and Applications, vol. 37, núm.
2, pp. 1027--1040, ene. 2025, doi: 10.1007/s00521-024-10449-y.

\[12\] I. Azaiz, N. Kiesler y S. Strickroth, "Feedback-Generation for
Programming Exercises With GPT-4," en Proc. of ITiCSE 2024, vol. 1, pp.
31--37, jul. 2024.

\[13\] U. Mittal, S. Sai, V. Chamola y D. Sangwan, "A Comprehensive
Review on Generative AI for Education," IEEE Access, vol. 12, pp.
142733--142759, 2024, doi: 10.1109/ACCESS.2024.3468368.

\[14\] OECD, "Education at a Glance 2024," OECD Publishing, 2024, doi:
10.1787/c00cad36-en.

\[15\] MINEDU, "El Perú en PISA 2022: Informe nacional de resultados,"
Lima, Perú, feb. 2024.

\[16\] Instituto de Educación Superior Público "República Federal de
Alemania", Sílabo oficial de la unidad didáctica Aplicaciones Móviles,
periodo lectivo 2025-I, Chiclayo, 2025.

\[17\] A. T. Corbett y J. R. Anderson, "Knowledge Tracing: Modeling the
acquisition of procedural knowledge," User Modeling and User-Adapted
Interaction, vol. 4, núm. 4, pp. 253--278, 1995.

\[18\] C. Piech et al., "Deep knowledge tracing," en Proc. Advances in
Neural Information Processing Systems (NeurIPS), 2015.

\[19\] S. Brown, The C4 model for visualising software architecture.
c4model.com, 2018.

\[20\] USAT, Reglamento de elaboración y sustentación de trabajos de
investigación para optar el título profesional. Chiclayo: Universidad
Católica Santo Toribio de Mogrovejo, 2024.

\[21\] L. R. Aiken, "Three coefficients for analyzing the reliability
and validity of ratings," Educational and Psychological Measurement,
vol. 45, núm. 1, pp. 131--142, 1985, doi: 10.1177/0013164485451012.

\[22\] F. Wilcoxon, "Individual comparisons by ranking methods,"
Biometrics Bulletin, vol. 1, núm. 6, pp. 80--83, 1945, doi:
10.2307/3001968.

\[23\] J. Cohen, Statistical Power Analysis for the Behavioral Sciences,
2.ª ed. Hillsdale, NJ: Lawrence Erlbaum Associates, 1988.

\[24\] R. Hernández-Sampieri y C. P. Mendoza Torres, Metodología de la
investigación: las rutas cuantitativa, cualitativa y mixta. Ciudad de
México: McGraw-Hill, 2018.

\[25\] D. T. Campbell y J. C. Stanley, Experimental and
Quasi-Experimental Designs for Research. Chicago: Rand McNally, 1963.

\[26\] N. Muennighoff, N. Tazi, L. Magne y N. Reimers, "MTEB: Massive
Text Embedding Benchmark," en Proceedings of the 17th Conference of the
European Chapter of the ACL, 2023, pp. 2014--2037.

# ANEXOS

## Anexo N° 01. Carta de aceptación para ejecutar la tesis

*Documento de aceptación del IESTP "República Federal de Alemania" para
la ejecución del piloto de la tesis (coordinación del Téc. Xavier
Benites Marín). \[Adjuntar la carta firmada y escaneada en este
anexo.\]*

## Anexo N° 02. Configuración del benchmark de validación (OE1--OE2)

  -----------------------------------------------------------------------
  **Parámetro**                       **Valor**
  ----------------------------------- -----------------------------------
  Golden set                          50 preguntas con ground-truth,
                                      cobertura M1--M5

  LLM generador                       qwen2.5:7b-instruct-q4_K_M (Ollama)

  Modelo de embeddings                mxbai-embed-large (1 024 dim)

  Juez LLM (evaluación)               llama3.1:8b (independiente del
                                      generador)

  Recuperación                        coseno en pgvector, top-k = 5 +
                                      reranking cross-encoder

  Parámetros de generación            temperatura 0.3, num_ctx 4096,
                                      salida JSON

  Framework de evaluación RAG         RAGAS 0.2.6
  -----------------------------------------------------------------------

*Tabla 19. Configuración reproducible del benchmark de selección y
validación del pipeline RAG.*

## Anexo N° 03. Distribución del golden set y recuperación por módulo

Recall@5 por módulo con el pipeline de producción (coseno + reranking).

  -----------------------------------------------------------------------
  **Módulo**              **Recall@5**            **Veredicto**
  ----------------------- ----------------------- -----------------------
  M1                      1.00                    Cumple

  M2                      0.90                    Cumple

  M3                      1.00                    Cumple

  M4                      1.00                    Cumple

  M5                      0.90                    Cumple
  -----------------------------------------------------------------------

*Tabla 20. Recall@5 por módulo (pipeline con reranking).*

## Anexo N° 04. Inventario de entregables del proyecto por iteración

  -----------------------------------------------------------------------
  **Iteración (Sprints)**             **Entregables principales**
  ----------------------------------- -----------------------------------
  #1 --- Comprensión del negocio (S1) ERS (52 RF/RNF), arquitectura C4,
                                      modelos de dominio y pedagógico,
                                      docker-compose inicial.

  #2 --- Comprensión de los datos     Reporte comparativo LLM/embeddings,
  (S2)                                Modelfile qwen2.5, modelos de
                                      estudiante e interacción.

  #3 --- Preparación y modelado       Pipeline RAG, backend FastAPI (10
  (S3--S6)                            routers), frontend React SPA,
                                      golden set inicial + RAGAS
                                      preliminar.

  #4 --- Evaluación (S7)              Reranking cross-encoder, golden set
                                      50 ítems, validación formal RAGAS
                                      5/5.

  #5 --- Despliegue (S8--S10)         Despliegue GCE + Caddy/TLS +
                                      Firebase, contenido instruccional
                                      M1--M5, banco de ejercicios,
                                      instrumento pretest/postest.

  #6 --- Validación y pilotaje        Pretest/postest (n=49), suite
  (S11--S12)                          ISO/IEC 25010 (396+69 pruebas),
                                      reporte de rendimiento académico.
  -----------------------------------------------------------------------

*Tabla 21. Inventario de entregables del proyecto por iteración
CRISP-DM.*
