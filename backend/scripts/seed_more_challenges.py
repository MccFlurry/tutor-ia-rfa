"""
seed_more_challenges.py — 15 desafíos adicionales para rebalancear M4 + M5
(extiende seed_extra_challenges.py para llegar a 45 challenges catálogo).

Idempotente: verifica por (topic_id, title) antes de insertar.
Ejecutar:
    docker compose exec backend python scripts/seed_more_challenges.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.topic import Topic
from app.models.coding import CodingChallenge


engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


MORE_CHALLENGES: dict[str, list[dict]] = {
    # =============================================================
    # M4 · Componentes Android y Gestión de Datos (+7)
    # =============================================================
    "Activities y el Ciclo de Vida de Android": [
        {
            "title": "Tracker de Ciclo de Vida",
            "difficulty": "medium",
            "description": """## Tracker de Ciclo de Vida

Modela las transiciones del ciclo de vida de una Activity y detecta combinaciones inválidas.

**Requisitos:**
- Enum `LifecycleState { CREATED, STARTED, RESUMED, PAUSED, STOPPED, DESTROYED }`.
- Clase `LifecycleTracker` con `var state` y método `transition(to: LifecycleState)` que:
  - Permite avanzar solo a estados adyacentes (CREATED→STARTED, STARTED→RESUMED, etc.).
  - Lanza `IllegalStateException("Transición inválida $from → $to")` si no.
- En `main()` simula: CREATED → STARTED → RESUMED → PAUSED → STOPPED → DESTROYED y demuestra una transición inválida.""",
            "initial_code": """enum class LifecycleState { CREATED, STARTED, RESUMED, PAUSED, STOPPED, DESTROYED }

class LifecycleTracker {
    var state: LifecycleState = LifecycleState.CREATED
        private set
    fun transition(to: LifecycleState) { TODO() }
}

fun main() {
    val t = LifecycleTracker()
    // demo + caso inválido
}""",
            "solution_code": """enum class LifecycleState { CREATED, STARTED, RESUMED, PAUSED, STOPPED, DESTROYED }

class LifecycleTracker {
    var state: LifecycleState = LifecycleState.CREATED
        private set

    private val transitions = mapOf(
        LifecycleState.CREATED to setOf(LifecycleState.STARTED, LifecycleState.DESTROYED),
        LifecycleState.STARTED to setOf(LifecycleState.RESUMED, LifecycleState.STOPPED),
        LifecycleState.RESUMED to setOf(LifecycleState.PAUSED),
        LifecycleState.PAUSED to setOf(LifecycleState.RESUMED, LifecycleState.STOPPED),
        LifecycleState.STOPPED to setOf(LifecycleState.STARTED, LifecycleState.DESTROYED),
        LifecycleState.DESTROYED to emptySet(),
    )

    fun transition(to: LifecycleState) {
        val allowed = transitions[state] ?: emptySet()
        check(to in allowed) { "Transición inválida $state → $to" }
        println("$state → $to")
        state = to
    }
}

fun main() {
    val t = LifecycleTracker()
    t.transition(LifecycleState.STARTED)
    t.transition(LifecycleState.RESUMED)
    t.transition(LifecycleState.PAUSED)
    t.transition(LifecycleState.STOPPED)
    t.transition(LifecycleState.DESTROYED)
    try { t.transition(LifecycleState.RESUMED) } catch (e: IllegalStateException) {
        println("Capturado: ${e.message}")
    }
}""",
            "hints": "Define un map estado→set de destinos válidos. Usa `check` para lanzar IllegalStateException.",
        },
        {
            "title": "Stack de Activities con Back",
            "difficulty": "hard",
            "description": """## Stack de Activities con Botón Atrás

Modela la navegación tipo Android con back stack.

**Requisitos:**
- Clase `ActivityStack` que mantenga un stack de nombres de Activity.
- Métodos:
  - `startActivity(name: String, clearTop: Boolean = false)` → si `clearTop=true` y existe, elimina todo lo de encima y la trae al tope.
  - `pressBack(): String?` → quita el tope y retorna nuevo tope (null si vacío).
  - `current(): String?`
- En `main()` simula: Home → Detail → Profile → back → Detail → startActivity("Home", clearTop=true) → debe quedar solo "Home".""",
            "initial_code": """class ActivityStack {
    private val stack = ArrayDeque<String>()
    fun startActivity(name: String, clearTop: Boolean = false) { TODO() }
    fun pressBack(): String? { TODO() }
    fun current(): String? = stack.lastOrNull()
}

