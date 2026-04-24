"""
seed_extra_challenges.py — Añade 23 desafíos de programación adicionales
al catálogo (7 existentes → 30 totales), distribuidos en M1-M5.

Idempotente: verifica por (topic_id, title) antes de insertar.
Ejecutar:
    docker compose exec backend python scripts/seed_extra_challenges.py
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


EXTRA_CHALLENGES: dict[str, list[dict]] = {
    # =============================================================
    # M1 · Fundamentos y Preparación del Entorno (+2)
    # =============================================================
    "SDK de Android: Versiones y Compatibilidad": [
        {
            "title": "Verificador de Compatibilidad de API",
            "difficulty": "easy",
            "description": """## Verificador de Compatibilidad de API

Escribe una función `checkCompatibility(apiLevel: Int, minSdk: Int): Pair<Boolean, String>` que evalúe si una versión de Android es compatible con tu app.

**Requisitos:**
- Si `apiLevel >= minSdk` → `Pair(true, "Compatible")`
- Si `apiLevel < minSdk` → `Pair(false, "Necesita actualizar Android")`
- Si `apiLevel >= 34` → añadir al mensaje " — Usa features modernos"

**Ejemplo:**
```
checkCompatibility(34, 24) → (true, "Compatible — Usa features modernos")
checkCompatibility(21, 24) → (false, "Necesita actualizar Android")
```""",
            "initial_code": """fun checkCompatibility(apiLevel: Int, minSdk: Int): Pair<Boolean, String> {
    // Tu código aquí
}

fun main() {
    println(checkCompatibility(34, 24))
    println(checkCompatibility(21, 24))
}""",
            "solution_code": """fun checkCompatibility(apiLevel: Int, minSdk: Int): Pair<Boolean, String> {
    if (apiLevel < minSdk) return Pair(false, "Necesita actualizar Android")
    val suffix = if (apiLevel >= 34) " — Usa features modernos" else ""
    return Pair(true, "Compatible$suffix")
}

fun main() {
    println(checkCompatibility(34, 24))
    println(checkCompatibility(21, 24))
}""",
            "hints": "Usa una estructura `if` para chequear incompatibilidad, luego concatena el sufijo si API ≥ 34.",
        },
    ],
    "Tu Primera Aplicación Android en Kotlin": [
        {
            "title": "Hola Mundo con Variables",
            "difficulty": "easy",
            "description": """## Hola Mundo Personalizado

En Android, tu primera pantalla suele saludar al usuario. Reproduce esa lógica en Kotlin puro.

**Requisitos:**
- Declara `val nombre` y `val institucion` (inmutables) con valores apropiados.
- Declara `var contadorSaludos` (mutable) iniciado en 0.
- Crea función `saludar()` que imprima "Hola {nombre}, bienvenido a {institucion}" e incremente el contador.
- Llámala 3 veces en `main()` y muestra el valor final del contador.

**Ejemplo de salida:**
```
Hola Ana, bienvenido a IESTP RFA
Hola Ana, bienvenido a IESTP RFA
Hola Ana, bienvenido a IESTP RFA
Saludos totales: 3
```""",
            "initial_code": """// Declara aquí las variables


fun saludar() {
    // Tu código aquí
}

fun main() {
    // Llama a saludar() 3 veces y muestra el contador
}""",
            "solution_code": """val nombre = "Ana"
val institucion = "IESTP RFA"
var contadorSaludos = 0

fun saludar() {
    println("Hola $nombre, bienvenido a $institucion")
    contadorSaludos++
}

fun main() {
    repeat(3) { saludar() }
    println("Saludos totales: $contadorSaludos")
}""",
            "hints": "`val` para lo inmutable, `var` para el contador. Usa string templates con `$variable` en el println.",
        },
    ],

    # =============================================================
    # M2 · Lógica de Programación en Kotlin (+4)
    # =============================================================
    "Variables, Tipos de Datos y Operadores en Kotlin": [
        {
            "title": "Conversor de Temperaturas",
            "difficulty": "easy",
            "description": """## Conversor de Temperaturas

Implementa dos funciones de conversión de temperatura:

**Requisitos:**
- `celsiusAFahrenheit(c: Double): Double` → devuelve c * 9/5 + 32
- `fahrenheitACelsius(f: Double): Double` → devuelve (f - 32) * 5/9
- En `main()`, convierte 100°C y muestra ambas equivalencias con 2 decimales.

**Ejemplo:**
```
100.0°C = 212.00°F
212.0°F = 100.00°C
```""",
            "initial_code": """fun celsiusAFahrenheit(c: Double): Double {
    // Tu código
}

fun fahrenheitACelsius(f: Double): Double {
    // Tu código
}

fun main() {
    val c = 100.0
    val f = celsiusAFahrenheit(c)
    println("%.1f°C = %.2f°F".format(c, f))
    println("%.1f°F = %.2f°C".format(f, fahrenheitACelsius(f)))
}""",
            "solution_code": """fun celsiusAFahrenheit(c: Double): Double = c * 9 / 5 + 32
fun fahrenheitACelsius(f: Double): Double = (f - 32) * 5 / 9

fun main() {
    val c = 100.0
    val f = celsiusAFahrenheit(c)
    println("%.1f°C = %.2f°F".format(c, f))
    println("%.1f°F = %.2f°C".format(f, fahrenheitACelsius(f)))
}""",
            "hints": "Usa expresiones de una sola línea con `=` para funciones simples. `format` aplica formato estilo printf.",
        },
    ],
    "Estructuras de Control: if/else, when y bucles": [
        {
            "title": "Simulador de Calificaciones",
            "difficulty": "easy",
            "description": """## Simulador de Calificaciones por Letra

Convierte notas numéricas (0-20) a letras académicas peruanas usando `when` con rangos.

**Requisitos:**
- Función `notaALetra(nota: Int): String`
- `17-20` → "A (Excelente)"
- `14-16` → "B (Bueno)"
- `11-13` → "C (Aprobado)"
- `0-10`  → "D (Desaprobado)"
- Si está fuera de rango → "Nota inválida"
- En `main()`, clasifica [20, 18, 15, 13, 10, 25] e imprime cada uno.

**Ejemplo:**
```
Nota 20 → A (Excelente)
Nota 25 → Nota inválida
```""",
            "initial_code": """fun notaALetra(nota: Int): String {
    // Usa when con rangos (in 1..5)
}

