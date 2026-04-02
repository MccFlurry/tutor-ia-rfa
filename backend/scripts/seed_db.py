"""
seed_db.py — Popula la base de datos con módulos, temas, logros y usuario admin.
Ejecutar después de las migraciones de Alembic.

Uso: python scripts/seed_db.py
  o desde docker: python /app/scripts/seed_db.py
"""

import asyncio
import os
import sys

# Add backend root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.user import User
from app.models.module import Module
from app.models.topic import Topic
from app.models.achievement import Achievement
from app.models.quiz import QuizQuestion
from app.utils.security import hash_password


engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ──────────────────────────────────────────────
# MÓDULOS
# ──────────────────────────────────────────────

MODULES = [
    {
        "title": "Fundamentos y Preparación del Entorno",
        "description": "Introduce el desarrollo móvil en Android: ecosistema, herramientas de desarrollo y configuración del entorno de programación con Android Studio.",
        "order_index": 1,
        "icon_name": "smartphone",
        "color_hex": "#6366f1",
    },
    {
        "title": "Lógica de Programación en Kotlin",
        "description": "Domina las bases de la programación en Kotlin: variables, operadores, estructuras de control, funciones y los fundamentos de la Programación Orientada a Objetos.",
        "order_index": 2,
        "icon_name": "code-2",
        "color_hex": "#0ea5e9",
    },
    {
        "title": "Elaboración de Interfaces de Usuario (UI)",
        "description": "Diseña interfaces Android profesionales con XML: layouts, componentes visuales, RecyclerView y CardView para presentar datos de forma atractiva.",
        "order_index": 3,
        "icon_name": "layout-panel-top",
        "color_hex": "#22c55e",
    },
    {
        "title": "Componentes Android y Gestión de Datos",
        "description": "Implementa la lógica de navegación entre pantallas (Activities e Intents), almacenamiento local (SQLite, SharedPreferences) y consumo de APIs REST con Retrofit.",
        "order_index": 4,
        "icon_name": "database",
        "color_hex": "#f59e0b",
    },
    {
        "title": "Funcionalidades Avanzadas y Despliegue",
        "description": "Domina el depurado con Logcat, las pruebas unitarias con JUnit y el proceso completo de publicación en Google Play Store.",
        "order_index": 5,
        "icon_name": "rocket",
        "color_hex": "#ef4444",
    },
]

# ──────────────────────────────────────────────
# TEMAS POR MÓDULO
# ──────────────────────────────────────────────