fun main() {
    val s = ActivityStack()
    s.startActivity("Home"); s.startActivity("Detail"); s.startActivity("Profile")
    println(s.current())
    s.pressBack(); println(s.current())
    s.startActivity("Home", clearTop = true)
    println("Final: ${s.current()}")
}""",
            "solution_code": """class ActivityStack {
    private val stack = ArrayDeque<String>()

    fun startActivity(name: String, clearTop: Boolean = false) {
        if (clearTop) {
            val idx = stack.indexOf(name)
            if (idx >= 0) {
                while (stack.size > idx + 1) stack.removeLast()
                return
            }
        }
        stack.addLast(name)
    }

    fun pressBack(): String? {
        if (stack.isNotEmpty()) stack.removeLast()
        return stack.lastOrNull()
    }

    fun current(): String? = stack.lastOrNull()
}

fun main() {
    val s = ActivityStack()
    s.startActivity("Home"); s.startActivity("Detail"); s.startActivity("Profile")
    println(s.current())              // Profile
    s.pressBack(); println(s.current()) // Detail
    s.startActivity("Home", clearTop = true)
    println("Final: ${s.current()}")    // Home
}""",
            "hints": "`ArrayDeque` soporta `addLast`, `removeLast`, `indexOf`. Para clearTop, busca y poda el tope sobrante.",
        },
    ],

    "Navegación entre Pantallas con Intents": [
        {
            "title": "Intent Filter para Deeplinks",
            "difficulty": "medium",
            "description": """## Resolver de Deeplinks

Diseña la lógica que mapea una URI tipo deeplink a una Activity destino.

**Requisitos:**
- Data class `DeeplinkRule(val scheme: String, val host: String, val pathPrefix: String, val activity: String)`.
- Clase `DeeplinkResolver(val rules: List<DeeplinkRule>)` con `resolve(uri: String): String?`.
- Soporta URIs tipo `tutorrfa://app/topic/12` y `https://tutorrfa.app/quiz/3`.
- Retorna nombre de Activity o `null` si nada coincide.

**Ejemplo:**
```
resolve("tutorrfa://app/topic/12") → "TopicActivity"
resolve("https://tutorrfa.app/quiz/3") → "QuizActivity"
resolve("https://otro.com/foo") → null
```""",
            "initial_code": """data class DeeplinkRule(val scheme: String, val host: String, val pathPrefix: String, val activity: String)

class DeeplinkResolver(val rules: List<DeeplinkRule>) {
    fun resolve(uri: String): String? { TODO() }
}

fun main() {
    val resolver = DeeplinkResolver(listOf(
        DeeplinkRule("tutorrfa", "app", "/topic", "TopicActivity"),
        DeeplinkRule("https", "tutorrfa.app", "/quiz", "QuizActivity"),
    ))
    println(resolver.resolve("tutorrfa://app/topic/12"))
    println(resolver.resolve("https://tutorrfa.app/quiz/3"))
    println(resolver.resolve("https://otro.com/foo"))
}""",
            "solution_code": """data class DeeplinkRule(val scheme: String, val host: String, val pathPrefix: String, val activity: String)

class DeeplinkResolver(val rules: List<DeeplinkRule>) {
    private val regex = Regex("^(\\\\w+)://([^/]+)(/.*)?$")

    fun resolve(uri: String): String? {
        val m = regex.matchEntire(uri) ?: return null
        val (scheme, host, path) = Triple(m.groupValues[1], m.groupValues[2], m.groupValues.getOrNull(3) ?: "")
        return rules.firstOrNull { it.scheme == scheme && it.host == host && path.startsWith(it.pathPrefix) }?.activity
    }
}

fun main() {
    val resolver = DeeplinkResolver(listOf(
        DeeplinkRule("tutorrfa", "app", "/topic", "TopicActivity"),
        DeeplinkRule("https", "tutorrfa.app", "/quiz", "QuizActivity"),
    ))
    println(resolver.resolve("tutorrfa://app/topic/12"))
    println(resolver.resolve("https://tutorrfa.app/quiz/3"))
    println(resolver.resolve("https://otro.com/foo"))
}""",
            "hints": "Parsea URI con Regex `^(\\\\w+)://([^/]+)(/.*)?$`. Usa `firstOrNull` con `startsWith` para match de prefijo.",
        },
    ],

    "Almacenamiento Local: SharedPreferences y SQLite": [
        {
            "title": "Migración de Esquema SQLite",
            "difficulty": "hard",
            "description": """## Migración de Esquema SQLite

Simula la lógica de migración entre versiones del esquema.

**Requisitos:**
- Clase `Migration(val fromVersion: Int, val toVersion: Int, val sql: List<String>)`.
- Clase `MigrationRunner(val migrations: List<Migration>)` con:
  - `fun migrate(currentVersion: Int, targetVersion: Int): List<String>` → retorna las sentencias SQL en orden.
  - Lanza `IllegalArgumentException("No path")` si falta una migración intermedia.
- Demuestra: migrar de v1 a v3 ejecutando dos migraciones encadenadas.""",
            "initial_code": """data class Migration(val fromVersion: Int, val toVersion: Int, val sql: List<String>)