fun main() {
    listOf(20, 18, 15, 13, 10, 25).forEach {
        println("Nota $it → ${notaALetra(it)}")
    }
}""",
            "solution_code": """fun notaALetra(nota: Int): String = when (nota) {
    in 17..20 -> "A (Excelente)"
    in 14..16 -> "B (Bueno)"
    in 11..13 -> "C (Aprobado)"
    in 0..10  -> "D (Desaprobado)"
    else -> "Nota inválida"
}

fun main() {
    listOf(20, 18, 15, 13, 10, 25).forEach {
        println("Nota $it → ${notaALetra(it)}")
    }
}""",
            "hints": "`when` en Kotlin soporta `in a..b` para rangos. El `else` captura cualquier valor fuera de rango.",
        },
    ],
    "Funciones, Lambdas y Alcance en Kotlin": [
        {
            "title": "Ordenar Personas por Edad",
            "difficulty": "medium",
            "description": """## Ordenamiento Funcional de Datos

Usa lambdas con las funciones de orden superior de Kotlin.

**Requisitos:**
- Crea data class `Persona(val nombre: String, val edad: Int)`.
- Lista con ≥5 personas variadas.
- Ordena ascendentemente por edad.
- Filtra mayores de edad (≥18).
- Agrupa por rango: "niños" (<12), "adolescentes" (12-17), "adultos" (≥18).
- Imprime cada paso.

**Tip:** usa `sortedBy`, `filter`, `groupBy`.""",
            "initial_code": """data class Persona(val nombre: String, val edad: Int)

fun main() {
    val personas = listOf(
        Persona("Ana", 20),
        Persona("Luis", 15),
        Persona("Sara", 8),
        Persona("Juan", 35),
        Persona("Mia", 11),
    )

    // 1. Ordena por edad asc
    // 2. Filtra mayores de edad
    // 3. Agrupa por rango
}""",
            "solution_code": """data class Persona(val nombre: String, val edad: Int)

fun main() {
    val personas = listOf(
        Persona("Ana", 20),
        Persona("Luis", 15),
        Persona("Sara", 8),
        Persona("Juan", 35),
        Persona("Mia", 11),
    )

    val ordenados = personas.sortedBy { it.edad }
    println("Ordenados: $ordenados")

    val adultos = personas.filter { it.edad >= 18 }
    println("Adultos: $adultos")

    val porRango = personas.groupBy {
        when {
            it.edad < 12 -> "niños"
            it.edad < 18 -> "adolescentes"
            else -> "adultos"
        }
    }
    porRango.forEach { (rango, lista) -> println("$rango: ${lista.map { it.nombre }}") }
}""",
            "hints": "Usa `sortedBy { it.edad }`, `filter { it.edad >= 18 }` y `groupBy { when { ... } }`.",
        },
    ],
    "POO: Herencia, Interfaces y Polimorfismo": [
        {
            "title": "Jerarquía de Vehículos con Polimorfismo",
            "difficulty": "hard",
            "description": """## Sistema de Vehículos Polimórfico

Diseña una jerarquía que use herencia, sobreescritura y polimorfismo.

**Requisitos:**
- Clase abstracta `Vehiculo(val marca: String, val velocidadMax: Int)` con función abstracta `describir(): String` y función concreta `acelerar()` que imprima "Acelerando {marca}".
- Clase `Auto` que hereda de `Vehiculo` y sobreescribe `describir()` mostrando también nroPuertas.
- Clase `Moto` que hereda con atributo `esDeportiva: Boolean`.
- Clase `Camion` con `capacidadCarga: Int`.
- En `main()`, crea una lista `List<Vehiculo>` con los 3 tipos e itera llamando a `describir()` y `acelerar()`.

**Tip:** usa `abstract class` + `open`/`override`.""",
            "initial_code": """abstract class Vehiculo(val marca: String, val velocidadMax: Int) {
    // función abstracta describir()
    // función concreta acelerar()
}

// Auto, Moto, Camion aquí

fun main() {
    val garage: List<Vehiculo> = listOf(
        // crea los 3 tipos
    )
    garage.forEach {
        println(it.describir())
        it.acelerar()
    }
}""",
            "solution_code": """abstract class Vehiculo(val marca: String, val velocidadMax: Int) {
    abstract fun describir(): String
    fun acelerar() {
        println("Acelerando $marca a $velocidadMax km/h")
    }
}

class Auto(marca: String, velocidadMax: Int, val nroPuertas: Int) : Vehiculo(marca, velocidadMax) {
    override fun describir() = "Auto $marca ($nroPuertas puertas, $velocidadMax km/h)"
}

class Moto(marca: String, velocidadMax: Int, val esDeportiva: Boolean) : Vehiculo(marca, velocidadMax) {
    override fun describir(): String {
        val tipo = if (esDeportiva) "deportiva" else "estándar"
        return "Moto $marca $tipo — $velocidadMax km/h"
    }
}

class Camion(marca: String, velocidadMax: Int, val capacidadCarga: Int) : Vehiculo(marca, velocidadMax) {
    override fun describir() = "Camión $marca — carga $capacidadCarga kg — $velocidadMax km/h"
}

fun main() {
    val garage: List<Vehiculo> = listOf(
        Auto("Toyota", 180, 4),
        Moto("Yamaha", 220, true),
        Camion("Volvo", 120, 12000),
    )
    garage.forEach {
        println(it.describir())
        it.acelerar()
    }
}""",
            "hints": "Usa `abstract class` y `abstract fun` para forzar override. La función concreta `acelerar()` se hereda sin cambios.",
        },
    ],

    # =============================================================
    # M3 · Interfaces de Usuario (+6)
    # =============================================================
    "Fundamentos de XML para Layouts Android": [
        {
            "title": "Layout XML Formulario de Registro",
            "difficulty": "medium",
            "description": """## Layout XML Formulario de Registro

Declara un layout XML (como string en Kotlin) que represente un formulario de registro.

**Requisitos:**
- Root `LinearLayout` vertical con padding 16dp.
- `TextView` título "Registro".
- 3 `EditText`: nombre, email (inputType email), password (inputType textPassword).
- `Button` "Registrar" con id `btnRegistrar`.
- Retorna el XML como `String` desde `fun generarLayout(): String`.