TOPICS_BY_MODULE = {
    1: [
        {
            "title": "Introducción al Desarrollo Móvil y Android",
            "order_index": 1,
            "estimated_minutes": 15,
            "has_quiz": True,
            "content": """# Introducción al Desarrollo Móvil y Android

## ¿Qué es el desarrollo móvil?

El **desarrollo móvil** es el proceso de crear aplicaciones de software que se ejecutan en dispositivos móviles como smartphones y tablets. En la actualidad, existen dos grandes ecosistemas:

- **Android** (Google): ~72% del mercado mundial
- **iOS** (Apple): ~27% del mercado mundial

## ¿Por qué Android?

Android es el sistema operativo móvil más utilizado en el mundo, y especialmente en Latinoamérica. Algunas ventajas de desarrollar para Android:

1. **Código abierto**: Android es un proyecto de código abierto basado en Linux
2. **Gran comunidad**: Millones de desarrolladores comparten recursos y soluciones
3. **Mercado masivo**: Más de 3 mil millones de dispositivos activos
4. **Herramientas gratuitas**: Android Studio y el SDK son completamente gratuitos

## Historia breve de Android

| Versión | Nombre | Año | API Level |
|---------|--------|-----|-----------|
| 8.0 | Oreo | 2017 | 26 |
| 9.0 | Pie | 2018 | 28 |
| 10 | Q | 2019 | 29 |
| 11 | R | 2020 | 30 |
| 12 | S | 2021 | 31 |
| 13 | Tiramisu | 2022 | 33 |
| 14 | Upside Down Cake | 2023 | 34 |

## Arquitectura de una app Android

Una aplicación Android típica se compone de:

- **Activities**: Pantallas individuales de la interfaz
- **Layouts (XML)**: Definen la estructura visual
- **Código Kotlin**: Lógica de la aplicación
- **AndroidManifest.xml**: Configuración y permisos

```kotlin
// Ejemplo básico de una Activity en Kotlin
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Tu código aquí
        println("¡Hola desde Android!")
    }
}
```

## Tipos de aplicaciones móviles

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| **Nativa** | Desarrollada específicamente para una plataforma | Apps de Google |
| **Híbrida** | Usa tecnologías web empaquetadas | Ionic, React Native |
| **PWA** | Aplicación web progresiva | Twitter Lite |

> **Nota importante:** En este curso nos enfocaremos en el desarrollo **nativo** con Kotlin, que es el lenguaje oficial recomendado por Google para Android.

## Resumen

- Android domina el mercado mundial de dispositivos móviles
- Kotlin es el lenguaje oficial para desarrollo Android
- Las aplicaciones nativas ofrecen el mejor rendimiento
- Android Studio es el IDE oficial y gratuito
""",
        },
        {
            "title": "Instalación y Configuración de Android Studio",
            "order_index": 2,
            "estimated_minutes": 25,
            "has_quiz": False,
            "content": """# Instalación y Configuración de Android Studio

## ¿Qué es Android Studio?

**Android Studio** es el Entorno de Desarrollo Integrado (IDE) oficial de Google para crear aplicaciones Android. Está basado en IntelliJ IDEA de JetBrains.

## Requisitos del sistema

### Windows
- Windows 10/11 (64 bits)
- 8 GB de RAM mínimo (16 GB recomendado)
- 8 GB de espacio en disco mínimo
- Resolución de pantalla: 1280 x 800 mínimo

### macOS
- macOS 10.14 (Mojave) o superior
- Procesador Apple Silicon o Intel
- 8 GB de RAM mínimo

## Pasos de instalación

### 1. Descargar Android Studio

Visita la página oficial de Android Developer y descarga la última versión estable.

### 2. Ejecutar el instalador

1. Abre el archivo descargado (`.exe` en Windows, `.dmg` en Mac)
2. Sigue el asistente de instalación
3. Selecciona los componentes:
   - ✅ Android Studio
   - ✅ Android SDK
   - ✅ Android Virtual Device (AVD)

### 3. Configuración inicial

Al abrir Android Studio por primera vez:

1. Selecciona **"Standard"** en el tipo de configuración
2. Elige el tema (claro u oscuro)
3. Espera a que se descarguen los componentes del SDK

## Verificar la instalación

Después de instalar, verifica que todo funcione:

```
Android Studio > Help > About
```

Debes ver la versión instalada y la información del SDK.

## Configurar un dispositivo virtual (AVD)

1. Abre **AVD Manager** (Tools → Device Manager)
2. Haz clic en **"Create Device"**
3. Selecciona un modelo (recomendado: **Pixel 6**)
4. Selecciona una imagen del sistema (recomendado: **API 33 - Tiramisu**)
5. Configura la RAM (recomendado: 2 GB)
6. Haz clic en **Finish**

```
💡 Tip: Si tu computadora tiene recursos limitados, puedes usar
un dispositivo físico Android conectado por USB en modo desarrollador.
```

## Activar modo desarrollador en un dispositivo físico

1. Ve a **Ajustes → Acerca del teléfono**
2. Toca **"Número de compilación"** 7 veces
3. Regresa y entra a **"Opciones de desarrollador"**
4. Activa **"Depuración por USB"**

## Estructura de Android Studio

| Área | Función |
|------|---------|
| **Project** | Explorador de archivos del proyecto |
| **Editor** | Zona principal de código |
| **Logcat** | Consola de depuración |
| **Build** | Estado de compilación |
| **Design** | Vista previa del diseño XML |

## Atajos de teclado importantes

| Atajo | Acción |
|-------|--------|
| `Ctrl + Shift + F10` | Ejecutar aplicación |
| `Ctrl + Space` | Autocompletado |
| `Ctrl + /` | Comentar línea |
| `Alt + Enter` | Corrección rápida |
| `Ctrl + B` | Ir a la definición |

## Resumen

- Android Studio es gratuito y es el IDE oficial
- Necesitas al menos 8 GB de RAM
- Incluye el SDK, emulador y herramientas de depuración
- Puedes usar un emulador o un dispositivo físico para pruebas
""",
        },
        {
            "title": "SDK de Android: Versiones y Compatibilidad",
            "order_index": 3,
            "estimated_minutes": 10,
            "has_quiz": True,
            "content": """# SDK de Android: Versiones y Compatibilidad

## ¿Qué es el Android SDK?

El **SDK (Software Development Kit)** de Android es un conjunto de herramientas que te permite desarrollar aplicaciones. Incluye:

- **Bibliotecas de Android**: APIs para acceder a funciones del sistema
- **Herramientas de compilación**: Para convertir tu código en una APK
- **Emulador**: Para probar sin un dispositivo físico
- **ADB (Android Debug Bridge)**: Para comunicarte con dispositivos

## API Level vs Versión de Android

Cada versión de Android tiene un **API Level** asociado:

```
Android 14 = API 34
Android 13 = API 33
Android 12 = API 31-32
Android 11 = API 30
Android 10 = API 29
```

## Configuración clave en `build.gradle`

```kotlin
android {
    compileSdk = 34          // SDK máximo para compilar

    defaultConfig {
        minSdk = 24          // Mínimo soportado (Android 7.0)
        targetSdk = 34       // SDK objetivo optimizado
        versionCode = 1
        versionName = "1.0"
    }
}
```

### ¿Qué significan estos valores?

| Propiedad | Significado |
|-----------|-------------|
| `compileSdk` | Versión del SDK usada para **compilar**. Usa la más reciente. |
| `minSdk` | Versión **mínima** de Android que tu app soporta |
| `targetSdk` | Versión para la cual tu app está **optimizada** |

> **Regla práctica**: `minSdk 24` cubre aproximadamente el **95%** de dispositivos Android activos en Latinoamérica.

## Gestión del SDK

En Android Studio, ve a **Tools → SDK Manager** para:

1. Ver los SDK instalados
2. Descargar nuevas versiones
3. Instalar herramientas adicionales (Build Tools, NDK, etc.)

## Compatibilidad hacia atrás

Para usar funciones nuevas en dispositivos antiguos, se usan las **bibliotecas AndroidX**:

```kotlin
// build.gradle (dependencias)
dependencies {
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
}
```

AndroidX proporciona versiones compatibles de componentes modernos que funcionan en versiones antiguas de Android.

## Resumen

- El SDK contiene todas las herramientas necesarias para desarrollar
- El API Level determina qué funciones puedes usar
- `minSdk 24` es un buen punto de partida para máxima compatibilidad
- AndroidX permite usar componentes modernos en dispositivos antiguos
""",
        },
        {
            "title": "Tu Primera Aplicación Android en Kotlin",
            "order_index": 4,
            "estimated_minutes": 30,
            "has_quiz": True,
            "content": """# Tu Primera Aplicación Android en Kotlin

## Crear un nuevo proyecto

1. Abre Android Studio
2. Selecciona **"New Project"**
3. Elige la plantilla **"Empty Views Activity"**
4. Configura el proyecto:
   - **Name**: MiPrimeraApp
   - **Package name**: com.ejemplo.miprimeraapp
   - **Language**: Kotlin
   - **Minimum SDK**: API 24 (Android 7.0)
5. Haz clic en **Finish**

## Estructura del proyecto

```
MiPrimeraApp/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/ejemplo/miprimeraapp/
│   │   │   │   └── MainActivity.kt        ← Tu código Kotlin
│   │   │   ├── res/
│   │   │   │   ├── layout/
│   │   │   │   │   └── activity_main.xml   ← Diseño de la pantalla
│   │   │   │   ├── values/
│   │   │   │   │   ├── strings.xml         ← Textos de la app
│   │   │   │   │   ├── colors.xml          ← Colores
│   │   │   │   │   └── themes.xml          ← Estilos y temas
│   │   │   │   └── drawable/               ← Imágenes e íconos
│   │   │   └── AndroidManifest.xml         ← Configuración de la app
│   │   └── test/                           ← Tests unitarios
│   └── build.gradle.kts                    ← Dependencias del módulo
├── build.gradle.kts                        ← Configuración global
└── settings.gradle.kts                     ← Proyectos incluidos
```

## El archivo `activity_main.xml`

Este archivo define la interfaz visual de tu pantalla principal:

```xml
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:gravity="center"
    android:padding="24dp">

    <TextView
        android:id="@+id/tvSaludo"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="¡Hola Mundo!"
        android:textSize="24sp"
        android:textStyle="bold" />

    <EditText
        android:id="@+id/etNombre"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:hint="Escribe tu nombre"
        android:layout_marginTop="16dp" />

    <Button
        android:id="@+id/btnSaludar"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Saludar"
        android:layout_marginTop="16dp" />

</LinearLayout>
```

## El archivo `MainActivity.kt`

```kotlin
package com.ejemplo.miprimeraapp

import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Conectar las vistas del XML con variables Kotlin
        val tvSaludo = findViewById<TextView>(R.id.tvSaludo)
        val etNombre = findViewById<EditText>(R.id.etNombre)
        val btnSaludar = findViewById<Button>(R.id.btnSaludar)

        // Configurar el evento click del botón
        btnSaludar.setOnClickListener {
            val nombre = etNombre.text.toString()
            if (nombre.isNotBlank()) {
                tvSaludo.text = "¡Hola, $nombre! 👋"
            } else {
                tvSaludo.text = "Por favor, escribe tu nombre"
            }
        }
    }
}
```

## Ejecutar la aplicación

1. Selecciona un dispositivo (emulador o físico) en la barra superior
2. Haz clic en el botón **▶ Run** (o `Shift + F10`)
3. Espera a que se compile y se instale
4. ¡Tu app debería aparecer en el dispositivo!

## Conceptos clave aprendidos

| Concepto | Descripción |
|----------|-------------|
| `Activity` | Pantalla de la aplicación |
| `setContentView` | Conecta el XML con la Activity |
| `findViewById` | Obtiene una referencia a un elemento del XML |
| `setOnClickListener` | Define qué pasa al tocar un botón |
| `R.layout.*` | Referencia a archivos de diseño |
| `R.id.*` | Referencia a elementos con id |

## Resumen

- Cada pantalla en Android es una `Activity`
- El diseño se define en XML (`res/layout/`)
- La lógica se escribe en Kotlin
- `findViewById` conecta el XML con el código
- Ejecutas la app con Run (▶) en un emulador o dispositivo real
""",
        },
    ],
    2: [
        {
            "title": "Variables, Tipos de Datos y Operadores en Kotlin",
            "order_index": 1,
            "estimated_minutes": 20,
            "has_quiz": True,
            "content": """# Variables, Tipos de Datos y Operadores en Kotlin

## Declaración de variables

En Kotlin existen dos palabras clave para declarar variables:

```kotlin
val nombre = "María"    // Inmutable (no se puede cambiar)
var edad = 20           // Mutable (se puede cambiar)

edad = 21               // ✅ OK: var se puede reasignar
// nombre = "Juan"      // ❌ Error: val no se puede reasignar
```

> **Regla de oro**: Usa `val` siempre que sea posible. Solo usa `var` cuando necesites cambiar el valor.

## Tipos de datos básicos

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `Int` | Entero (32 bits) | `val edad: Int = 20` |
| `Long` | Entero largo (64 bits) | `val poblacion: Long = 8_000_000L` |
| `Double` | Decimal (64 bits) | `val precio: Double = 19.99` |
| `Float` | Decimal (32 bits) | `val pi: Float = 3.14f` |
| `Boolean` | Verdadero/falso | `val activo: Boolean = true` |
| `String` | Cadena de texto | `val nombre: String = "Ana"` |
| `Char` | Un solo carácter | `val letra: Char = 'A'` |

## Inferencia de tipos

Kotlin puede deducir el tipo automáticamente:

```kotlin
val mensaje = "Hola"      // Kotlin infiere: String
val numero = 42            // Kotlin infiere: Int
val decimal = 3.14         // Kotlin infiere: Double
val esValido = true        // Kotlin infiere: Boolean
```

## String templates

Kotlin permite insertar variables dentro de cadenas de texto:

```kotlin
val nombre = "Carlos"
val edad = 22

println("Me llamo $nombre y tengo $edad años")
// Salida: Me llamo Carlos y tengo 22 años

println("El próximo año tendré ${edad + 1} años")
// Salida: El próximo año tendré 23 años
```

## Operadores aritméticos

```kotlin
val a = 10
val b = 3

println(a + b)    // 13 (suma)
println(a - b)    // 7  (resta)
println(a * b)    // 30 (multiplicación)
println(a / b)    // 3  (división entera)
println(a % b)    // 1  (módulo / residuo)
```

## Operadores de comparación

```kotlin
val x = 5
val y = 10

println(x == y)   // false (igualdad)
println(x != y)   // true  (desigualdad)
println(x > y)    // false (mayor que)
println(x < y)    // true  (menor que)
println(x >= 5)   // true  (mayor o igual)
```

## Operadores lógicos

```kotlin
val a = true
val b = false

println(a && b)    // false (AND: ambos deben ser true)
println(a || b)    // true  (OR: al menos uno debe ser true)
println(!a)        // false (NOT: invierte el valor)
```

## Conversión de tipos

```kotlin
val entero = 42
val decimal = entero.toDouble()    // 42.0
val texto = entero.toString()      // "42"

val textoNumero = "123"
val numero = textoNumero.toInt()   // 123
```

## Resumen

- `val` = inmutable, `var` = mutable
- Kotlin infiere tipos automáticamente
- Los String templates (`$variable`) simplifican la concatenación
- Los operadores funcionan de forma similar a otros lenguajes
""",
        },
        {
            "title": "Estructuras de Control: if/else, when y bucles",
            "order_index": 2,
            "estimated_minutes": 20,
            "has_quiz": True,
            "content": """# Estructuras de Control: if/else, when y bucles

## Condicional if/else

```kotlin
val nota = 15

if (nota >= 18) {
    println("Excelente")
} else if (nota >= 14) {
    println("Bueno")
} else if (nota >= 11) {
    println("Regular")
} else {
    println("Desaprobado")
}
```

### if como expresión

En Kotlin, `if` puede devolver un valor:

```kotlin
val nota = 16
val resultado = if (nota >= 11) "Aprobado" else "Desaprobado"
println(resultado) // Aprobado
```

## Expresión when (similar a switch)

`when` es más poderoso que el `switch` de Java:

```kotlin
val dia = 3

when (dia) {
    1 -> println("Lunes")
    2 -> println("Martes")
    3 -> println("Miércoles")
    4 -> println("Jueves")
    5 -> println("Viernes")
    6, 7 -> println("Fin de semana")
    else -> println("Día inválido")
}
```

### when con rangos y condiciones

```kotlin
val edad = 20

when {
    edad < 13 -> println("Niño")
    edad in 13..17 -> println("Adolescente")
    edad in 18..64 -> println("Adulto")
    else -> println("Adulto mayor")
}
```

## Bucle for

```kotlin
// Rango ascendente
for (i in 1..5) {
    println(i)  // 1, 2, 3, 4, 5
}

// Rango descendente
for (i in 5 downTo 1) {
    println(i)  // 5, 4, 3, 2, 1
}

// Con paso
for (i in 0..10 step 2) {
    println(i)  // 0, 2, 4, 6, 8, 10
}

// Iterar una lista
val frutas = listOf("Manzana", "Plátano", "Naranja")
for (fruta in frutas) {
    println(fruta)
}
```

## Bucle while

```kotlin
var contador = 5
while (contador > 0) {
    println("Cuenta regresiva: $contador")
    contador--
}
println("¡Despegue!")
```

## Bucle do-while

```kotlin
var numero: Int
do {
    println("Ingresa un número positivo:")
    numero = readLine()?.toIntOrNull() ?: -1
} while (numero < 0)
```

## break y continue

```kotlin
// break: sale del bucle
for (i in 1..10) {
    if (i == 5) break
    println(i)  // 1, 2, 3, 4
}

// continue: salta a la siguiente iteración
for (i in 1..10) {
    if (i % 2 == 0) continue
    println(i)  // 1, 3, 5, 7, 9
}
```

## Resumen

- `if/else` puede usarse como expresión que devuelve valor
- `when` reemplaza a `switch` y es mucho más versátil
- `for` trabaja con rangos (`..`), listas y `step`
- `while` y `do-while` funcionan como en otros lenguajes
""",
        },
        {
            "title": "Funciones, Lambdas y Alcance en Kotlin",
            "order_index": 3,
            "estimated_minutes": 25,
            "has_quiz": True,
            "content": """# Funciones, Lambdas y Alcance en Kotlin

## Funciones básicas

```kotlin
fun saludar(nombre: String): String {
    return "¡Hola, $nombre!"
}

println(saludar("María"))  // ¡Hola, María!
```

## Funciones de una sola expresión

Si el cuerpo es una sola expresión, puedes simplificar:

```kotlin
fun sumar(a: Int, b: Int): Int = a + b

fun esMayor(edad: Int): Boolean = edad >= 18
```

## Parámetros con valores por defecto

```kotlin
fun crearSaludo(nombre: String, titulo: String = "Sr./Sra."): String {
    return "Estimado/a $titulo $nombre"
}

println(crearSaludo("García"))              // Estimado/a Sr./Sra. García
println(crearSaludo("Ana", "Ing."))         // Estimado/a Ing. Ana
```

## Parámetros nombrados

```kotlin
fun registrarAlumno(nombre: String, edad: Int, carrera: String) {
    println("$nombre, $edad años, $carrera")
}

// Puedes nombrar los parámetros para mayor claridad
registrarAlumno(
    nombre = "Carlos",
    carrera = "Ingeniería de Sistemas",
    edad = 22   // El orden no importa con parámetros nombrados
)
```

## Funciones Unit (sin retorno)

```kotlin
fun mostrarMensaje(msg: String): Unit {
    println(msg)
}

// Unit se puede omitir:
fun mostrarMensaje2(msg: String) {
    println(msg)
}
```

## Lambdas (funciones anónimas)

Una lambda es una función sin nombre que se puede almacenar en una variable:

```kotlin
val duplicar = { numero: Int -> numero * 2 }
println(duplicar(5))  // 10

val sumar = { a: Int, b: Int -> a + b }
println(sumar(3, 4))  // 7
```

## Lambdas con colecciones

```kotlin
val numeros = listOf(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)

// filter: filtrar elementos
val pares = numeros.filter { it % 2 == 0 }
println(pares)  // [2, 4, 6, 8, 10]

// map: transformar elementos
val dobles = numeros.map { it * 2 }
println(dobles)  // [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]

// forEach: recorrer elementos
numeros.forEach { println(it) }
```

## Funciones de extensión

Puedes agregar funciones a clases existentes:

```kotlin
fun String.contarVocales(): Int {
    return this.count { it.lowercaseChar() in "aeiouáéíóú" }
}

println("Hola Mundo".contarVocales())  // 4
```

## Resumen

- Las funciones usan `fun` y pueden tener valores por defecto
- Las lambdas son funciones anónimas: `{ param -> cuerpo }`
- `it` es el parámetro implícito cuando hay un solo argumento
- `filter`, `map`, `forEach` son esenciales para trabajar con listas
""",
        },
        {
            "title": "POO: Clases, Objetos y Constructores",
            "order_index": 4,
            "estimated_minutes": 25,
            "has_quiz": True,
            "content": """# POO: Clases, Objetos y Constructores

## ¿Qué es la Programación Orientada a Objetos?

La **POO** es un paradigma que organiza el código en **clases** (plantillas) y **objetos** (instancias). Es fundamental para el desarrollo Android.

## Clases en Kotlin

```kotlin
class Alumno {
    var nombre: String = ""
    var edad: Int = 0
    var carrera: String = ""

    fun presentarse(): String {
        return "Soy $nombre, tengo $edad años y estudio $carrera"
    }
}

// Crear un objeto (instancia)
val alumno = Alumno()
alumno.nombre = "María"
alumno.edad = 20
alumno.carrera = "Sistemas"
println(alumno.presentarse())
```

## Constructor primario

```kotlin
class Alumno(
    val nombre: String,
    val edad: Int,
    val carrera: String
) {
    fun presentarse() = "Soy $nombre, $edad años, $carrera"
}

val alumno = Alumno("Carlos", 22, "Sistemas")
println(alumno.presentarse())
```

## Constructor secundario

```kotlin
class Alumno(val nombre: String, val edad: Int) {
    var carrera: String = "Sin asignar"

    // Constructor secundario
    constructor(nombre: String, edad: Int, carrera: String) : this(nombre, edad) {
        this.carrera = carrera
    }
}
```

## Bloque init

Se ejecuta justo después del constructor primario:

```kotlin
class Alumno(val nombre: String, val edad: Int) {
    val esAdulto: Boolean

    init {
        esAdulto = edad >= 18
        println("Alumno $nombre creado")
    }
}
```

## Propiedades con getters y setters personalizados

```kotlin
class Alumno(val nombre: String, notas: List<Double>) {
    var promedio: Double = 0.0
        private set   // Solo se puede modificar dentro de la clase

    val estado: String
        get() = if (promedio >= 10.5) "Aprobado" else "Desaprobado"

    init {
        promedio = if (notas.isNotEmpty()) notas.average() else 0.0
    }
}

val alumno = Alumno("Ana", listOf(15.0, 12.0, 18.0, 14.0))
println("Promedio: ${alumno.promedio}")  // 14.75
println("Estado: ${alumno.estado}")      // Aprobado
```

## Data classes

Para clases que solo almacenan datos, usa `data class`:

```kotlin
data class Contacto(
    val nombre: String,
    val telefono: String,
    val email: String
)

val c1 = Contacto("Ana", "987654321", "ana@email.com")
val c2 = c1.copy(nombre = "María")  // Copia modificando un campo

println(c1)  // Contacto(nombre=Ana, telefono=987654321, email=ana@email.com)
println(c1 == c2)  // false (compara por contenido)
```

## Companion object

Equivalente a los métodos `static` de Java:

```kotlin
class Calculadora {
    companion object {
        fun sumar(a: Int, b: Int) = a + b
        fun restar(a: Int, b: Int) = a - b
    }
}

println(Calculadora.sumar(5, 3))  // 8
```

## Resumen

- Las clases definen plantillas; los objetos son instancias
- El constructor primario va en la declaración de la clase
- `data class` genera automáticamente `equals`, `hashCode`, `toString` y `copy`
- `companion object` es el equivalente a `static` en Java
""",
        },
        {
            "title": "POO: Herencia, Interfaces y Polimorfismo",
            "order_index": 5,
            "estimated_minutes": 30,
            "has_quiz": True,
            "content": """# POO: Herencia, Interfaces y Polimorfismo

## Herencia en Kotlin

En Kotlin, las clases son **cerradas por defecto**. Para permitir herencia, usa `open`:

```kotlin
open class Animal(val nombre: String) {
    open fun hacerSonido(): String = "..."

    fun presentarse(): String = "Soy $nombre"
}

class Perro(nombre: String) : Animal(nombre) {
    override fun hacerSonido(): String = "¡Guau!"
}

class Gato(nombre: String) : Animal(nombre) {
    override fun hacerSonido(): String = "¡Miau!"
}

val perro = Perro("Rex")
println(perro.presentarse())   // Soy Rex
println(perro.hacerSonido())   // ¡Guau!
```

## Clases abstractas

```kotlin
abstract class Figura(val nombre: String) {
    abstract fun calcularArea(): Double

    fun describir(): String = "$nombre con área: ${calcularArea()}"
}

class Circulo(val radio: Double) : Figura("Círculo") {
    override fun calcularArea(): Double = Math.PI * radio * radio
}

class Rectangulo(val ancho: Double, val alto: Double) : Figura("Rectángulo") {
    override fun calcularArea(): Double = ancho * alto
}
```

## Interfaces

```kotlin
interface Reproducible {
    fun reproducir()
    fun pausar()
    fun detener() {
        println("Detenido")  // Implementación por defecto
    }
}

interface Descargable {
    fun descargar(url: String)
}

// Una clase puede implementar múltiples interfaces
class Cancion(val titulo: String) : Reproducible, Descargable {
    override fun reproducir() = println("Reproduciendo: $titulo")
    override fun pausar() = println("Pausado: $titulo")
    override fun descargar(url: String) = println("Descargando desde $url")
}
```

## Polimorfismo

```kotlin
fun imprimirSonidos(animales: List<Animal>) {
    for (animal in animales) {
        println("${animal.nombre}: ${animal.hacerSonido()}")
    }
}

val animales = listOf(
    Perro("Rex"),
    Gato("Misu"),
    Perro("Bobby")
)

imprimirSonidos(animales)
// Rex: ¡Guau!
// Misu: ¡Miau!
// Bobby: ¡Guau!
```

## Sealed classes (clases selladas)

Limitan las subclases posibles — ideal para representar estados:

```kotlin
sealed class ResultadoRed {
    data class Exito(val datos: String) : ResultadoRed()
    data class Error(val mensaje: String) : ResultadoRed()
    object Cargando : ResultadoRed()
}

fun manejarResultado(resultado: ResultadoRed) {
    when (resultado) {
        is ResultadoRed.Exito -> println("Datos: ${resultado.datos}")
        is ResultadoRed.Error -> println("Error: ${resultado.mensaje}")
        ResultadoRed.Cargando -> println("Cargando...")
    }
}
```

## Casting con `is` y `as`

```kotlin
fun procesarAnimal(animal: Animal) {
    if (animal is Perro) {
        // Smart cast: Kotlin sabe que es Perro aquí
        println("Es un perro que dice: ${animal.hacerSonido()}")
    }
}
```

## Resumen

- Usa `open` para permitir herencia y `override` para sobrescribir
- Las clases abstractas no se pueden instanciar directamente
- Las interfaces permiten herencia múltiple
- Polimorfismo: un mismo método se comporta distinto según el tipo
- `sealed class` es perfecto para modelar estados finitos
""",
        },
    ],
    3: [
        {
            "title": "Fundamentos de XML para Layouts Android",
            "order_index": 1,
            "estimated_minutes": 20,
            "has_quiz": True,
            "content": """# Fundamentos de XML para Layouts Android

## ¿Qué es XML en Android?

**XML (eXtensible Markup Language)** es el lenguaje usado para definir las interfaces de usuario en Android. Cada pantalla de tu app se diseña en un archivo `.xml`.

## Estructura básica de un layout

```xml
<?xml version="1.0" encoding="utf-8"?>
<LinearLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:padding="16dp">

    <TextView
        android:id="@+id/tvTitulo"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="¡Hola Mundo!" />

</LinearLayout>
```

## Atributos esenciales

| Atributo | Valores | Descripción |
|----------|---------|-------------|
| `layout_width` | `match_parent`, `wrap_content`, `XXdp` | Ancho del componente |
| `layout_height` | `match_parent`, `wrap_content`, `XXdp` | Alto del componente |
| `id` | `@+id/nombre` | Identificador único |
| `padding` | `16dp` | Espacio interior |
| `margin` | `8dp` | Espacio exterior |

## Unidades de medida

| Unidad | Uso |
|--------|-----|
| `dp` | Dimensiones de layouts y márgenes (density-independent pixels) |
| `sp` | Tamaño de texto (scale-independent pixels) |
| `px` | Píxeles absolutos (evitar) |

> **Regla**: Usa siempre `dp` para dimensiones y `sp` para texto. Nunca uses `px`.

## Tipos de Layout

### LinearLayout
Organiza los elementos en una fila (horizontal) o columna (vertical):

```xml
<LinearLayout
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:orientation="horizontal">

    <Button android:text="Botón 1"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:layout_weight="1" />

    <Button android:text="Botón 2"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:layout_weight="1" />

</LinearLayout>
```

### FrameLayout
Apila los elementos uno sobre otro:

```xml
<FrameLayout
    android:layout_width="match_parent"
    android:layout_height="200dp">

    <ImageView ... />
    <TextView
        android:layout_gravity="bottom|center_horizontal"
        android:text="Texto sobre la imagen" />

</FrameLayout>
```

## Resumen

- XML define la estructura visual de las pantallas Android
- `dp` y `sp` son las unidades correctas para diseño responsive
- `match_parent` ocupa todo el espacio disponible del padre
- `wrap_content` se ajusta al tamaño del contenido
""",
        },
        {
            "title": "Views básicos: TextView, Button, EditText e ImageView",
            "order_index": 2,
            "estimated_minutes": 20,
            "has_quiz": True,
            "content": """# Views básicos: TextView, Button, EditText e ImageView

## TextView — Mostrar texto

```xml
<TextView
    android:id="@+id/tvMensaje"
    android:layout_width="wrap_content"
    android:layout_height="wrap_content"
    android:text="Texto de ejemplo"
    android:textSize="18sp"
    android:textColor="#333333"
    android:textStyle="bold"
    android:maxLines="2"
    android:ellipsize="end" />
```

Desde Kotlin:
```kotlin
val tv = findViewById<TextView>(R.id.tvMensaje)
tv.text = "Nuevo texto desde código"
```

## Button — Botón interactivo

```xml
<Button
    android:id="@+id/btnAceptar"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:text="Aceptar"
    android:backgroundTint="#2196F3"
    android:textColor="@android:color/white" />
```

```kotlin
val btn = findViewById<Button>(R.id.btnAceptar)
btn.setOnClickListener {
    Toast.makeText(this, "¡Botón presionado!", Toast.LENGTH_SHORT).show()
}
```

## EditText — Campo de entrada

```xml
<EditText
    android:id="@+id/etEmail"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:hint="Correo electrónico"
    android:inputType="textEmailAddress"
    android:maxLength="100" />
```

Tipos de `inputType`:
| Valor | Teclado |
|-------|---------|
| `text` | Texto general |
| `textPassword` | Contraseña (oculta caracteres) |
| `textEmailAddress` | Teclado con @ |
| `number` | Solo números |
| `phone` | Teclado telefónico |

```kotlin
val email = findViewById<EditText>(R.id.etEmail)
val texto = email.text.toString()  // Obtener el texto
```

## ImageView — Mostrar imágenes

```xml
<ImageView
    android:id="@+id/ivFoto"
    android:layout_width="200dp"
    android:layout_height="200dp"
    android:src="@drawable/mi_imagen"
    android:scaleType="centerCrop"
    android:contentDescription="Foto de perfil" />
```

Tipos de `scaleType`:
| Valor | Comportamiento |
|-------|---------------|
| `centerCrop` | Recorta para llenar (mantiene proporciones) |
| `fitCenter` | Ajusta dentro del espacio |
| `centerInside` | Centra sin recortar |

## Toast — Mensaje emergente

```kotlin
Toast.makeText(this, "¡Hola desde Android!", Toast.LENGTH_SHORT).show()
// LENGTH_SHORT = 2 segundos
// LENGTH_LONG = 3.5 segundos
```

## Resumen

- `TextView` para mostrar texto, `EditText` para capturar texto
- `Button` con `setOnClickListener` para manejar clicks
- `ImageView` con `scaleType` para controlar cómo se muestra la imagen
- `Toast` para mensajes rápidos al usuario
""",
        },
        {
            "title": "Layouts: ConstraintLayout y RelativeLayout",
            "order_index": 3,
            "estimated_minutes": 25,
            "has_quiz": True,
            "content": """# Layouts: ConstraintLayout y RelativeLayout

## ConstraintLayout — El layout recomendado

`ConstraintLayout` es el layout más potente y flexible de Android. Permite posicionar elementos con **restricciones (constraints)** relativas a otros elementos o al contenedor padre.

```xml
<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:padding="16dp">

    <TextView
        android:id="@+id/tvTitulo"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:text="Mi Aplicación"
        android:textSize="24sp"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent" />

    <EditText
        android:id="@+id/etBuscar"
        android:layout_width="0dp"
        android:layout_height="wrap_content"
        android:hint="Buscar..."
        app:layout_constraintTop_toBottomOf="@id/tvTitulo"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toStartOf="@id/btnBuscar"
        android:layout_marginTop="16dp"
        android:layout_marginEnd="8dp" />

    <Button
        android:id="@+id/btnBuscar"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:text="Buscar"
        app:layout_constraintTop_toTopOf="@id/etBuscar"
        app:layout_constraintEnd_toEndOf="parent"
        app:layout_constraintBottom_toBottomOf="@id/etBuscar" />

</androidx.constraintlayout.widget.ConstraintLayout>
```

## Constraints principales

| Constraint | Significado |
|------------|-------------|
| `constraintTop_toTopOf` | Mi borde superior se alinea al borde superior de... |
| `constraintTop_toBottomOf` | Mi borde superior va debajo de... |
| `constraintStart_toStartOf` | Mi borde izquierdo se alinea al izquierdo de... |
| `constraintEnd_toEndOf` | Mi borde derecho se alinea al derecho de... |

> **Importante**: `0dp` en ConstraintLayout significa "expandir según las constraints".

## Chains (cadenas)

Las chains permiten distribuir elementos equitativamente:

```xml
<!-- Tres botones distribuidos horizontalmente -->
<Button android:id="@+id/btn1"
    app:layout_constraintHorizontal_chainStyle="spread"
    app:layout_constraintStart_toStartOf="parent"
    app:layout_constraintEnd_toStartOf="@id/btn2" ... />

<Button android:id="@+id/btn2"
    app:layout_constraintStart_toEndOf="@id/btn1"
    app:layout_constraintEnd_toStartOf="@id/btn3" ... />

<Button android:id="@+id/btn3"
    app:layout_constraintStart_toEndOf="@id/btn2"
    app:layout_constraintEnd_toEndOf="parent" ... />
```

## RelativeLayout

Posiciona elementos relativos a otros elementos o al padre:

```xml
<RelativeLayout
    android:layout_width="match_parent"
    android:layout_height="match_parent">

    <TextView
        android:id="@+id/tvCentro"
        android:layout_centerInParent="true"
        android:text="Centro" />

    <Button
        android:layout_below="@id/tvCentro"
        android:layout_centerHorizontal="true"
        android:text="Debajo" />

</RelativeLayout>
```

> **Recomendación**: Usa `ConstraintLayout` para layouts complejos. Es más eficiente que anidar múltiples `LinearLayout`.

## Resumen

- `ConstraintLayout` es el más flexible y eficiente
- Los constraints conectan los bordes de un elemento con otros
- `0dp` significa "expandir según constraints"
- Evita anidar muchos layouts — usa ConstraintLayout para layouts planos
""",
        },
        {
            "title": "RecyclerView y CardView para Listas de Datos",
            "order_index": 4,
            "estimated_minutes": 35,
            "has_quiz": True,
            "content": """# RecyclerView y CardView para Listas de Datos

## ¿Qué es RecyclerView?

`RecyclerView` es el componente estándar de Android para mostrar **listas eficientes** de datos. Reutiliza las vistas que salen de la pantalla para mostrar nuevos elementos.

## Dependencia necesaria

```kotlin
// build.gradle
dependencies {
    implementation("androidx.recyclerview:recyclerview:1.3.2")
    implementation("androidx.cardview:cardview:1.0.0")
}
```

## Paso 1: Crear el modelo de datos

```kotlin
data class Contacto(
    val nombre: String,
    val telefono: String,
    val foto: Int  // Recurso drawable
)
```

## Paso 2: Diseñar el item (item_contacto.xml)

```xml
<com.google.android.material.card.MaterialCardView
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="wrap_content"
    android:layout_margin="8dp"
    app:cardCornerRadius="12dp"
    app:cardElevation="4dp">

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:orientation="horizontal"
        android:padding="16dp"
        android:gravity="center_vertical">

        <ImageView
            android:id="@+id/ivFoto"
            android:layout_width="48dp"
            android:layout_height="48dp" />

        <LinearLayout
            android:layout_width="0dp"
            android:layout_height="wrap_content"
            android:layout_weight="1"
            android:orientation="vertical"
            android:layout_marginStart="16dp">

            <TextView
                android:id="@+id/tvNombre"
                android:textSize="16sp"
                android:textStyle="bold" />

            <TextView
                android:id="@+id/tvTelefono"
                android:textSize="14sp"
                android:textColor="#666" />

        </LinearLayout>
    </LinearLayout>
</com.google.android.material.card.MaterialCardView>
```

## Paso 3: Crear el Adapter

```kotlin
class ContactoAdapter(
    private val contactos: List<Contacto>,
    private val onClick: (Contacto) -> Unit
) : RecyclerView.Adapter<ContactoAdapter.ViewHolder>() {

    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        val tvNombre: TextView = view.findViewById(R.id.tvNombre)
        val tvTelefono: TextView = view.findViewById(R.id.tvTelefono)
        val ivFoto: ImageView = view.findViewById(R.id.ivFoto)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_contacto, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val contacto = contactos[position]
        holder.tvNombre.text = contacto.nombre
        holder.tvTelefono.text = contacto.telefono
        holder.ivFoto.setImageResource(contacto.foto)
        holder.itemView.setOnClickListener { onClick(contacto) }
    }

    override fun getItemCount() = contactos.size
}
```

## Paso 4: Configurar en la Activity

```kotlin
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val contactos = listOf(
            Contacto("Ana García", "987654321", R.drawable.avatar1),
            Contacto("Carlos López", "912345678", R.drawable.avatar2),
        )

        val recyclerView = findViewById<RecyclerView>(R.id.rvContactos)
        recyclerView.layoutManager = LinearLayoutManager(this)
        recyclerView.adapter = ContactoAdapter(contactos) { contacto ->
            Toast.makeText(this, "Seleccionado: ${contacto.nombre}", Toast.LENGTH_SHORT).show()
        }
    }
}
```

## Resumen

- `RecyclerView` es eficiente porque reutiliza vistas
- El patrón es: **Modelo → Layout XML → Adapter → Activity**
- `CardView` agrega sombra y bordes redondeados
- El Adapter conecta los datos con las vistas
""",
        },
    ],
    4: [
        {
            "title": "Activities y el Ciclo de Vida de Android",
            "order_index": 1,
            "estimated_minutes": 25,
            "has_quiz": True,
            "content": """# Activities y el Ciclo de Vida de Android

## ¿Qué es una Activity?

Una **Activity** representa una pantalla en tu aplicación. Cada pantalla (login, lista de productos, detalle) es una Activity diferente.

## Ciclo de vida de una Activity

```
onCreate()  →  onStart()  →  onResume()  →  [ACTIVA]
                                              ↓
                                          onPause()
                                              ↓
                                          onStop()
                                              ↓
                                          onDestroy()
```

| Método | ¿Cuándo se ejecuta? |
|--------|---------------------|
| `onCreate()` | Al crear la Activity (una sola vez) |
| `onStart()` | La Activity se hace visible |
| `onResume()` | La Activity está en primer plano e interactiva |
| `onPause()` | Otra Activity toma el foco parcialmente |
| `onStop()` | La Activity ya no es visible |
| `onDestroy()` | La Activity se destruye |

## Ejemplo implementado

```kotlin
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        Log.d("CicloVida", "onCreate - Inicializando la pantalla")
    }

    override fun onStart() {
        super.onStart()
        Log.d("CicloVida", "onStart - La pantalla es visible")
    }

    override fun onResume() {
        super.onResume()
        Log.d("CicloVida", "onResume - El usuario puede interactuar")
    }

    override fun onPause() {
        super.onPause()
        Log.d("CicloVida", "onPause - Guardando datos temporales")
    }

    override fun onStop() {
        super.onStop()
        Log.d("CicloVida", "onStop - Ya no es visible")
    }

    override fun onDestroy() {
        super.onDestroy()
        Log.d("CicloVida", "onDestroy - Liberando recursos")
    }
}
```

## ¿Cuándo usar cada método?

| Método | Uso típico |
|--------|------------|
| `onCreate` | Inflar layout, inicializar variables, configurar RecyclerView |
| `onResume` | Reconectar listeners, reanudar animaciones, actualizar datos |
| `onPause` | Guardar datos temporales, pausar animaciones |
| `onStop` | Liberar recursos costosos (GPS, cámara) |
| `onDestroy` | Limpiar recursos finales |

## Resumen

- Cada pantalla es una Activity con un ciclo de vida
- `onCreate` → `onResume` es el flujo de inicio normal
- Siempre guarda datos importantes en `onPause`
- Libera recursos en `onStop` o `onDestroy`
""",
        },
        {
            "title": "Navegación entre Pantallas con Intents",
            "order_index": 2,
            "estimated_minutes": 20,
            "has_quiz": True,
            "content": """# Navegación entre Pantallas con Intents

## ¿Qué es un Intent?

Un **Intent** es un objeto que permite la comunicación entre componentes de Android. Se usa principalmente para navegar entre Activities y pasar datos.

## Intent explícito — Navegar a otra pantalla

```kotlin
// En MainActivity.kt
val intent = Intent(this, DetalleActivity::class.java)
startActivity(intent)
```

## Pasar datos con Intent

```kotlin
// ENVIAR datos (desde MainActivity)
val intent = Intent(this, DetalleActivity::class.java)
intent.putExtra("nombre", "Carlos")
intent.putExtra("edad", 22)
intent.putExtra("promedio", 15.5)
startActivity(intent)

// RECIBIR datos (en DetalleActivity)
class DetalleActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_detalle)

        val nombre = intent.getStringExtra("nombre") ?: "Sin nombre"
        val edad = intent.getIntExtra("edad", 0)
        val promedio = intent.getDoubleExtra("promedio", 0.0)

        findViewById<TextView>(R.id.tvInfo).text =
            "$nombre, $edad años, promedio: $promedio"
    }
}
```

## Registrar la Activity en AndroidManifest.xml

```xml
<manifest ...>
    <application ...>
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
        <activity android:name=".DetalleActivity" />
    </application>
</manifest>
```

## Intent implícito — Acciones del sistema

```kotlin
// Abrir una página web
val intent = Intent(Intent.ACTION_VIEW, Uri.parse("https://developer.android.com"))
startActivity(intent)

// Enviar un texto (compartir)
val intent = Intent(Intent.ACTION_SEND)
intent.type = "text/plain"
intent.putExtra(Intent.EXTRA_TEXT, "¡Mira esta app!")
startActivity(Intent.createChooser(intent, "Compartir vía"))

// Llamar por teléfono
val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:987654321"))
startActivity(intent)
```

## Regresar a la Activity anterior

```kotlin
// En DetalleActivity: regresar
finish()
```

## Resumen

- Los Intents conectan Activities y permiten pasar datos
- `putExtra` envía datos, `getStringExtra`/`getIntExtra` los recibe
- Toda Activity debe estar registrada en AndroidManifest.xml
- Los Intents implícitos delegan acciones al sistema (abrir web, compartir, llamar)
""",
        },
        {
            "title": "Almacenamiento Local: SharedPreferences y SQLite",
            "order_index": 3,
            "estimated_minutes": 30,
            "has_quiz": True,
            "content": """# Almacenamiento Local: SharedPreferences y SQLite

## SharedPreferences — Datos simples (clave-valor)

Ideal para guardar configuraciones y datos pequeños.

### Guardar datos

```kotlin
val prefs = getSharedPreferences("mi_app_prefs", MODE_PRIVATE)
val editor = prefs.edit()
editor.putString("nombre_usuario", "María")
editor.putInt("edad", 20)
editor.putBoolean("tema_oscuro", true)
editor.apply()  // Guardar de forma asíncrona
```

### Leer datos

```kotlin
val prefs = getSharedPreferences("mi_app_prefs", MODE_PRIVATE)
val nombre = prefs.getString("nombre_usuario", "Invitado")
val edad = prefs.getInt("edad", 0)
val temaOscuro = prefs.getBoolean("tema_oscuro", false)
```

### Eliminar datos

```kotlin
prefs.edit().remove("nombre_usuario").apply()  // Eliminar una clave
prefs.edit().clear().apply()                    // Eliminar todo
```

## SQLite — Base de datos relacional local

Para datos estructurados y complejos, Android incluye SQLite.

### Crear un Helper

```kotlin
class BaseDatosHelper(context: Context) : SQLiteOpenHelper(
    context, "alumnos.db", null, 1
) {
    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            "CREATE TABLE alumnos (" +
            "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
            "nombre TEXT NOT NULL, " +
            "edad INTEGER NOT NULL, " +
            "carrera TEXT NOT NULL)"
        )
    }

    override fun onUpgrade(db: SQLiteDatabase, oldV: Int, newV: Int) {
        db.execSQL("DROP TABLE IF EXISTS alumnos")
        onCreate(db)
    }
}
```

### Insertar datos

```kotlin
val db = BaseDatosHelper(this).writableDatabase
val values = ContentValues().apply {
    put("nombre", "Carlos")
    put("edad", 22)
    put("carrera", "Sistemas")
}
db.insert("alumnos", null, values)
```

### Consultar datos

```kotlin
val db = BaseDatosHelper(this).readableDatabase
val cursor = db.rawQuery("SELECT * FROM alumnos", null)

while (cursor.moveToNext()) {
    val nombre = cursor.getString(cursor.getColumnIndexOrThrow("nombre"))
    val edad = cursor.getInt(cursor.getColumnIndexOrThrow("edad"))
    println("$nombre - $edad años")
}
cursor.close()
```

## ¿Cuándo usar cada uno?

| Tipo de dato | SharedPreferences | SQLite |
|-------------|------------------|--------|
| Configuración del usuario | ✅ | ❌ |
| Token de sesión | ✅ | ❌ |
| Lista de productos | ❌ | ✅ |
| Historial de compras | ❌ | ✅ |
| Tema (claro/oscuro) | ✅ | ❌ |

## Resumen

- `SharedPreferences` para datos simples clave-valor (configuraciones, tokens)
- `SQLite` para datos relacionales y estructurados (listas, historiales)
- Siempre usa `apply()` en vez de `commit()` para SharedPreferences
""",
        },
        {
            "title": "Consumo de APIs REST y Manejo de JSON",
            "order_index": 4,
            "estimated_minutes": 25,
            "has_quiz": True,
            "content": """# Consumo de APIs REST y Manejo de JSON

## ¿Qué es una API REST?

Una **API REST** es un servicio web que te permite obtener y enviar datos usando HTTP. Las aplicaciones móviles se comunican con servidores a través de APIs.

## Métodos HTTP principales

| Método | Acción | Ejemplo |
|--------|--------|---------|
| `GET` | Obtener datos | Listar productos |
| `POST` | Crear datos | Registrar usuario |
| `PUT` | Actualizar datos | Editar perfil |
| `DELETE` | Eliminar datos | Borrar publicación |

## Formato JSON

```json
{
    "id": 1,
    "nombre": "Carlos",
    "edad": 22,
    "cursos": ["Kotlin", "Android", "SQL"]
}
```

## Permisos de Internet

En `AndroidManifest.xml`:

```xml
<manifest>
    <uses-permission android:name="android.permission.INTERNET" />
    <application ...>
```

## Parseo de JSON con Gson

```kotlin
// Dependencia: implementation("com.google.code.gson:gson:2.10.1")

data class Usuario(
    val id: Int,
    val nombre: String,
    val email: String
)

// JSON String → Objeto Kotlin
val json = "{\"id\": 1, \"nombre\": \"Ana\", \"email\": \"ana@email.com\"}"
val usuario = Gson().fromJson(json, Usuario::class.java)
println(usuario.nombre)  // Ana

// Objeto Kotlin → JSON String
val jsonString = Gson().toJson(usuario)
println(jsonString)
```

## Códigos de respuesta HTTP

| Código | Significado |
|--------|-------------|
| `200` | OK — Éxito |
| `201` | Created — Recurso creado |
| `400` | Bad Request — Error del cliente |
| `401` | Unauthorized — No autenticado |
| `404` | Not Found — No existe |
| `500` | Server Error — Error del servidor |

## Resumen

- Las APIs REST usan HTTP para comunicar cliente y servidor
- JSON es el formato estándar para intercambiar datos
- Siempre necesitas el permiso `INTERNET` en el Manifest
- Gson convierte entre JSON y objetos Kotlin fácilmente
""",
        },
        {
            "title": "Retrofit para Servicios Web en Android",
            "order_index": 5,
            "estimated_minutes": 30,
            "has_quiz": True,
            "content": """# Retrofit para Servicios Web en Android

## ¿Qué es Retrofit?

**Retrofit** es la biblioteca más popular para consumir APIs REST en Android. Simplifica las llamadas HTTP y el manejo de respuestas.

## Configuración

```kotlin
// build.gradle
dependencies {
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
}
```

## Paso 1: Definir el modelo de datos

```kotlin
data class Tarea(
    val id: Int,
    val title: String,
    val completed: Boolean
)
```

## Paso 2: Crear la interfaz del servicio

```kotlin
interface TareasApi {
    @GET("todos")
    suspend fun obtenerTareas(): List<Tarea>

    @GET("todos/{id}")
    suspend fun obtenerTarea(@Path("id") id: Int): Tarea

    @POST("todos")
    suspend fun crearTarea(@Body tarea: Tarea): Tarea

    @PUT("todos/{id}")
    suspend fun actualizarTarea(@Path("id") id: Int, @Body tarea: Tarea): Tarea

    @DELETE("todos/{id}")
    suspend fun eliminarTarea(@Path("id") id: Int)
}
```

## Paso 3: Crear la instancia de Retrofit

```kotlin
object RetrofitClient {
    private const val BASE_URL = "https://jsonplaceholder.typicode.com/"

    val api: TareasApi by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(TareasApi::class.java)
    }
}
```

## Paso 4: Usar en la Activity con Coroutines

```kotlin
class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        lifecycleScope.launch {
            try {
                val tareas = RetrofitClient.api.obtenerTareas()
                // Actualizar el RecyclerView con las tareas
                println("Se obtuvieron ${tareas.size} tareas")
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity,
                    "Error: ${e.message}", Toast.LENGTH_LONG).show()
            }
        }
    }
}
```

## Anotaciones de Retrofit

| Anotación | Uso |
|-----------|-----|
| `@GET` | Petición GET |
| `@POST` | Petición POST |
| `@PUT` | Petición PUT |
| `@DELETE` | Petición DELETE |
| `@Path` | Parámetro en la URL |
| `@Query` | Parámetro de consulta (?key=value) |
| `@Body` | Cuerpo de la petición (JSON) |
| `@Header` | Cabecera HTTP personalizada |

## Resumen

- Retrofit simplifica el consumo de APIs REST en Android
- Se define una interfaz con las rutas y métodos HTTP
- Usa coroutines (`suspend fun`) para llamadas asíncronas
- Gson convierte automáticamente JSON ↔ objetos Kotlin
""",
        },
    ],
    5: [
        {
            "title": "Depuración de Aplicaciones con Logcat",
            "order_index": 1,
            "estimated_minutes": 20,
            "has_quiz": False,
            "content": """# Depuración de Aplicaciones con Logcat

## ¿Qué es Logcat?

**Logcat** es la herramienta de Android Studio que muestra los logs (registros) de tu aplicación en tiempo real. Es esencial para encontrar y solucionar errores.

## Niveles de log

```kotlin
Log.v("MiTag", "Verbose: información detallada")     // Más detallado
Log.d("MiTag", "Debug: información de depuración")    // Para desarrollo
Log.i("MiTag", "Info: información general")            // Información
Log.w("MiTag", "Warning: algo podría estar mal")       // Advertencia
Log.e("MiTag", "Error: algo falló")                    // Error
```

| Nivel | Color | Uso |
|-------|-------|-----|
| V (Verbose) | — | Todo, muy detallado |
| D (Debug) | Azul | Depuración durante desarrollo |
| I (Info) | Verde | Eventos importantes |
| W (Warn) | Amarillo | Situaciones potencialmente problemáticas |
| E (Error) | Rojo | Errores que necesitan atención |

## Ejemplo práctico

```kotlin
class MainActivity : AppCompatActivity() {
    private val TAG = "MainActivity"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Log.d(TAG, "onCreate ejecutado")

        try {
            val resultado = calcular(10, 0)
            Log.i(TAG, "Resultado: $resultado")
        } catch (e: Exception) {
            Log.e(TAG, "Error en cálculo: ${e.message}", e)
        }
    }

    private fun calcular(a: Int, b: Int): Int {
        Log.d(TAG, "calcular($a, $b)")
        return a / b
    }
}
```

## Filtrar en Logcat

- Por **tag**: Escribe el tag en el campo de búsqueda
- Por **nivel**: Selecciona el nivel mínimo (Debug, Info, etc.)
- Por **proceso**: Filtra por tu app específica

## Breakpoints (puntos de interrupción)

1. Haz clic en el margen izquierdo del editor (aparece un punto rojo)
2. Ejecuta en modo Debug (icono de insecto 🐛)
3. La ejecución se detendrá en ese punto
4. Puedes inspeccionar variables y avanzar paso a paso

## Resumen

- Logcat es tu mejor aliado para depurar
- Usa `Log.d` para desarrollo y `Log.e` para errores
- Filtra por tag para encontrar tus logs rápidamente
- Los breakpoints permiten inspeccionar el estado de la app en tiempo real
""",
        },
        {
            "title": "Pruebas Unitarias con JUnit en Android",
            "order_index": 2,
            "estimated_minutes": 25,
            "has_quiz": True,
            "content": """# Pruebas Unitarias con JUnit en Android

## ¿Qué son las pruebas unitarias?

Las **pruebas unitarias** verifican que funciones individuales producen los resultados esperados. Son esenciales para garantizar la calidad del código.

## Configuración

JUnit ya viene incluido en los proyectos Android:

```kotlin
// build.gradle (ya incluido por defecto)
dependencies {
    testImplementation("junit:junit:4.13.2")
}
```

## Tu primera prueba

```kotlin
// src/test/java/.../CalculadoraTest.kt
import org.junit.Assert.*
import org.junit.Test

class CalculadoraTest {

    @Test
    fun sumar_dosPositivos_retornaResultadoCorrecto() {
        val resultado = Calculadora.sumar(3, 5)
        assertEquals(8, resultado)
    }

    @Test
    fun dividir_entreCero_lanzaExcepcion() {
        assertThrows(ArithmeticException::class.java) {
            Calculadora.dividir(10, 0)
        }
    }
}
```

## Assertions principales

| Método | Verifica |
|--------|----------|
| `assertEquals(expected, actual)` | Que dos valores sean iguales |
| `assertNotEquals(a, b)` | Que dos valores sean diferentes |
| `assertTrue(condition)` | Que la condición sea verdadera |
| `assertFalse(condition)` | Que la condición sea falsa |
| `assertNull(object)` | Que el objeto sea nulo |
| `assertNotNull(object)` | Que el objeto NO sea nulo |

## Convención de nombres

```
metodo_escenario_resultadoEsperado
```

Ejemplos:
- `calcularPromedio_listaVacia_retornaCero`
- `validarEmail_emailInvalido_retornaFalse`
- `login_credencialesCorrectas_retornaTrue`

## Ejemplo completo con validaciones

```kotlin
class ValidadorTest {
    private val validador = Validador()

    @Test
    fun validarEmail_emailCorrecto_retornaTrue() {
        assertTrue(validador.esEmailValido("ana@gmail.com"))
    }

    @Test
    fun validarEmail_sinArroba_retornaFalse() {
        assertFalse(validador.esEmailValido("anagmail.com"))
    }

    @Test
    fun validarPassword_menosDe6Caracteres_retornaFalse() {
        assertFalse(validador.esPasswordSeguro("123"))
    }

    @Test
    fun validarPassword_6oMasCaracteres_retornaTrue() {
        assertTrue(validador.esPasswordSeguro("abc123"))
    }
}
```

## Ejecutar pruebas

- **En Android Studio**: Clic derecho en el archivo → Run Tests
- **En terminal**: `./gradlew test`

## Resumen

- Las pruebas verifican que tu código funciona correctamente
- JUnit es el framework estándar para pruebas en Android
- Usa nombres descriptivos: `metodo_escenario_resultado`
- Ejecuta las pruebas frecuentemente durante el desarrollo
""",
        },
        {
            "title": "Firma y Preparación de la APK para Producción",
            "order_index": 3,
            "estimated_minutes": 20,
            "has_quiz": False,
            "content": """# Firma y Preparación de la APK para Producción

## ¿Por qué firmar una APK?

Google Play requiere que todas las aplicaciones estén **firmadas digitalmente** con un certificado. La firma garantiza la identidad del desarrollador y la integridad de la app.

## APK vs App Bundle

| Formato | Extensión | Uso |
|---------|-----------|-----|
| APK | `.apk` | Distribución directa, testing |
| AAB (App Bundle) | `.aab` | Google Play (recomendado) |

> **Google Play ahora requiere App Bundles** (AAB) en lugar de APK.

## Generar un Keystore (almacén de claves)

1. En Android Studio: **Build → Generate Signed Bundle / APK**
2. Selecciona **Android App Bundle**
3. Haz clic en **Create new...**
4. Completa los datos:
   - **Key store path**: ruta donde guardar el archivo `.jks`
   - **Password**: contraseña del keystore
   - **Alias**: nombre del certificado
   - **Key password**: contraseña de la clave
   - **Nombre y organización**: tus datos

> **IMPORTANTE**: Guarda el keystore y las contraseñas en un lugar seguro. Si los pierdes, no podrás actualizar tu app en Google Play.

## Configurar la firma en build.gradle

```kotlin
android {
    signingConfigs {
        create("release") {
            storeFile = file("mi-keystore.jks")
            storePassword = "tu_password"
            keyAlias = "mi_alias"
            keyPassword = "tu_key_password"
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true     // Activar ProGuard/R8
            isShrinkResources = true   // Eliminar recursos no usados
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            signingConfig = signingConfigs.getByName("release")
        }
    }
}
```

## ProGuard / R8

R8 (sucesor de ProGuard) **optimiza y ofusca** tu código:
- Elimina código no utilizado
- Acorta nombres de clases y métodos
- Reduce el tamaño del APK significativamente

## Checklist antes de publicar

- [ ] Versión actualizada (`versionCode` y `versionName`)
- [ ] ProGuard/R8 activado
- [ ] Keystore guardado en lugar seguro
- [ ] App testeada en múltiples dispositivos
- [ ] Permisos mínimos necesarios
- [ ] Íconos de la app en todas las resoluciones

## Resumen

- Toda app necesita firma digital para publicarse
- Usa App Bundle (.aab) para Google Play
- R8 optimiza y reduce el tamaño de tu app
- Nunca pierdas tu keystore — es irrecuperable
""",
        },
        {
            "title": "Publicación en Google Play Store",
            "order_index": 4,
            "estimated_minutes": 30,
            "has_quiz": True,
            "content": """# Publicación en Google Play Store

## Requisitos previos

1. Cuenta de desarrollador en Google Play ($25 USD, pago único)
2. App Bundle (.aab) firmado
3. Ficha de la tienda completa (capturas, descripción, ícono)

## Crear una cuenta de desarrollador

1. Ve a [Google Play Console](https://play.google.com/console)
2. Inicia sesión con tu cuenta de Google
3. Paga la tarifa de registro ($25 USD)
4. Completa tu perfil de desarrollador

## Configurar la ficha de la tienda

### Información básica
- **Nombre de la app**: máximo 30 caracteres
- **Descripción breve**: máximo 80 caracteres
- **Descripción completa**: máximo 4000 caracteres

### Recursos gráficos necesarios

| Recurso | Tamaño | Cantidad |
|---------|--------|----------|
| Ícono | 512 x 512 px | 1 |
| Capturas de pantalla (móvil) | mín. 320px | 2-8 |
| Gráfico de funciones | 1024 x 500 px | 1 |

### Categorización
- Selecciona la **categoría** (Educación, Productividad, etc.)
- Completa el **cuestionario de clasificación de contenido**
- Define los **países** donde estará disponible

## Proceso de publicación

### 1. Crear un release
1. Ve a **Producción** en el menú lateral
2. Haz clic en **"Crear nueva versión"**
3. Sube tu App Bundle (.aab)

### 2. Revisión de Google
- Google revisa tu app (puede tomar de horas a días)
- Verifica que cumple con las políticas de la tienda

### 3. Publicación
- Una vez aprobada, tu app estará disponible en Play Store

## Tipos de pruebas en Play Console

| Tipo | Audiencia | Uso |
|------|-----------|-----|
| **Prueba interna** | Hasta 100 testers | Testing inicial rápido |
| **Prueba cerrada** | Testers por email | Beta testing controlado |
| **Prueba abierta** | Cualquier usuario | Beta pública |
| **Producción** | Todos | Versión final |

> **Recomendación**: Siempre prueba con "Prueba interna" antes de publicar en producción.

## Políticas importantes de Google Play

- No recopilar datos sin consentimiento
- Declarar todos los permisos que usa tu app
- No incluir contenido engañoso o malicioso
- Respetar derechos de propiedad intelectual

## Resumen

- Necesitas una cuenta de desarrollador ($25 USD único)
- La ficha requiere ícono, capturas y descripciones
- Siempre prueba internamente antes de publicar
- Google revisa cada versión antes de hacerla pública
""",
        },
    ],
}