class MigrationRunner(val migrations: List<Migration>) {
    fun migrate(currentVersion: Int, targetVersion: Int): List<String> { TODO() }
}

fun main() {
    val runner = MigrationRunner(listOf(
        Migration(1, 2, listOf("ALTER TABLE notes ADD COLUMN created_at INTEGER")),
        Migration(2, 3, listOf("CREATE INDEX idx_notes_created ON notes(created_at)")),
    ))
    runner.migrate(1, 3).forEach(::println)
}""",
            "solution_code": """data class Migration(val fromVersion: Int, val toVersion: Int, val sql: List<String>)

class MigrationRunner(val migrations: List<Migration>) {
    fun migrate(currentVersion: Int, targetVersion: Int): List<String> {
        val plan = mutableListOf<String>()
        var v = currentVersion
        while (v < targetVersion) {
            val step = migrations.firstOrNull { it.fromVersion == v }
                ?: throw IllegalArgumentException("No path from v$v")
            plan += step.sql
            v = step.toVersion
        }
        return plan
    }
}

fun main() {
    val runner = MigrationRunner(listOf(
        Migration(1, 2, listOf("ALTER TABLE notes ADD COLUMN created_at INTEGER")),
        Migration(2, 3, listOf("CREATE INDEX idx_notes_created ON notes(created_at)")),
    ))
    runner.migrate(1, 3).forEach(::println)
}""",
            "hints": "Itera de currentVersion hacia targetVersion buscando la migración con `fromVersion == v`. Acumula SQL.",
        },
    ],

    "Consumo de APIs REST y Manejo de JSON": [
        {
            "title": "Parser de Respuesta Paginada",
            "difficulty": "medium",
            "description": """## Parser de Respuesta Paginada

Modela la respuesta típica `{ data: [...], page, total_pages }`.

**Requisitos:**
- Data class `Page<T>(val data: List<T>, val page: Int, val totalPages: Int, val hasNext: Boolean)`.
- Función genérica `parsePage(json: String, mapper: (org.json.JSONObject) -> T): Page<T>`.
- `hasNext` se calcula como `page < totalPages`.
- En `main()` parsea un JSON con usuarios y otro con productos.""",
            "initial_code": """import org.json.JSONObject

data class Page<T>(val data: List<T>, val page: Int, val totalPages: Int, val hasNext: Boolean)

fun <T> parsePage(json: String, mapper: (JSONObject) -> T): Page<T> { TODO() }

data class User(val id: Int, val name: String)

fun main() {
    val json = ""\"{"data":[{"id":1,"name":"Ana"},{"id":2,"name":"Beto"}],"page":1,"total_pages":3}""\"
    val page = parsePage(json) { User(it.getInt("id"), it.getString("name")) }
    println(page)
}""",
            "solution_code": """import org.json.JSONObject

data class Page<T>(val data: List<T>, val page: Int, val totalPages: Int, val hasNext: Boolean)

fun <T> parsePage(json: String, mapper: (JSONObject) -> T): Page<T> {
    val obj = JSONObject(json)
    val arr = obj.getJSONArray("data")
    val items = (0 until arr.length()).map { mapper(arr.getJSONObject(it)) }
    val page = obj.getInt("page")
    val total = obj.getInt("total_pages")
    return Page(items, page, total, hasNext = page < total)
}

data class User(val id: Int, val name: String)

fun main() {
    val json = ""\"{"data":[{"id":1,"name":"Ana"},{"id":2,"name":"Beto"}],"page":1,"total_pages":3}""\"
    val page = parsePage(json) { User(it.getInt("id"), it.getString("name")) }
    println(page)
}""",
            "hints": "Usa una función genérica con tipo `<T>`. El mapper convierte cada JSONObject a T. `hasNext` evalúa `page < totalPages`.",
        },
    ],

    "Retrofit para Servicios Web en Android": [
        {
            "title": "Interceptor de Auth con Bearer Token",
            "difficulty": "medium",
            "description": """## Interceptor Bearer Token

Simula un OkHttp Interceptor que adjunta `Authorization: Bearer <token>` a cada request.

**Requisitos:**
- Data class `Request(val url: String, val headers: Map<String, String> = emptyMap())`.
- Data class `Response(val status: Int, val body: String)`.
- Interface `Interceptor { fun intercept(req: Request, next: (Request) -> Response): Response }`.
- Clase `AuthInterceptor(private val tokenProvider: () -> String?) : Interceptor`.
  - Si el provider devuelve token no nulo, añade header `Authorization=Bearer $token`.
  - Si es nulo, deja la request intacta.
- En `main()` demuestra con tokenProvider que retorna "abc123" y otro que retorna null.""",
            "initial_code": """data class Request(val url: String, val headers: Map<String, String> = emptyMap())