**Valida** que tu string incluya: `android:inputType="textPassword"`, `android:id="@+id/btnRegistrar"`, `android:orientation="vertical"`.""",
            "initial_code": """fun generarLayout(): String {
    // Retorna el XML como multi-line string
    return ""\"
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <!-- Completa el layout -->

</LinearLayout>
""\"
}

fun main() {
    println(generarLayout())
}""",
            "solution_code": """fun generarLayout(): String = ""\"
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:padding="16dp">

    <TextView
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Registro"
        android:textSize="20sp"/>

    <EditText
        android:id="@+id/etNombre"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:hint="Nombre completo"/>

    <EditText
        android:id="@+id/etEmail"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:inputType="textEmailAddress"
        android:hint="Correo"/>

    <EditText
        android:id="@+id/etPassword"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:inputType="textPassword"
        android:hint="Contraseña"/>

    <Button
        android:id="@+id/btnRegistrar"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:text="Registrar"/>

</LinearLayout>
""\".trimIndent()

fun main() {
    println(generarLayout())
}""",
            "hints": "Cada EditText necesita `inputType` específico. El root `LinearLayout` requiere `orientation=\"vertical\"`.",
        },
    ],
    "Views básicos: TextView, Button, EditText e ImageView": [
        {
            "title": "Validador de EditText Email",
            "difficulty": "easy",
            "description": """## Validador de Email

Simula la lógica de validación que asignarías a un `EditText` de email.

**Requisitos:**
- Función `validarEmail(email: String): Pair<Boolean, String?>`.
- Retorna `(true, null)` si es válido.
- Retorna `(false, "Email inválido")` si no.
- Valida con regex: letras, números, punto, guion bajo antes del `@`, luego dominio con `.`.

**Ejemplo:**
```
validarEmail("ana@iestprfa.edu.pe") → (true, null)
validarEmail("no-es-email") → (false, "Email inválido")
```""",
            "initial_code": """fun validarEmail(email: String): Pair<Boolean, String?> {
    val regex = Regex("...") // Completa
    // Tu código
}

fun main() {
    println(validarEmail("ana@iestprfa.edu.pe"))
    println(validarEmail("no-es-email"))
}""",
            "solution_code": """fun validarEmail(email: String): Pair<Boolean, String?> {
    val regex = Regex("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\\\.[A-Za-z]{2,}$")
    return if (regex.matches(email)) Pair(true, null) else Pair(false, "Email inválido")
}

fun main() {
    println(validarEmail("ana@iestprfa.edu.pe"))
    println(validarEmail("no-es-email"))
}""",
            "hints": "Patrón regex típico: `^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$`.",
        },
        {
            "title": "Click Handler con Toast Simulado",
            "difficulty": "easy",
            "description": """## Handler de Click con Toast Simulado

En una app Android real, pulsar un Button muestra un Toast. Simula esa interacción.

**Requisitos:**
- Interface funcional `OnClickListener { fun onClick(label: String) }`.
- Clase `Button(val id: String)` con `fun setOnClickListener(l: OnClickListener)` y `fun click()` que invoca al listener.
- En `main()` crea un botón con id "btnSaludar", asígnale listener (lambda SAM) que imprima "Toast: ¡Hola desde {id}!" y ejecútalo 2 veces.""",
            "initial_code": """fun interface OnClickListener {
    fun onClick(label: String)
}

class Button(val id: String) {
    // TODO: guardar listener, implementar setOnClickListener y click
}

fun main() {
    // Crear botón, asignar listener lambda, clickear 2 veces
}""",
            "solution_code": """fun interface OnClickListener {
    fun onClick(label: String)
}

class Button(val id: String) {
    private var listener: OnClickListener? = null
    fun setOnClickListener(l: OnClickListener) { listener = l }
    fun click() { listener?.onClick(id) }
}

fun main() {
    val btn = Button("btnSaludar")
    btn.setOnClickListener { id -> println("Toast: ¡Hola desde $id!") }
    btn.click()
    btn.click()
}""",
            "hints": "`fun interface` permite pasar lambda SAM. Guarda el listener como `var` privado y llámalo desde `click()`.",
        },
    ],
    "Layouts: ConstraintLayout y RelativeLayout": [
        {
            "title": "Generador ConstraintLayout Programático",
            "difficulty": "medium",
            "description": """## ConstraintLayout Programático

Genera dinámicamente un XML de `ConstraintLayout` con un TextView centrado y un Button debajo.

**Requisitos:**
- Función `crearLoginLayout(): String`.
- Root `androidx.constraintlayout.widget.ConstraintLayout` tamaño match_parent.
- `TextView` con texto "Inicio de sesión" centrado (app:layout_constraintStart/End/Top toParent).
- `EditText` con id `etUser` debajo del título (app:layout_constraintTop_toBottomOf).
- `Button` con id `btnLogin` debajo del EditText.
- Debe incluir xmlns:app.""",
            "initial_code": """fun crearLoginLayout(): String {
    // Devuelve XML ConstraintLayout con título + EditText + Button
    return ""
}

fun main() { println(crearLoginLayout()) }""",
            "solution_code": """fun crearLoginLayout(): String = ""\"
<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <TextView
        android:id="@+id/tvTitulo"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Inicio de sesión"
        android:textSize="20sp"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintTop_toTopOf="parent"
        android:layout_marginTop="48dp"/>

    <EditText
        android:id="@+id/etUser"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:hint="Usuario"
        app:layout_constraintTop_toBottomOf="@id/tvTitulo"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        android:layout_margin="16dp"/>

    <Button
        android:id="@+id/btnLogin"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:text="Ingresar"
        app:layout_constraintTop_toBottomOf="@id/etUser"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent"
        android:layout_margin="16dp"/>

</androidx.constraintlayout.widget.ConstraintLayout>
""\".trimIndent()

fun main() { println(crearLoginLayout()) }""",
            "hints": "Usa `app:layout_constraintStart_toStartOf` y similares. Ancho `0dp` con constraints laterales = match_constraint.",
        },
        {
            "title": "Card Responsivo Portrait/Landscape",
            "difficulty": "medium",
            "description": """## Card Responsivo según Orientación

Decide layout según la orientación de pantalla.