# ──────────────────────────────────────────────
# LOGROS
# ──────────────────────────────────────────────

ACHIEVEMENTS = [
    {
        "name": "Primer Paso",
        "description": "Completaste tu primera lección",
        "badge_emoji": "\U0001f680",
        "badge_color": "#6366f1",
        "condition_type": "first_topic",
        "condition_value": 1,
        "condition_module_id": None,
    },
    {
        "name": "Finalizador de Módulo",
        "description": "Completaste todos los temas de un módulo",
        "badge_emoji": "\U0001f3c6",
        "badge_color": "#f59e0b",
        "condition_type": "module_completed",
        "condition_value": 1,
        "condition_module_id": None,
    },
    {
        "name": "Racha de 7 Días",
        "description": "Accediste a la plataforma 7 días consecutivos",
        "badge_emoji": "\U0001f525",
        "badge_color": "#ef4444",
        "condition_type": "streak_days",
        "condition_value": 7,
        "condition_module_id": None,
    },
    {
        "name": "Explorador del Tutor IA",
        "description": "Realizaste 10 consultas al Tutor IA",
        "badge_emoji": "\U0001f916",
        "badge_color": "#0ea5e9",
        "condition_type": "chat_messages",
        "condition_value": 10,
        "condition_module_id": None,
    },
    {
        "name": "Maestro de Kotlin",
        "description": "Completaste el Módulo 2 — Lógica de Programación",
        "badge_emoji": "\u26a1",
        "badge_color": "#22c55e",
        "condition_type": "module_completed",
        "condition_value": 2,
        "condition_module_id": None,  # Will be set to module 2's ID
    },
    {
        "name": "Quiz Perfecto",
        "description": "Obtuviste 100% en una autoevaluación",
        "badge_emoji": "\U0001f4af",
        "badge_color": "#8b5cf6",
        "condition_type": "quiz_perfect",
        "condition_value": 100,
        "condition_module_id": None,
    },
    {
        "name": "Desarrollador Completo",
        "description": "¡Completaste el 100% del curso!",
        "badge_emoji": "\U0001f393",
        "badge_color": "#10b981",
        "condition_type": "course_completed",
        "condition_value": 100,
        "condition_module_id": None,
    },
]