data class Response(val status: Int, val body: String)

interface Interceptor {
    fun intercept(req: Request, next: (Request) -> Response): Response
}

class AuthInterceptor(private val tokenProvider: () -> String?) : Interceptor {
    override fun intercept(req: Request, next: (Request) -> Response): Response { TODO() }
}

fun main() {
    val mockServer: (Request) -> Response = { Response(200, "headers=${it.headers}") }
    println(AuthInterceptor { "abc123" }.intercept(Request("/api/me"), mockServer))
    println(AuthInterceptor { null }.intercept(Request("/api/public"), mockServer))
}""",
            "solution_code": """data class Request(val url: String, val headers: Map<String, String> = emptyMap())
data class Response(val status: Int, val body: String)

interface Interceptor {
    fun intercept(req: Request, next: (Request) -> Response): Response
}

class AuthInterceptor(private val tokenProvider: () -> String?) : Interceptor {
    override fun intercept(req: Request, next: (Request) -> Response): Response {
        val token = tokenProvider() ?: return next(req)
        val newReq = req.copy(headers = req.headers + ("Authorization" to "Bearer $token"))
        return next(newReq)
    }
}

fun main() {
    val mockServer: (Request) -> Response = { Response(200, "headers=${it.headers}") }
    println(AuthInterceptor { "abc123" }.intercept(Request("/api/me"), mockServer))
    println(AuthInterceptor { null }.intercept(Request("/api/public"), mockServer))
}""",
            "hints": "Usa `req.copy(headers = ...)` para mantener inmutabilidad. Combina maps con `+`.",
        },
        {
            "title": "Sealed Class para Errores HTTP",
            "difficulty": "hard",
            "description": """## Modelado de Errores con Sealed Class

Aplica el patrón Result/sealed-class para respuestas HTTP.

**Requisitos:**
- Sealed class `ApiResult<out T>`:
  - `data class Success<T>(val data: T) : ApiResult<T>()`
  - `data class HttpError(val code: Int, val message: String) : ApiResult<Nothing>()`
  - `data class NetworkError(val cause: String) : ApiResult<Nothing>()`
  - `object Loading : ApiResult<Nothing>()`
- Función `mapStatus(code: Int, body: String): ApiResult<String>`:
  - 200..299 → Success(body)
  - 400..599 → HttpError(code, body)
  - else → NetworkError("código inesperado $code")
- En `main()` muestra los 3 casos.""",
            "initial_code": """sealed class ApiResult<out T> {
    data class Success<T>(val data: T) : ApiResult<T>()
    data class HttpError(val code: Int, val message: String) : ApiResult<Nothing>()
    data class NetworkError(val cause: String) : ApiResult<Nothing>()
    object Loading : ApiResult<Nothing>()
}

fun mapStatus(code: Int, body: String): ApiResult<String> { TODO() }

fun main() {
    listOf(200 to "OK", 404 to "Not Found", -1 to "down").forEach { (c, b) ->
        println(mapStatus(c, b))
    }
}""",
            "solution_code": """sealed class ApiResult<out T> {
    data class Success<T>(val data: T) : ApiResult<T>()
    data class HttpError(val code: Int, val message: String) : ApiResult<Nothing>()
    data class NetworkError(val cause: String) : ApiResult<Nothing>()
    object Loading : ApiResult<Nothing>()
}

fun mapStatus(code: Int, body: String): ApiResult<String> = when (code) {
    in 200..299 -> ApiResult.Success(body)
    in 400..599 -> ApiResult.HttpError(code, body)
    else -> ApiResult.NetworkError("código inesperado $code")
}

fun main() {
    listOf(200 to "OK", 404 to "Not Found", -1 to "down").forEach { (c, b) ->
        println(mapStatus(c, b))
    }
}""",
            "hints": "Usa `when` con rangos `in 200..299`. `out T` permite covarianza (Success<Int> es ApiResult<Number>).",
        },
    ],

    # =============================================================
    # M5 · Funcionalidades Avanzadas y Despliegue (+8)
    # =============================================================
    "Depuración de Aplicaciones con Logcat": [
        {
            "title": "Filtro de Logs por Tag y Nivel",
            "difficulty": "medium",
            "description": """## Filtro Logcat por Tag y Nivel

Imita los filtros que aplicas en Logcat (`Tag:MainActivity Level:Warn`).

**Requisitos:**
- Data class `LogEntry(val timestamp: Long, val tag: String, val level: String, val message: String)`.
- Función `filterLogs(entries: List<LogEntry>, tag: String?, minLevel: String?): List<LogEntry>`.
- Orden niveles: VERBOSE < DEBUG < INFO < WARN < ERROR.
- `tag == null` ⇒ no filtra por tag; `minLevel == null` ⇒ no filtra por nivel.
- En `main()`, crea 5 logs variados y filtra por tag="Auth" + minLevel="WARN".""",
            "initial_code": """data class LogEntry(val timestamp: Long, val tag: String, val level: String, val message: String)