**Requisitos:**
- Enum `Orientation { PORTRAIT, LANDSCAPE }`.
- Data class `CardConfig(val columns: Int, val imageHeight: Int, val padding: Int)`.
- Función `cardConfigFor(orientation: Orientation, screenWidthDp: Int): CardConfig` que:
  - PORTRAIT: 1 columna, imageHeight=180, padding=16 (o 2 col si width ≥ 600).
  - LANDSCAPE: 2 columnas, imageHeight=120, padding=24 (o 3 col si width ≥ 900).
- Pruébala con los 4 casos en `main()`.""",
            "initial_code": """enum class Orientation { PORTRAIT, LANDSCAPE }
data class CardConfig(val columns: Int, val imageHeight: Int, val padding: Int)

fun cardConfigFor(orientation: Orientation, screenWidthDp: Int): CardConfig {
    // Tu código
    TODO()
}

fun main() {
    println(cardConfigFor(Orientation.PORTRAIT, 360))
    println(cardConfigFor(Orientation.PORTRAIT, 720))
    println(cardConfigFor(Orientation.LANDSCAPE, 720))
    println(cardConfigFor(Orientation.LANDSCAPE, 1024))
}""",
            "solution_code": """enum class Orientation { PORTRAIT, LANDSCAPE }
data class CardConfig(val columns: Int, val imageHeight: Int, val padding: Int)

fun cardConfigFor(orientation: Orientation, screenWidthDp: Int): CardConfig = when (orientation) {
    Orientation.PORTRAIT -> CardConfig(
        columns = if (screenWidthDp >= 600) 2 else 1,
        imageHeight = 180,
        padding = 16,
    )
    Orientation.LANDSCAPE -> CardConfig(
        columns = if (screenWidthDp >= 900) 3 else 2,
        imageHeight = 120,
        padding = 24,
    )
}

fun main() {
    println(cardConfigFor(Orientation.PORTRAIT, 360))
    println(cardConfigFor(Orientation.PORTRAIT, 720))
    println(cardConfigFor(Orientation.LANDSCAPE, 720))
    println(cardConfigFor(Orientation.LANDSCAPE, 1024))
}""",
            "hints": "`when (orientation)` con bloque; dentro usa `if` para ajustar columnas por ancho.",
        },
    ],
    "RecyclerView y CardView para Listas de Datos": [
        {
            "title": "Adapter Mínimo de RecyclerView",
            "difficulty": "hard",
            "description": """## Adapter Simulado de RecyclerView

Implementa la lógica de un Adapter minimalista.

**Requisitos:**
- Class `ItemView(var texto: String)` (simula el ViewHolder).
- Class `MyAdapter(private val items: List<String>)`:
  - `fun getItemCount(): Int`
  - `fun onCreateViewHolder(): ItemView` (retorna vista vacía)
  - `fun onBindViewHolder(holder: ItemView, position: Int)` → asigna texto de `items[position]`.
- Simula recycling: en `main()` crea adapter con 5 items, re-usa 2 ItemView rotándolos para posiciones 0..4. Imprime estado final de cada ItemView por posición.""",
            "initial_code": """class ItemView(var texto: String = "")

class MyAdapter(private val items: List<String>) {
    fun getItemCount(): Int = TODO()
    fun onCreateViewHolder(): ItemView = TODO()
    fun onBindViewHolder(holder: ItemView, position: Int) { TODO() }
}

fun main() {
    val adapter = MyAdapter(listOf("Ana", "Beto", "Carla", "Dino", "Eva"))
    // Simula 2 ItemViews reciclándose
}""",
            "solution_code": """class ItemView(var texto: String = "")

class MyAdapter(private val items: List<String>) {
    fun getItemCount(): Int = items.size
    fun onCreateViewHolder(): ItemView = ItemView()
    fun onBindViewHolder(holder: ItemView, position: Int) {
        holder.texto = items[position]
    }
}

fun main() {
    val adapter = MyAdapter(listOf("Ana", "Beto", "Carla", "Dino", "Eva"))
    val pool = listOf(adapter.onCreateViewHolder(), adapter.onCreateViewHolder())
    for (pos in 0 until adapter.getItemCount()) {
        val holder = pool[pos % pool.size]
        adapter.onBindViewHolder(holder, pos)
        println("Posición $pos → ItemView('${holder.texto}')")
    }
}""",
            "hints": "El reciclaje típico de RecyclerView reutiliza ViewHolders modificando su contenido. Aquí los rotas con `pos % pool.size`.",
        },
    ],

    # =============================================================
    # M4 · Componentes Android y Gestión de Datos (+6)
    # =============================================================
    "Activities y el Ciclo de Vida de Android": [
        {
            "title": "Counter Persistente con Bundle",
            "difficulty": "medium",
            "description": """## Counter Persistente (simula onSaveInstanceState)

En Android el Bundle preserva estado en rotaciones. Simula ese patrón en Kotlin.

**Requisitos:**
- Clase `CounterActivity` con var `count = 0` y métodos:
  - `onCreate(savedInstanceState: Map<String, Any>?)` → restaura count si existe la clave "count".
  - `increment()` → incrementa count.
  - `onSaveInstanceState(): Map<String, Any>` → retorna mapa con "count".
- En `main()`: crea activity, increment 3 veces, guarda bundle, crea nueva activity pasando ese bundle → debe tener count=3.""",
            "initial_code": """class CounterActivity {
    var count = 0
    fun onCreate(savedInstanceState: Map<String, Any>?) {
        // restaurar si existe
    }
    fun increment() { TODO() }
    fun onSaveInstanceState(): Map<String, Any> = TODO()
}

fun main() {
    val a = CounterActivity()
    a.onCreate(null)
    repeat(3) { a.increment() }
    val bundle = a.onSaveInstanceState()
    val b = CounterActivity()
    b.onCreate(bundle)
    println("Count preservado: ${b.count}")
}""",
            "solution_code": """class CounterActivity {
    var count = 0
    fun onCreate(savedInstanceState: Map<String, Any>?) {
        count = (savedInstanceState?.get("count") as? Int) ?: 0
    }
    fun increment() { count++ }
    fun onSaveInstanceState(): Map<String, Any> = mapOf("count" to count)
}