# ──────────────────────────────────────────────
# PREGUNTAS DE QUIZ (muestra de preguntas por tema)
# ──────────────────────────────────────────────

# topic title -> list of questions
QUIZ_QUESTIONS = {
    "Introducción al Desarrollo Móvil y Android": [
        {
            "question_text": "¿Cuál es el porcentaje aproximado de mercado mundial que tiene Android?",
            "options": ["A: ~50%", "B: ~72%", "C: ~90%", "D: ~30%"],
            "correct_option_index": 1,
            "explanation": "Android tiene aproximadamente el 72% del mercado mundial de dispositivos móviles.",
        },
        {
            "question_text": "¿Cuál es el lenguaje oficial recomendado por Google para desarrollo Android?",
            "options": ["A: Java", "B: Python", "C: Kotlin", "D: Swift"],
            "correct_option_index": 2,
            "explanation": "Kotlin es el lenguaje oficial recomendado por Google para desarrollo Android desde 2019.",
        },
        {
            "question_text": "¿Qué componente de Android representa una pantalla individual?",
            "options": ["A: Fragment", "B: Activity", "C: Service", "D: Layout"],
            "correct_option_index": 1,
            "explanation": "Una Activity representa una pantalla individual en una aplicación Android.",
        },
    ],
    "SDK de Android: Versiones y Compatibilidad": [
        {
            "question_text": "¿Qué propiedad define la versión mínima de Android que soporta tu app?",
            "options": ["A: compileSdk", "B: targetSdk", "C: minSdk", "D: buildSdk"],
            "correct_option_index": 2,
            "explanation": "minSdk define la versión mínima de Android en la que tu app puede instalarse.",
        },
        {
            "question_text": "¿Qué API Level corresponde a Android 14?",
            "options": ["A: API 30", "B: API 31", "C: API 33", "D: API 34"],
            "correct_option_index": 3,
            "explanation": "Android 14 corresponde al API Level 34.",
        },
    ],
    "Tu Primera Aplicación Android en Kotlin": [
        {
            "question_text": "¿Qué método conecta un archivo XML de layout con una Activity?",
            "options": ["A: setLayout()", "B: setContentView()", "C: loadXML()", "D: inflateView()"],
            "correct_option_index": 1,
            "explanation": "setContentView() conecta el archivo de layout XML con la Activity.",
        },
        {
            "question_text": "¿Qué método se usa para obtener una referencia a un elemento del XML?",
            "options": ["A: getView()", "B: findElement()", "C: getElementById()", "D: findViewById()"],
            "correct_option_index": 3,
            "explanation": "findViewById<T>() busca un elemento del layout por su id.",
        },
    ],
    "Variables, Tipos de Datos y Operadores en Kotlin": [
        {
            "question_text": "¿Cuál es la diferencia entre val y var en Kotlin?",
            "options": [
                "A: val es para números, var es para texto",
                "B: val es inmutable, var es mutable",
                "C: val es privado, var es público",
                "D: No hay diferencia",
            ],
            "correct_option_index": 1,
            "explanation": "val declara una variable inmutable (no se puede reasignar), var declara una variable mutable.",
        },
        {
            "question_text": "¿Qué tipo de dato se infiere para: val x = 3.14?",
            "options": ["A: Float", "B: Int", "C: Double", "D: Number"],
            "correct_option_index": 2,
            "explanation": "Kotlin infiere Double para números decimales por defecto.",
        },
    ],
    "Estructuras de Control: if/else, when y bucles": [
        {
            "question_text": "¿Cuál es el equivalente de switch en Kotlin?",
            "options": ["A: match", "B: case", "C: when", "D: select"],
            "correct_option_index": 2,
            "explanation": "La expresión 'when' en Kotlin reemplaza al switch de Java y es más versátil.",
        },
        {
            "question_text": "¿Qué imprime: for (i in 5 downTo 1 step 2) println(i)?",
            "options": ["A: 5, 4, 3, 2, 1", "B: 5, 3, 1", "C: 1, 3, 5", "D: 5, 2"],
            "correct_option_index": 1,
            "explanation": "downTo recorre de 5 a 1, y step 2 salta de 2 en 2: 5, 3, 1.",
        },
    ],
    "Funciones, Lambdas y Alcance en Kotlin": [
        {
            "question_text": "¿Qué representa 'it' en una lambda de Kotlin?",
            "options": [
                "A: La función que contiene la lambda",
                "B: El parámetro implícito cuando hay un solo argumento",
                "C: El valor de retorno",
                "D: Una variable global",
            ],
            "correct_option_index": 1,
            "explanation": "'it' es el nombre implícito del único parámetro en una lambda con un solo argumento.",
        },
    ],
    "POO: Clases, Objetos y Constructores": [
        {
            "question_text": "¿Qué genera automáticamente una data class?",
            "options": [
                "A: Solo toString()",
                "B: equals(), hashCode(), toString() y copy()",
                "C: Solo el constructor",
                "D: Métodos getter y setter",
            ],
            "correct_option_index": 1,
            "explanation": "data class genera automáticamente equals(), hashCode(), toString(), copy() y componentN().",
        },
    ],
    "POO: Herencia, Interfaces y Polimorfismo": [
        {
            "question_text": "¿Qué palabra clave permite que una clase sea heredable en Kotlin?",
            "options": ["A: abstract", "B: public", "C: open", "D: extends"],
            "correct_option_index": 2,
            "explanation": "En Kotlin las clases son cerradas por defecto. La palabra 'open' permite la herencia.",
        },
    ],
    "Fundamentos de XML para Layouts Android": [
        {
            "question_text": "¿Qué unidad se debe usar para tamaños de texto en Android?",
            "options": ["A: dp", "B: px", "C: sp", "D: em"],
            "correct_option_index": 2,
            "explanation": "sp (scale-independent pixels) es la unidad correcta para texto, ya que respeta la configuración de tamaño de texto del usuario.",
        },
    ],
    "Views básicos: TextView, Button, EditText e ImageView": [
        {
            "question_text": "¿Qué inputType se usa para un campo de contraseña?",
            "options": ["A: text", "B: textPassword", "C: password", "D: hidden"],
            "correct_option_index": 1,
            "explanation": "textPassword oculta los caracteres ingresados mostrando puntos.",
        },
    ],
    "Layouts: ConstraintLayout y RelativeLayout": [
        {
            "question_text": "¿Qué significa layout_width='0dp' en un ConstraintLayout?",
            "options": [
                "A: El elemento es invisible",
                "B: El ancho es cero píxeles",
                "C: El ancho se determina por las constraints",
                "D: Es un error de diseño",
            ],
            "correct_option_index": 2,
            "explanation": "En ConstraintLayout, 0dp (match_constraints) significa que el tamaño se calcula según las constraints definidas.",
        },
    ],
    "RecyclerView y CardView para Listas de Datos": [
        {
            "question_text": "¿Cuál es la principal ventaja de RecyclerView sobre ListView?",
            "options": [
                "A: Es más fácil de implementar",
                "B: Reutiliza vistas para mejor rendimiento",
                "C: Soporta más tipos de datos",
                "D: No necesita un Adapter",
            ],
            "correct_option_index": 1,
            "explanation": "RecyclerView reutiliza las vistas que salen de la pantalla, mejorando significativamente el rendimiento con listas grandes.",
        },
    ],
    "Activities y el Ciclo de Vida de Android": [
        {
            "question_text": "¿En qué método del ciclo de vida deberías guardar datos temporales?",
            "options": ["A: onCreate", "B: onResume", "C: onPause", "D: onDestroy"],
            "correct_option_index": 2,
            "explanation": "onPause es el lugar correcto para guardar datos temporales, ya que se ejecuta antes de que la Activity pierda el foco.",
        },
    ],
    "Navegación entre Pantallas con Intents": [
        {
            "question_text": "¿Qué método se usa para enviar datos a otra Activity?",
            "options": ["A: intent.setData()", "B: intent.putExtra()", "C: intent.addData()", "D: intent.send()"],
            "correct_option_index": 1,
            "explanation": "putExtra() permite adjuntar datos al Intent que se envía a otra Activity.",
        },
    ],
    "Almacenamiento Local: SharedPreferences y SQLite": [
        {
            "question_text": "¿Para qué tipo de datos es más apropiado SharedPreferences?",
            "options": [
                "A: Listas de productos con imágenes",
                "B: Configuraciones simples como tema claro/oscuro",
                "C: Historial de mensajes de chat",
                "D: Base de datos relacional compleja",
            ],
            "correct_option_index": 1,
            "explanation": "SharedPreferences es ideal para datos simples clave-valor como configuraciones del usuario.",
        },
    ],
    "Consumo de APIs REST y Manejo de JSON": [
        {
            "question_text": "¿Qué código HTTP indica que el recurso no fue encontrado?",
            "options": ["A: 200", "B: 401", "C: 404", "D: 500"],
            "correct_option_index": 2,
            "explanation": "El código 404 (Not Found) indica que el recurso solicitado no existe en el servidor.",
        },
    ],
    "Retrofit para Servicios Web en Android": [
        {
            "question_text": "¿Qué anotación de Retrofit se usa para enviar datos en el cuerpo de la petición?",
            "options": ["A: @Query", "B: @Path", "C: @Body", "D: @Field"],
            "correct_option_index": 2,
            "explanation": "@Body envía un objeto como JSON en el cuerpo de la petición HTTP.",
        },
    ],
    "Pruebas Unitarias con JUnit en Android": [
        {
            "question_text": "¿Qué método de JUnit verifica que dos valores sean iguales?",
            "options": ["A: assertSame()", "B: assertEquals()", "C: assertMatch()", "D: assertIs()"],
            "correct_option_index": 1,
            "explanation": "assertEquals(expected, actual) verifica que dos valores sean iguales.",
        },
    ],
    "Publicación en Google Play Store": [
        {
            "question_text": "¿Qué formato de archivo requiere Google Play actualmente para subir apps?",
            "options": ["A: APK (.apk)", "B: App Bundle (.aab)", "C: ZIP (.zip)", "D: JAR (.jar)"],
            "correct_option_index": 1,
            "explanation": "Google Play requiere App Bundles (.aab) en lugar de APK para nuevas aplicaciones.",
        },
    ],
}