fun filterLogs(entries: List<LogEntry>, tag: String?, minLevel: String?): List<LogEntry> { TODO() }

fun main() {
    val logs = listOf(
        LogEntry(1, "Auth", "INFO", "Login ok"),
        LogEntry(2, "Auth", "ERROR", "Token expirado"),
        LogEntry(3, "UI",   "WARN", "Botón sin id"),
        LogEntry(4, "Auth", "WARN", "Sesión cercana a expirar"),
        LogEntry(5, "Net",  "DEBUG", "GET /me"),
    )
    filterLogs(logs, "Auth", "WARN").forEach(::println)
}""",
            "solution_code": """data class LogEntry(val timestamp: Long, val tag: String, val level: String, val message: String)

private val LEVEL_ORDER = listOf("VERBOSE", "DEBUG", "INFO", "WARN", "ERROR")

fun filterLogs(entries: List<LogEntry>, tag: String?, minLevel: String?): List<LogEntry> {
    val minIdx = minLevel?.let { LEVEL_ORDER.indexOf(it) } ?: -1
    return entries.filter {
        (tag == null || it.tag == tag) && (minIdx < 0 || LEVEL_ORDER.indexOf(it.level) >= minIdx)
    }
}

fun main() {
    val logs = listOf(
        LogEntry(1, "Auth", "INFO", "Login ok"),
        LogEntry(2, "Auth", "ERROR", "Token expirado"),
        LogEntry(3, "UI",   "WARN", "Botón sin id"),
        LogEntry(4, "Auth", "WARN", "Sesión cercana a expirar"),
        LogEntry(5, "Net",  "DEBUG", "GET /me"),
    )
    filterLogs(logs, "Auth", "WARN").forEach(::println)
}""",
            "hints": "Define `LEVEL_ORDER` y compara `indexOf`. Maneja nulos con `?:` y operador early-return.",
        },
        {
            "title": "Logger Persistente con Rotación",
            "difficulty": "hard",
            "description": """## Logger con Rotación de Archivos

Simula un logger que rota archivos al alcanzar capacidad.

**Requisitos:**
- Clase `RotatingLogger(val maxLinesPerFile: Int)`:
  - Lista interna `files: MutableList<MutableList<String>>` (cada elemento es un archivo).
  - `fun log(line: String)`: agrega la línea al archivo actual; si éste alcanza `maxLinesPerFile` líneas, crea archivo nuevo.
  - `fun totalLines(): Int`.
  - `fun fileCount(): Int`.
- En `main()`: logger con maxLinesPerFile=3, escribe 7 líneas → debe haber 3 archivos (3+3+1 líneas).""",
            "initial_code": """class RotatingLogger(val maxLinesPerFile: Int) {
    private val files: MutableList<MutableList<String>> = mutableListOf(mutableListOf())
    fun log(line: String) { TODO() }
    fun totalLines(): Int = TODO()
    fun fileCount(): Int = files.size
}

fun main() {
    val logger = RotatingLogger(3)
    repeat(7) { logger.log("evento $it") }
    println("Archivos: ${logger.fileCount()}, líneas: ${logger.totalLines()}")
}""",
            "solution_code": """class RotatingLogger(val maxLinesPerFile: Int) {
    private val files: MutableList<MutableList<String>> = mutableListOf(mutableListOf())

    fun log(line: String) {
        val current = files.last()
        if (current.size >= maxLinesPerFile) {
            files.add(mutableListOf(line))
        } else {
            current.add(line)
        }
    }

    fun totalLines(): Int = files.sumOf { it.size }
    fun fileCount(): Int = files.size
}

fun main() {
    val logger = RotatingLogger(3)
    repeat(7) { logger.log("evento $it") }
    println("Archivos: ${logger.fileCount()}, líneas: ${logger.totalLines()}")
}""",
            "hints": "Chequea `files.last().size >= maxLinesPerFile` antes de agregar. Usa `sumOf` para totalizar.",
        },
    ],

    "Pruebas Unitarias con JUnit en Android": [
        {
            "title": "Mocking Manual con Interface",
            "difficulty": "medium",
            "description": """## Mocking Manual sin Mockito

Antes de adoptar Mockito, dominar el mocking manual es esencial.

**Requisitos:**
- Interface `UserRepository { suspend fun findById(id: Int): String? }`.
- Clase `UserService(private val repo: UserRepository)` con `suspend fun greet(id: Int): String`:
  - Si `repo.findById(id)` devuelve nombre → "Hola $nombre".
  - Si devuelve null → "Usuario no encontrado".