fun main() {
    val a = CounterActivity()
    a.onCreate(null)
    repeat(3) { a.increment() }
    val bundle = a.onSaveInstanceState()
    val b = CounterActivity()
    b.onCreate(bundle)
    println("Count preservado: ${b.count}")
}""",
            "hints": "`as? Int` hace cast seguro que retorna null si no es Int. Combínalo con Elvis `?:` para default.",
        },
    ],
    "Navegación entre Pantallas con Intents": [
        {
            "title": "Simulador de Intent con Extras",
            "difficulty": "medium",
            "description": """## Simulación de Intent con Extras

Modela cómo un Intent pasa datos entre Activities.

**Requisitos:**
- Clase `Intent(val targetActivity: String)` con:
  - `fun putExtra(key: String, value: Any): Intent` (fluida)
  - `fun getStringExtra(key: String): String?`
  - `fun getIntExtra(key: String, default: Int): Int`
- Clase `DetailActivity` con `fun handle(intent: Intent)` que imprima los extras recibidos.
- En `main()` crea Intent con putExtra("userId", 42) y ("name", "Ana"), envíalo a DetailActivity.""",
            "initial_code": """class Intent(val targetActivity: String) {
    private val extras = mutableMapOf<String, Any>()
    fun putExtra(key: String, value: Any): Intent { TODO() }
    fun getStringExtra(key: String): String? = TODO()
    fun getIntExtra(key: String, default: Int): Int = TODO()
}

class DetailActivity {
    fun handle(intent: Intent) { TODO() }
}

fun main() {
    val intent = Intent("DetailActivity")
        .putExtra("userId", 42)
        .putExtra("name", "Ana")
    DetailActivity().handle(intent)
}""",
            "solution_code": """class Intent(val targetActivity: String) {
    private val extras = mutableMapOf<String, Any>()
    fun putExtra(key: String, value: Any): Intent {
        extras[key] = value
        return this
    }
    fun getStringExtra(key: String): String? = extras[key] as? String
    fun getIntExtra(key: String, default: Int): Int = (extras[key] as? Int) ?: default
}

class DetailActivity {
    fun handle(intent: Intent) {
        val name = intent.getStringExtra("name") ?: "(sin nombre)"
        val userId = intent.getIntExtra("userId", -1)
        println("Activity destino: ${intent.targetActivity}")
        println("Recibido → userId=$userId, name=$name")
    }
}

fun main() {
    val intent = Intent("DetailActivity")
        .putExtra("userId", 42)
        .putExtra("name", "Ana")
    DetailActivity().handle(intent)
}""",
            "hints": "Devuelve `this` en `putExtra` para encadenar. Usa `as?` para cast seguro al leer.",
        },
    ],
    "Almacenamiento Local: SharedPreferences y SQLite": [
        {
            "title": "SharedPreferences Simulado",
            "difficulty": "easy",
            "description": """## Mock de SharedPreferences

Simula SharedPreferences con un Map en memoria.

**Requisitos:**
- Clase `SharedPreferences` con:
  - `getString(key: String, default: String?): String?`
  - `edit(): Editor`
- Clase anidada `Editor` con `putString(k, v): Editor`, `remove(k): Editor`, `apply()`.
- En `main()` guarda "user" = "ana", léelo, luego remove y confirma null.""",
            "initial_code": """class SharedPreferences {
    private val store = mutableMapOf<String, String>()

    fun getString(key: String, default: String?): String? = TODO()

    fun edit(): Editor = TODO()

    inner class Editor {
        private val pending = mutableMapOf<String, String?>()
        fun putString(k: String, v: String): Editor { TODO() }
        fun remove(k: String): Editor { TODO() }
        fun apply() { TODO() }
    }
}

fun main() {
    val prefs = SharedPreferences()
    prefs.edit().putString("user", "ana").apply()
    println(prefs.getString("user", null))   // ana
    prefs.edit().remove("user").apply()
    println(prefs.getString("user", null))   // null
}""",
            "solution_code": """class SharedPreferences {
    private val store = mutableMapOf<String, String>()

    fun getString(key: String, default: String?): String? = store[key] ?: default

    fun edit(): Editor = Editor()

    inner class Editor {
        private val pending = mutableMapOf<String, String?>()
        fun putString(k: String, v: String): Editor { pending[k] = v; return this }
        fun remove(k: String): Editor { pending[k] = null; return this }
        fun apply() {
            pending.forEach { (k, v) ->
                if (v == null) store.remove(k) else store[k] = v
            }
            pending.clear()
        }
    }
}

fun main() {
    val prefs = SharedPreferences()
    prefs.edit().putString("user", "ana").apply()
    println(prefs.getString("user", null))   // ana
    prefs.edit().remove("user").apply()
    println(prefs.getString("user", null))   // null
}""",
            "hints": "Usa `inner class` para acceder al mapa padre. Los cambios solo se persisten al llamar `apply()`.",
        },
        {
            "title": "Mini CRUD con SQLite Simulado",
            "difficulty": "hard",
            "description": """## CRUD Notas con SQLite Mock

Simula operaciones SQLite con estructuras en memoria.

**Requisitos:**
- Data class `Note(val id: Int, val title: String, val content: String)`.
- Clase `NotesDao` con:
  - `insert(note: Note): Int` (retorna id asignado, autoincrement)
  - `get(id: Int): Note?`
  - `getAll(): List<Note>`
  - `update(id: Int, title: String, content: String): Boolean`
  - `delete(id: Int): Boolean`
- Inicialmente vacío; `insert` asigna ids 1, 2, 3...
- En `main()` demuestra las 4 operaciones.""",
            "initial_code": """data class Note(val id: Int, val title: String, val content: String)

class NotesDao {
    // TODO: estructura + métodos
}

fun main() {
    val dao = NotesDao()
    // Demo: insert 3 notas, update la 2da, delete la 1ra, imprimir getAll
}""",
            "solution_code": """data class Note(val id: Int, val title: String, val content: String)

class NotesDao {
    private val notes = mutableMapOf<Int, Note>()
    private var nextId = 1

    fun insert(note: Note): Int {
        val id = nextId++
        notes[id] = note.copy(id = id)
        return id
    }

    fun get(id: Int): Note? = notes[id]

    fun getAll(): List<Note> = notes.values.toList()