async def seed():
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        result = await db.execute(select(Module))
        if result.scalars().first():
            print("La base de datos ya tiene datos. Saltando seed.")
            return

        print("Sembrando base de datos...")

        # 1. Create admin user
        admin = User(
            email=settings.ADMIN_EMAIL,
            full_name=settings.ADMIN_NAME,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        await db.flush()
        print(f"  Admin creado: {admin.email}")

        # 2. Create modules
        module_map = {}  # order_index -> Module
        for m_data in MODULES:
            module = Module(**m_data)
            db.add(module)
            await db.flush()
            module_map[module.order_index] = module
            print(f"  Módulo {module.order_index}: {module.title}")

        # 3. Create topics
        topic_map = {}  # title -> Topic
        for module_order, topics_data in TOPICS_BY_MODULE.items():
            module = module_map[module_order]
            for t_data in topics_data:
                topic = Topic(
                    module_id=module.id,
                    title=t_data["title"],
                    content=t_data["content"],
                    order_index=t_data["order_index"],
                    estimated_minutes=t_data["estimated_minutes"],
                    has_quiz=t_data["has_quiz"],
                    video_url=t_data.get("video_url"),
                )
                db.add(topic)
                await db.flush()
                topic_map[topic.title] = topic
            print(f"    → {len(topics_data)} temas creados para Módulo {module_order}")

        # 4. Create quiz questions
        total_questions = 0
        for topic_title, questions in QUIZ_QUESTIONS.items():
            topic = topic_map.get(topic_title)
            if not topic:
                print(f"  ⚠ Tema no encontrado para quiz: {topic_title}")
                continue
            for idx, q_data in enumerate(questions):
                question = QuizQuestion(
                    topic_id=topic.id,
                    question_text=q_data["question_text"],
                    options=q_data["options"],
                    correct_option_index=q_data["correct_option_index"],
                    explanation=q_data["explanation"],
                    order_index=idx,
                )
                db.add(question)
                total_questions += 1
        await db.flush()
        print(f"  {total_questions} preguntas de quiz creadas")

        # 5. Create achievements
        for a_data in ACHIEVEMENTS:
            # Set condition_module_id for "Maestro de Kotlin"
            if a_data["name"] == "Maestro de Kotlin":
                a_data["condition_module_id"] = module_map[2].id

            achievement = Achievement(
                name=a_data["name"],
                description=a_data["description"],
                badge_emoji=a_data["badge_emoji"],
                badge_color=a_data["badge_color"],
                condition_type=a_data["condition_type"],
                condition_value=a_data["condition_value"],
                condition_module_id=a_data["condition_module_id"],
            )
            db.add(achievement)
        await db.flush()
        print(f"  {len(ACHIEVEMENTS)} logros creados")

        await db.commit()
        print("\nSeed completado exitosamente.")
        print(f"  {len(MODULES)} módulos")
        print(f"  {sum(len(t) for t in TOPICS_BY_MODULE.values())} temas")
        print(f"  {total_questions} preguntas de quiz")
        print(f"  {len(ACHIEVEMENTS)} logros")
        print(f"  1 usuario admin ({settings.ADMIN_EMAIL})")


if __name__ == "__main__":
    asyncio.run(seed())