- Crea `FakeUserRepository(private val users: Map<Int, String>) : UserRepository`.
- En `main()`+`runBlocking`: prueba 2 casos (id válido + id inexistente) y verifica con `check`.""",
            "initial_code": """import kotlinx.coroutines.runBlocking

interface UserRepository {
    suspend fun findById(id: Int): String?
}

class UserService(private val repo: UserRepository) {
    suspend fun greet(id: Int): String { TODO() }
}

// FakeUserRepository aquí

fun main() = runBlocking {
    // Demo + asserts con check
}""",
            "solution_code": """import kotlinx.coroutines.runBlocking

interface UserRepository {
    suspend fun findById(id: Int): String?
}

class UserService(private val repo: UserRepository) {
    suspend fun greet(id: Int): String {
        val name = repo.findById(id) ?: return "Usuario no encontrado"
        return "Hola $name"
    }
}

class FakeUserRepository(private val users: Map<Int, String>) : UserRepository {
    override suspend fun findById(id: Int): String? = users[id]
}

fun main() = runBlocking {
    val fake = FakeUserRepository(mapOf(1 to "Ana"))
    val svc = UserService(fake)
    check(svc.greet(1) == "Hola Ana") { "fallo greet válido" }
    check(svc.greet(99) == "Usuario no encontrado") { "fallo fallback" }
    println("✓ Tests pasan")
}""",
            "hints": "Inyectar la interface en el constructor permite usar fake en tests. Para coroutines, envolver en runBlocking.",
        },
        {
            "title": "Test Parametrizado de Validador",
            "difficulty": "medium",
            "description": """## Test Parametrizado

Aplica el patrón parametrizado para reducir duplicación.

**Requisitos:**
- Función `validarPassword(pwd: String): List<String>` que retorne errores:
  - longitud < 8 → "Mínimo 8 caracteres"
  - sin mayúscula → "Necesita al menos 1 mayúscula"
  - sin dígito → "Necesita al menos 1 dígito"
- Vacío si todo OK.
- En `main()` corre una tabla de casos: `(password, expectedErrorsCount)` con 5+ filas y verifica cada uno con `check`.""",
            "initial_code": """fun validarPassword(pwd: String): List<String> { TODO() }

fun main() {
    val casos = listOf(
        "abc" to 3,
        "abcdefgh" to 2,
        "Abcdefgh" to 1,
        "Abcdefg1" to 0,
        "ABCDEFG1" to 0,
    )
    casos.forEach { (pwd, expected) ->
        val errs = validarPassword(pwd)
        check(errs.size == expected) { "Para '$pwd' esperado $expected, obtuvo ${errs.size}: $errs" }
        println("✓ '$pwd' → ${errs.size} errores")
    }
}""",
            "solution_code": """fun validarPassword(pwd: String): List<String> {
    val errs = mutableListOf<String>()
    if (pwd.length < 8) errs += "Mínimo 8 caracteres"
    if (pwd.none { it.isUpperCase() }) errs += "Necesita al menos 1 mayúscula"
    if (pwd.none { it.isDigit() }) errs += "Necesita al menos 1 dígito"
    return errs
}

fun main() {
    val casos = listOf(
        "abc" to 3,
        "abcdefgh" to 2,
        "Abcdefgh" to 1,
        "Abcdefg1" to 0,
        "ABCDEFG1" to 0,
    )
    casos.forEach { (pwd, expected) ->
        val errs = validarPassword(pwd)
        check(errs.size == expected) { "Para '$pwd' esperado $expected, obtuvo ${errs.size}: $errs" }
        println("✓ '$pwd' → ${errs.size} errores")
    }
}""",
            "hints": "Acumula errores en una lista mutable. Usa `none { it.isUpperCase() }` para detectar ausencia.",
        },
    ],

    "Firma y Preparación de la APK para Producción": [
        {
            "title": "Generador de ProGuard Rules",
            "difficulty": "medium",
            "description": """## Generador de Reglas ProGuard

ProGuard ofusca el código pero rompe librerías con reflection si no se configuran reglas.

**Requisitos:**
- Data class `KeepRule(val pattern: String, val keepMembers: Boolean = false)`.
- Función `buildProguardRules(rules: List<KeepRule>): String` que retorne el archivo proguard-rules.pro.
- Cada `KeepRule` produce: `-keep class <pattern>` y si `keepMembers=true`, también `{ *; }`.
- Incluye 2 reglas base: `-dontwarn javax.annotation.**` y `-keepattributes Signature`.""",
            "initial_code": """data class KeepRule(val pattern: String, val keepMembers: Boolean = false)

fun buildProguardRules(rules: List<KeepRule>): String { TODO() }

fun main() {
    println(buildProguardRules(listOf(
        KeepRule("com.google.gson.**", keepMembers = true),
        KeepRule("pe.edu.iestprfa.tutor.data.dto.**", keepMembers = true),
        KeepRule("pe.edu.iestprfa.tutor.MainActivity"),
    )))
}""",
            "solution_code": """data class KeepRule(val pattern: String, val keepMembers: Boolean = false)