    fun update(id: Int, title: String, content: String): Boolean {
        val existing = notes[id] ?: return false
        notes[id] = existing.copy(title = title, content = content)
        return true
    }

    fun delete(id: Int): Boolean = notes.remove(id) != null
}

fun main() {
    val dao = NotesDao()
    val id1 = dao.insert(Note(0, "Compras", "Leche, pan"))
    val id2 = dao.insert(Note(0, "Tareas", "Finalizar tesis"))
    val id3 = dao.insert(Note(0, "Ideas", "Proyecto final"))

    dao.update(id2, "Tareas urgentes", "Finalizar tesis ASAP")
    dao.delete(id1)

    println("Notas restantes:")
    dao.getAll().forEach { println(it) }
}""",
            "hints": "Usa `mutableMapOf<Int, Note>` como tabla. Autoincrement con `var nextId = 1` y `++`.",
        },
    ],
    "Consumo de APIs REST y Manejo de JSON": [
        {
            "title": "Parser Manual de JSON",
            "difficulty": "medium",
            "description": """## Parser Manual de JSON (sin Gson)

Antes de adoptar Retrofit/Gson, manipular JSON a mano fortalece tu entendimiento.

**Requisitos:**
- Data class `User(val id: Int, val name: String, val email: String)`.
- Función `parseUser(json: String): User` usando `org.json.JSONObject`.
- Maneja que los campos estén presentes; si falta `email` usa "—".
- Función `parseUserList(jsonArray: String): List<User>`.
- En `main()` parsea un JSON single + array y muestra resultados.

**Nota:** `org.json.JSONObject` está disponible en Kotlin/Android sin libs extra.""",
            "initial_code": """import org.json.JSONObject
import org.json.JSONArray

data class User(val id: Int, val name: String, val email: String)

fun parseUser(json: String): User { TODO() }

fun parseUserList(jsonArray: String): List<User> { TODO() }

fun main() {
    val single = ""\"{"id":1,"name":"Ana","email":"ana@test.com"}""\"
    val list = ""\"[{"id":1,"name":"Ana","email":"a@t.com"},{"id":2,"name":"Beto"}]""\"
    println(parseUser(single))
    parseUserList(list).forEach(::println)
}""",
            "solution_code": """import org.json.JSONObject
import org.json.JSONArray

data class User(val id: Int, val name: String, val email: String)

fun parseUser(json: String): User {
    val obj = JSONObject(json)
    return User(
        id = obj.getInt("id"),
        name = obj.getString("name"),
        email = if (obj.has("email")) obj.getString("email") else "—",
    )
}

fun parseUserList(jsonArray: String): List<User> {
    val arr = JSONArray(jsonArray)
    return (0 until arr.length()).map { parseUser(arr.getJSONObject(it).toString()) }
}

fun main() {
    val single = ""\"{"id":1,"name":"Ana","email":"ana@test.com"}""\"
    val list = ""\"[{"id":1,"name":"Ana","email":"a@t.com"},{"id":2,"name":"Beto"}]""\"
    println(parseUser(single))
    parseUserList(list).forEach(::println)
}""",
            "hints": "`JSONObject.has(key)` chequea existencia. `JSONArray.length()` da el tamaño. Usa `map { ... }` con rango.",
        },
    ],
    "Retrofit para Servicios Web en Android": [
        {
            "title": "Interface Retrofit GitHub API",
            "difficulty": "hard",
            "description": """## Interface Retrofit para la API de GitHub

Diseña la interface Retrofit que consume la API pública de GitHub.

**Requisitos:**
- Data class `GithubUser(val login: String, val name: String?, val publicRepos: Int)`.
- Data class `Repo(val name: String, val stars: Int, val language: String?)`.
- Interface `GithubService` con:
  - `@GET("users/{username}") suspend fun getUser(@Path("username") u: String): GithubUser`
  - `@GET("users/{username}/repos") suspend fun getRepos(@Path("username") u: String, @Query("per_page") limit: Int = 10): List<Repo>`
- En `main()` invoca ambos (mockeados) y muéstralos. Usa `suspend` + `runBlocking`.

**Nota:** los decoradores Retrofit van en la interface. La implementación real la genera Retrofit.""",
            "initial_code": """import kotlinx.coroutines.runBlocking

data class GithubUser(val login: String, val name: String?, val publicRepos: Int)
data class Repo(val name: String, val stars: Int, val language: String?)

// TODO: interface GithubService con anotaciones Retrofit
// (simula con comentarios si no tienes Retrofit en el classpath)

fun main() = runBlocking {
    // Invoca un mock que devuelve datos estáticos
}""",
            "solution_code": """import kotlinx.coroutines.runBlocking

data class GithubUser(val login: String, val name: String?, val publicRepos: Int)
data class Repo(val name: String, val stars: Int, val language: String?)

// Anotaciones Retrofit reales (se dejan como comentario-referencia para Kotlin standalone):
// @retrofit2.http.GET("users/{username}")
// suspend fun getUser(@retrofit2.http.Path("username") u: String): GithubUser
interface GithubService {
    suspend fun getUser(username: String): GithubUser
    suspend fun getRepos(username: String, limit: Int = 10): List<Repo>
}

class GithubServiceMock : GithubService {
    override suspend fun getUser(username: String) = GithubUser(username, "Mock User", 42)
    override suspend fun getRepos(username: String, limit: Int) = listOf(
        Repo("tutor-ia-rfa", 12, "Python"),
        Repo("kotlin-lab", 8, "Kotlin"),
    ).take(limit)
}

fun main() = runBlocking {
    val service: GithubService = GithubServiceMock()
    println(service.getUser("zavaleta"))
    service.getRepos("zavaleta").forEach(::println)
}""",
            "hints": "En producción pones `@GET`, `@Path`, `@Query`. Aquí el mock implementa la interface para demostrar el contrato.",
        },
    ],

    # =============================================================
    # M5 · Funcionalidades Avanzadas y Despliegue (+5)
    # =============================================================
    "Depuración de Aplicaciones con Logcat": [
        {
            "title": "Logger por Nivel",
            "difficulty": "easy",
            "description": """## Logger con Niveles (Simula Log.d/i/w/e)

Simula android.util.Log con enum y rutado.