fun buildProguardRules(rules: List<KeepRule>): String {
    val base = listOf(
        "-dontwarn javax.annotation.**",
        "-keepattributes Signature",
    )
    val custom = rules.map { r ->
        val members = if (r.keepMembers) " { *; }" else ""
        "-keep class ${r.pattern}$members"
    }
    return (base + custom).joinToString("\n")
}

fun main() {
    println(buildProguardRules(listOf(
        KeepRule("com.google.gson.**", keepMembers = true),
        KeepRule("pe.edu.iestprfa.tutor.data.dto.**", keepMembers = true),
        KeepRule("pe.edu.iestprfa.tutor.MainActivity"),
    )))
}""",
            "hints": "Concatena reglas base + custom con `joinToString(\"\\n\")`. `keepMembers` añade `{ *; }`.",
        },
        {
            "title": "Validador de AndroidManifest",
            "difficulty": "medium",
            "description": """## Validador de AndroidManifest

Detecta problemas comunes en el AndroidManifest antes de firmar.

**Requisitos:**
- Data class `ManifestConfig(val packageName: String, val versionCode: Int, val minSdk: Int, val targetSdk: Int, val permissions: List<String>, val hasMainActivity: Boolean)`.
- Función `validate(cfg: ManifestConfig): List<String>` con reglas:
  - `versionCode > 0`
  - `targetSdk >= minSdk`
  - `targetSdk >= 34` (Play 2026)
  - `packageName` contiene al menos un `.`
  - `permissions` no contiene duplicados
  - `hasMainActivity == true`
- Lista vacía si todo OK.""",
            "initial_code": """data class ManifestConfig(
    val packageName: String,
    val versionCode: Int,
    val minSdk: Int,
    val targetSdk: Int,
    val permissions: List<String>,
    val hasMainActivity: Boolean,
)

fun validate(cfg: ManifestConfig): List<String> { TODO() }

fun main() {
    println(validate(ManifestConfig("pe.iestprfa.tutor", 1, 24, 34, listOf("INTERNET"), true)))
    println(validate(ManifestConfig("tutor", 0, 24, 30, listOf("INTERNET", "INTERNET"), false)))
}""",
            "solution_code": """data class ManifestConfig(
    val packageName: String,
    val versionCode: Int,
    val minSdk: Int,
    val targetSdk: Int,
    val permissions: List<String>,
    val hasMainActivity: Boolean,
)

fun validate(cfg: ManifestConfig): List<String> {
    val errs = mutableListOf<String>()
    if (cfg.versionCode <= 0) errs += "versionCode debe ser > 0"
    if (cfg.targetSdk < cfg.minSdk) errs += "targetSdk < minSdk"
    if (cfg.targetSdk < 34) errs += "targetSdk debe ser >= 34 (Play 2026)"
    if (!cfg.packageName.contains('.')) errs += "packageName debe ser dotted"
    if (cfg.permissions.distinct().size != cfg.permissions.size) errs += "permissions duplicados"
    if (!cfg.hasMainActivity) errs += "Falta MAIN/LAUNCHER intent-filter"
    return errs
}

fun main() {
    println(validate(ManifestConfig("pe.iestprfa.tutor", 1, 24, 34, listOf("INTERNET"), true)))
    println(validate(ManifestConfig("tutor", 0, 24, 30, listOf("INTERNET", "INTERNET"), false)))
}""",
            "hints": "Para detectar duplicados, compara `list.distinct().size` con `list.size`.",
        },
    ],

    "Publicación en Google Play Store": [
        {
            "title": "Release Notes Multi-Idioma",
            "difficulty": "easy",
            "description": """## Generador de Release Notes Multi-Idioma

Play Store soporta release notes por locale (es-PE, en-US, etc.).

**Requisitos:**
- Data class `Release(val versionName: String, val features: List<String>, val fixes: List<String>)`.
- Función `renderEs(release: Release): String` (español) y `renderEn(release: Release): String` (inglés).
- Formato:
  ```
  v1.2.0
  Novedades:
  • Feature A
  Correcciones:
  • Bug fix B
  ```
- En `main()` imprime ambos para una release con 2 features y 1 fix.""",
            "initial_code": """data class Release(val versionName: String, val features: List<String>, val fixes: List<String>)

fun renderEs(release: Release): String { TODO() }
fun renderEn(release: Release): String { TODO() }

fun main() {
    val r = Release("1.2.0", listOf("Modo oscuro", "Editor Monaco"), listOf("Crash al iniciar sin red"))
    println(renderEs(r)); println("---"); println(renderEn(r))
}""",
            "solution_code": """data class Release(val versionName: String, val features: List<String>, val fixes: List<String>)