**Requisitos:**
- Enum `LogLevel { DEBUG, INFO, WARN, ERROR }`.
- Objeto singleton `Logger` con var `minLevel: LogLevel = DEBUG`.
- Función `log(level: LogLevel, tag: String, message: String)` que solo imprime si `level.ordinal >= minLevel.ordinal`.
- Helpers `d(tag, msg)`, `i(tag, msg)`, `w(tag, msg)`, `e(tag, msg)`.
- En `main()`: log todos niveles con `minLevel=INFO` → DEBUG debe filtrarse.""",
            "initial_code": """enum class LogLevel { DEBUG, INFO, WARN, ERROR }

object Logger {
    var minLevel: LogLevel = LogLevel.DEBUG
    fun log(level: LogLevel, tag: String, message: String) { TODO() }
    fun d(tag: String, msg: String) = log(LogLevel.DEBUG, tag, msg)
    fun i(tag: String, msg: String) = log(LogLevel.INFO, tag, msg)
    fun w(tag: String, msg: String) = log(LogLevel.WARN, tag, msg)
    fun e(tag: String, msg: String) = log(LogLevel.ERROR, tag, msg)
}

fun main() {
    Logger.minLevel = LogLevel.INFO
    Logger.d("App", "Debug invisible")
    Logger.i("App", "Info visible")
    Logger.w("App", "Warning visible")
    Logger.e("App", "Error visible")
}""",
            "solution_code": """enum class LogLevel { DEBUG, INFO, WARN, ERROR }

object Logger {
    var minLevel: LogLevel = LogLevel.DEBUG
    fun log(level: LogLevel, tag: String, message: String) {
        if (level.ordinal >= minLevel.ordinal) {
            println("[${level.name}] $tag: $message")
        }
    }
    fun d(tag: String, msg: String) = log(LogLevel.DEBUG, tag, msg)
    fun i(tag: String, msg: String) = log(LogLevel.INFO, tag, msg)
    fun w(tag: String, msg: String) = log(LogLevel.WARN, tag, msg)
    fun e(tag: String, msg: String) = log(LogLevel.ERROR, tag, msg)
}

fun main() {
    Logger.minLevel = LogLevel.INFO
    Logger.d("App", "Debug invisible")
    Logger.i("App", "Info visible")
    Logger.w("App", "Warning visible")
    Logger.e("App", "Error visible")
}""",
            "hints": "Compara `level.ordinal` contra `minLevel.ordinal`. Usa `object` para singleton global.",
        },
    ],
    "Pruebas Unitarias con JUnit en Android": [
        {
            "title": "Test Unitario Función Calculadora",
            "difficulty": "easy",
            "description": """## Test Unitario con JUnit 5

Escribe una suite mínima para validar una función de cálculo.

**Requisitos:**
- Función `dividir(a: Int, b: Int): Double` que lanza `IllegalArgumentException("División entre cero")` si b=0.
- Test class `CalculadoraTest` con:
  - `@Test fun dividir_valoresValidos_retornaCociente()`
  - `@Test fun dividir_porCero_lanzaException()` (usa assertThrows)
  - Usa assertEquals de JUnit 5.
- En `main()` corre la función 2 veces y captura la excepción del caso inválido.""",
            "initial_code": """fun dividir(a: Int, b: Int): Double {
    // Tu código
    TODO()
}

// Tests (pseudocódigo si no tienes JUnit en classpath)
class CalculadoraTest {
    // @Test dividir_valoresValidos_retornaCociente()
    // @Test dividir_porCero_lanzaException()
}

fun main() {
    println(dividir(10, 2))
    try { dividir(5, 0) } catch (e: IllegalArgumentException) { println("OK lanzó: ${e.message}") }
}""",
            "solution_code": """fun dividir(a: Int, b: Int): Double {
    require(b != 0) { "División entre cero" }
    return a.toDouble() / b
}

/*
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.assertThrows
import kotlin.test.assertEquals

class CalculadoraTest {
    @Test
    fun dividir_valoresValidos_retornaCociente() {
        assertEquals(5.0, dividir(10, 2), 0.0001)
    }

    @Test
    fun dividir_porCero_lanzaException() {
        val ex = assertThrows<IllegalArgumentException> { dividir(5, 0) }
        assertEquals("División entre cero", ex.message)
    }
}
*/

fun main() {
    println(dividir(10, 2))
    try { dividir(5, 0) } catch (e: IllegalArgumentException) { println("OK lanzó: ${e.message}") }
}""",
            "hints": "`require(cond) { msg }` lanza `IllegalArgumentException` si cond es falsa. En JUnit5, `assertThrows<T> { ... }`.",
        },
        {
            "title": "Test Suite para Data Class User",
            "difficulty": "medium",
            "description": """## Suite de Tests para Data Class

Valida las garantías de una `data class`.

**Requisitos:**
- `data class User(val id: Int, val name: String, val age: Int)`.
- Función `isAdult(u: User): Boolean` (edad ≥ 18).
- Test suite mínima verificando:
  - `equals` entre users idénticos → true.
  - `equals` con age distinto → false.
  - `copy` genera instancia nueva con un campo cambiado.
  - `isAdult(User(1,"Ana",20))` → true; `User(2,"Luis",15)` → false.
- Ejecuta los asserts manualmente en `main()` con `check()`.""",
            "initial_code": """data class User(val id: Int, val name: String, val age: Int)

fun isAdult(u: User): Boolean = TODO()

fun main() {
    val a1 = User(1, "Ana", 20)
    val a2 = User(1, "Ana", 20)
    val diff = a1.copy(age = 25)
    // Verifica todas las propiedades con check(cond) { "mensaje" }
}""",
            "solution_code": """data class User(val id: Int, val name: String, val age: Int)

fun isAdult(u: User): Boolean = u.age >= 18

fun main() {
    val a1 = User(1, "Ana", 20)
    val a2 = User(1, "Ana", 20)
    val diff = a1.copy(age = 25)

    check(a1 == a2) { "equals debería ser true" }
    check(a1 != diff) { "equals debería ser false tras copy con otra edad" }
    check(a1.hashCode() == a2.hashCode()) { "hashCode consistente con equals" }
    check(isAdult(User(1, "Ana", 20))) { "Ana adulta" }
    check(!isAdult(User(2, "Luis", 15))) { "Luis menor" }
    println("✓ Todos los asserts pasan")
}""",
            "hints": "`check(cond) { msg }` lanza `IllegalStateException` si la condición es falsa. Útil para aserciones en demos.",
        },
    ],
    "Firma y Preparación de la APK para Producción": [
        {
            "title": "Generador de signingConfigs Gradle",
            "difficulty": "medium",
            "description": """## Generador de Bloque signingConfigs