private fun render(release: Release, labels: Triple<String, String, String>): String = buildString {
    appendLine("v${release.versionName}")
    appendLine(labels.second + ":")
    release.features.forEach { appendLine("• $it") }
    appendLine(labels.third + ":")
    release.fixes.forEach { appendLine("• $it") }
}

fun renderEs(release: Release) = render(release, Triple("v", "Novedades", "Correcciones"))
fun renderEn(release: Release) = render(release, Triple("v", "What's new", "Bug fixes"))

fun main() {
    val r = Release("1.2.0", listOf("Modo oscuro", "Editor Monaco"), listOf("Crash al iniciar sin red"))
    println(renderEs(r)); println("---"); println(renderEn(r))
}""",
            "hints": "Usa `buildString { appendLine(...) }` para concatenar líneas de forma eficiente. Factoriza el renderer común.",
        },
        {
            "title": "Estrategia de Rollout Progresivo",
            "difficulty": "medium",
            "description": """## Cálculo de Rollout Progresivo

Play Store permite liberar la versión en porcentajes (10% → 25% → 50% → 100%).

**Requisitos:**
- Data class `RolloutStage(val percent: Int, val daysAfterPrevious: Int)`.
- Función `plan(stages: List<RolloutStage>, startDay: Int = 0): List<Pair<Int, Int>>`:
  - Devuelve lista de `(día, porcentajeAcumulado)`.
  - `daysAfterPrevious` define el delta de días desde la etapa anterior.
- En `main()` planea: [10%@d0, 25%@+2d, 50%@+3d, 100%@+5d] y muéstralo.""",
            "initial_code": """data class RolloutStage(val percent: Int, val daysAfterPrevious: Int)

fun plan(stages: List<RolloutStage>, startDay: Int = 0): List<Pair<Int, Int>> { TODO() }

fun main() {
    val s = listOf(
        RolloutStage(10, 0),
        RolloutStage(25, 2),
        RolloutStage(50, 3),
        RolloutStage(100, 5),
    )
    plan(s).forEach { (day, pct) -> println("día $day → $pct%") }
}""",
            "solution_code": """data class RolloutStage(val percent: Int, val daysAfterPrevious: Int)

fun plan(stages: List<RolloutStage>, startDay: Int = 0): List<Pair<Int, Int>> {
    var day = startDay
    return stages.map { s ->
        day += s.daysAfterPrevious
        day to s.percent
    }
}

fun main() {
    val s = listOf(
        RolloutStage(10, 0),
        RolloutStage(25, 2),
        RolloutStage(50, 3),
        RolloutStage(100, 5),
    )
    plan(s).forEach { (day, pct) -> println("día $day → $pct%") }
}""",
            "hints": "Acumula `day` mientras iteras. `map` devuelve la lista con la tupla `(día, porcentaje)`.",
        },
    ],
}


async def seed_more():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Topic))
        topics = result.scalars().all()
        topic_map = {t.title: t for t in topics}

        total_inserted = 0
        total_skipped = 0

        for topic_title, challenges in MORE_CHALLENGES.items():
            topic = topic_map.get(topic_title)
            if not topic:
                print(f"  ⚠ Tema no encontrado: {topic_title}")
                continue

            existing_q = await db.execute(
                select(CodingChallenge).where(
                    CodingChallenge.topic_id == topic.id,
                    CodingChallenge.is_ai_generated == False,
                )
            )
            existing_catalog = existing_q.scalars().all()
            existing_titles = {c.title for c in existing_catalog}
            next_order = max((c.order_index or 0) for c in existing_catalog) + 1 if existing_catalog else 0

            for c_data in challenges:
                if c_data["title"] in existing_titles:
                    print(f"  ⊙ Ya existe: [{topic_title}] {c_data['title']}")
                    total_skipped += 1
                    continue

                db.add(CodingChallenge(
                    topic_id=topic.id,
                    title=c_data["title"],
                    description=c_data["description"],
                    initial_code=c_data.get("initial_code"),
                    language=c_data.get("language", "kotlin"),
                    difficulty=c_data.get("difficulty", "medium"),
                    hints=c_data.get("hints"),
                    solution_code=c_data.get("solution_code"),
                    order_index=next_order,
                    is_ai_generated=False,
                ))
                next_order += 1
                total_inserted += 1
                print(f"  ✓ [{topic_title}] {c_data['title']} ({c_data['difficulty']})")

        await db.commit()

        final = await db.execute(select(CodingChallenge).where(CodingChallenge.is_ai_generated == False))
        total_catalog = len(list(final.scalars().all()))

        print(f"\n{'='*60}")
        print(f"Insertados: {total_inserted}   Saltados: {total_skipped}")
        print(f"Catálogo total: {total_catalog}")
        print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(seed_more())