Genera programáticamente el bloque Gradle Kotlin DSL para firma.

**Requisitos:**
- Data class `SigningConfig(val keystorePath: String, val alias: String, val storePass: String, val keyPass: String)`.
- Función `buildGradleSigning(config: SigningConfig): String` que retorne el bloque `signingConfigs { ... }` en Kotlin DSL.
- Incluye `buildTypes.release.signingConfig = signingConfigs.release`.
- Devuelve un String listo para pegar en `app/build.gradle.kts`.""",
            "initial_code": """data class SigningConfig(val keystorePath: String, val alias: String, val storePass: String, val keyPass: String)

fun buildGradleSigning(config: SigningConfig): String { TODO() }

fun main() {
    val cfg = SigningConfig("keystore.jks", "tutor-rfa", "S3cret!", "S3cret!")
    println(buildGradleSigning(cfg))
}""",
            "solution_code": """data class SigningConfig(val keystorePath: String, val alias: String, val storePass: String, val keyPass: String)

fun buildGradleSigning(config: SigningConfig): String = ""\"
android {
    signingConfigs {
        create("release") {
            storeFile = file("${config.keystorePath}")
            storePassword = "${config.storePass}"
            keyAlias = "${config.alias}"
            keyPassword = "${config.keyPass}"
        }
    }
    buildTypes {
        release {
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
}
""\".trimIndent()

fun main() {
    val cfg = SigningConfig("keystore.jks", "tutor-rfa", "S3cret!", "S3cret!")
    println(buildGradleSigning(cfg))
}""",
            "hints": "Usa triple comilla + `trimIndent()` para strings multi-línea. Interpola con `${variable}`.",
        },
    ],
    "Publicación en Google Play Store": [
        {
            "title": "Checklist Pre-Publicación Google Play",
            "difficulty": "medium",
            "description": """## Validador Pre-Publicación Google Play

Valida si una app está lista para publicarse (reglas reales de Play Console).

**Requisitos:**
- Data class `PlayStoreConfig(val packageName: String, val versionCode: Int, val versionName: String, val minSdk: Int, val targetSdk: Int, val privacyPolicyUrl: String?, val screenshotsCount: Int, val iconPng512: Boolean)`.
- Función `validarPublicacion(cfg: PlayStoreConfig): List<String>` que devuelve lista de errores:
  - packageName debe tener al menos 2 puntos (ej. com.empresa.app).
  - versionCode ≥ 1.
  - targetSdk ≥ 34 (requisito vigente 2026).
  - privacyPolicyUrl no nulo.
  - screenshotsCount ≥ 2.
  - iconPng512 == true.
- Retorna `emptyList()` si todo OK.""",
            "initial_code": """data class PlayStoreConfig(
    val packageName: String,
    val versionCode: Int,
    val versionName: String,
    val minSdk: Int,
    val targetSdk: Int,
    val privacyPolicyUrl: String?,
    val screenshotsCount: Int,
    val iconPng512: Boolean,
)

fun validarPublicacion(cfg: PlayStoreConfig): List<String> { TODO() }

fun main() {
    val ok = PlayStoreConfig("pe.edu.iestprfa.tutor", 10, "1.0.0", 24, 34, "https://...", 5, true)
    println("OK: ${validarPublicacion(ok)}")
    val malo = PlayStoreConfig("tutor", 0, "", 24, 30, null, 1, false)
    println("ERR: ${validarPublicacion(malo)}")
}""",
            "solution_code": """data class PlayStoreConfig(
    val packageName: String,
    val versionCode: Int,
    val versionName: String,
    val minSdk: Int,
    val targetSdk: Int,
    val privacyPolicyUrl: String?,
    val screenshotsCount: Int,
    val iconPng512: Boolean,
)

fun validarPublicacion(cfg: PlayStoreConfig): List<String> {
    val errores = mutableListOf<String>()
    if (cfg.packageName.count { it == '.' } < 2) errores += "packageName inválido (necesita ≥ 2 puntos)"
    if (cfg.versionCode < 1) errores += "versionCode debe ser ≥ 1"
    if (cfg.targetSdk < 34) errores += "targetSdk debe ser ≥ 34 (requisito Play Store 2026)"
    if (cfg.privacyPolicyUrl.isNullOrBlank()) errores += "privacyPolicyUrl requerido"
    if (cfg.screenshotsCount < 2) errores += "mínimo 2 screenshots"
    if (!cfg.iconPng512) errores += "icono PNG 512x512 requerido"
    return errores
}

fun main() {
    val ok = PlayStoreConfig("pe.edu.iestprfa.tutor", 10, "1.0.0", 24, 34, "https://...", 5, true)
    println("OK: ${validarPublicacion(ok)}")
    val malo = PlayStoreConfig("tutor", 0, "", 24, 30, null, 1, false)
    println("ERR: ${validarPublicacion(malo)}")
}""",
            "hints": "Usa `mutableListOf` y acumula. `packageName.count { it == '.' }` cuenta puntos. `isNullOrBlank()` valida nulos + vacío.",
        },
    ],
}


async def seed_extra():
    async with AsyncSessionLocal() as db:
        # Load topics by title
        result = await db.execute(select(Topic))
        topics = result.scalars().all()
        topic_map = {t.title: t for t in topics}

        total_inserted = 0
        total_skipped = 0

        for topic_title, challenges in EXTRA_CHALLENGES.items():
            topic = topic_map.get(topic_title)
            if not topic:
                print(f"  ⚠ Tema no encontrado: {topic_title}")
                continue

            # Check existing max order_index for this topic (catalog only)
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

        # Verify totals
        final = await db.execute(select(CodingChallenge).where(CodingChallenge.is_ai_generated == False))
        total_catalog = len(list(final.scalars().all()))

        print(f"\n{'='*60}")
        print(f"Insertados: {total_inserted}   Saltados: {total_skipped}")
        print(f"Catálogo total: {total_catalog}")
        print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(seed_extra())
