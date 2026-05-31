"""
seed_learning_resources.py — Carga recursos de aprendizaje curados
(videos/docs) por módulo. Idempotente: skip si ya hay recursos.

URLs verificadas (mayo 2026) mediante búsqueda + WebFetch/WebSearch:
docs oficiales de developer.android.com / kotlinlang.org y videos en
español de canales reputados (MoureDev, AristiDevs). El sistema NUNCA
inventa recursos vía LLM. Revisar periódicamente: los enlaces de YouTube
pueden cambiar o retirarse; el admin puede editarlos en el panel.

Ejecutar:
    docker compose exec backend python /app/scripts/seed_learning_resources.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.user import User
from app.models.learning_resource import LearningResource

engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Recursos curados y verificados por módulo (M1-M5).
RESOURCES_BY_MODULE = {
    # M1 — Fundamentos de Android
    1: [
        {"kind": "doc", "title": "Cómo instalar Android Studio",
         "url": "https://developer.android.com/studio/install.html?hl=es-419",
         "author": "Android Developers (Google)",
         "description": "Guía oficial en español: requisitos e instalación del IDE en Windows/Mac/Linux.",
         "order_index": 0},
        {"kind": "doc", "title": "Descarga e instala Android Studio (codelab)",
         "url": "https://developer.android.com/codelabs/basic-android-kotlin-training-install-android-studio?hl=es-419",
         "author": "Android Developers (Google)",
         "description": "Codelab paso a paso (ES) para instalar y configurar Android Studio.",
         "order_index": 1},
        {"kind": "doc", "title": "Crea y ejecuta tu primera app (codelab)",
         "url": "https://developer.android.com/codelabs/basic-android-kotlin-training-first-template-project?hl=es-419",
         "author": "Android Developers (Google)",
         "description": "Primera app en Kotlin desde plantilla; recorrido por la estructura del proyecto.",
         "order_index": 2},
        {"kind": "doc", "title": "Ejecuta tu primera app en el emulador (codelab)",
         "url": "https://developer.android.com/codelabs/basic-android-kotlin-compose-emulator",
         "author": "Android Developers (Google)",
         "description": "Crear un dispositivo virtual (AVD) y ejecutar la app en el emulador.",
         "order_index": 3},
        {"kind": "video", "title": "Cómo CREAR una APP para Android [Kotlin] — Español",
         "url": "https://www.youtube.com/watch?v=tuHuo_RC5Zw",
         "author": "MoureDev by Brais Moure",
         "description": "Tutorial en español: crear la primera app en Android Studio con Kotlin.",
         "order_index": 4},
        {"kind": "video", "title": "El EMULADOR de Android a fondo — Español",
         "url": "https://www.youtube.com/watch?v=8WfQQ0BRDY8",
         "author": "MoureDev by Brais Moure",
         "description": "Tutorial en español dedicado al emulador de Android Studio.",
         "order_index": 5},
        {"kind": "video", "title": "Curso Android Studio en Kotlin desde CERO (playlist)",
         "url": "https://www.youtube.com/playlist?list=PL8ie04dqq7_OcBYDpvHrcSFVoggLi3cm_",
         "author": "Mobile Dev by AristiDevs",
         "description": "Playlist introductoria en español: Android Studio, primera app, emulador.",
         "order_index": 6},
    ],
    # M2 — Programación en Kotlin
    2: [
        {"kind": "doc", "title": "Tour interactivo de Kotlin",
         "url": "https://kotlinlang.org/docs/kotlin-tour-welcome.html",
         "author": "Kotlin (JetBrains)",
         "description": "Recorrido oficial con editor ejecutable: sintaxis, clases, null safety, colecciones, lambdas.",
         "order_index": 0},
        {"kind": "doc", "title": "Sintaxis básica de Kotlin",
         "url": "https://kotlinlang.org/docs/basic-syntax.html",
         "author": "Kotlin (JetBrains)",
         "description": "Referencia: variables val/var, tipos, funciones y control de flujo.",
         "order_index": 1},
        {"kind": "doc", "title": "Colecciones en Kotlin",
         "url": "https://kotlinlang.org/docs/collections-overview.html",
         "author": "Kotlin (JetBrains)",
         "description": "List, Set y Map; interfaces de solo lectura vs mutables.",
         "order_index": 2},
        {"kind": "doc", "title": "Clases y objetos en Kotlin (codelab)",
         "url": "https://developer.android.com/codelabs/basic-android-kotlin-compose-classes-and-objects",
         "author": "Android Developers (Google)",
         "description": "POO en Kotlin: clases, objetos, constructores, herencia y polimorfismo.",
         "order_index": 3},
        {"kind": "doc", "title": "Null safety en Kotlin (codelab)",
         "url": "https://developer.android.com/codelabs/basic-android-kotlin-compose-nullability",
         "author": "Android Developers (Google)",
         "description": "Tipos anulables, operadores ?., ?: y manejo seguro de nulos.",
         "order_index": 4},
        {"kind": "video", "title": "Null Safety en Kotlin — Español (Lección 8)",
         "url": "https://www.youtube.com/watch?v=057JbCQ4ico",
         "author": "AristiDevs",
         "description": "Explicación en español de null safety en Kotlin.",
         "order_index": 5},
    ],
    # M3 — Interfaz de usuario (UI)
    3: [
        {"kind": "doc", "title": "Curso: Aspectos básicos de Android con Compose",
         "url": "https://developer.android.com/courses/android-basics-compose/course",
         "author": "Android Developers (Google)",
         "description": "Curso oficial: Jetpack Compose, Material Design, layouts y navegación.",
         "order_index": 0},
        {"kind": "doc", "title": "Layouts en vistas (XML)",
         "url": "https://developer.android.com/guide/topics/ui/declaring-layout",
         "author": "Android Developers (Google)",
         "description": "Layouts XML, jerarquía View/ViewGroup y widgets.",
         "order_index": 1},
        {"kind": "doc", "title": "Material Design 3 en Compose",
         "url": "https://developer.android.com/develop/ui/compose/designsystems/material3",
         "author": "Android Developers (Google)",
         "description": "Theming, color, tipografía y componentes de Material Design 3.",
         "order_index": 2},
        {"kind": "doc", "title": "Navegar entre pantallas con Compose (codelab)",
         "url": "https://developer.android.com/codelabs/basic-android-kotlin-compose-navigation",
         "author": "Android Developers (Google)",
         "description": "NavHost/NavController, rutas y back stack en Jetpack Compose.",
         "order_index": 3},
        {"kind": "doc", "title": "Fragments (arquitectura de UI)",
         "url": "https://developer.android.com/guide/fragments",
         "author": "Android Developers (Google)",
         "description": "Fragments como porciones reutilizables de UI y su ciclo de vida.",
         "order_index": 4},
        {"kind": "video", "title": "Curso completo de Jetpack Compose (playlist)",
         "url": "https://www.youtube.com/playlist?list=PLrn69hTK5FBwu7VmWBg76v23atiMqz_pY",
         "author": "AristiDevs",
         "description": "Curso en español de UI con Jetpack Compose desde cero.",
         "order_index": 5},
        {"kind": "video", "title": "Jetpack Compose desde Cero (playlist)",
         "url": "https://www.youtube.com/playlist?list=PLNdFk2_brsRclwvl8ruCo_q36jVbXcCCx",
         "author": "YouTube (español)",
         "description": "UI moderna en Android con Kotlin y Jetpack Compose.",
         "order_index": 6},
        {"kind": "video", "title": "Navegar entre pantallas en Jetpack Compose",
         "url": "https://www.youtube.com/watch?v=9PiR8bL52Fw",
         "author": "YouTube (español)",
         "description": "Tutorial en español de Navigation Compose.",
         "order_index": 7},
    ],
    # M4 — Componentes y manejo de datos
    4: [
        {"kind": "doc", "title": "Ciclo de vida de Activity",
         "url": "https://developer.android.com/guide/components/activities/activity-lifecycle",
         "author": "Android Developers (Google)",
         "description": "onCreate/onStart/onResume/onPause/onStop/onDestroy con ejemplos en Kotlin.",
         "order_index": 0},
        {"kind": "doc", "title": "Guarda datos en una base local con Room",
         "url": "https://developer.android.com/training/data-storage/room",
         "author": "Android Developers (Google)",
         "description": "Persistencia con Room sobre SQLite: entidades, DAOs y base de datos.",
         "order_index": 1},
        {"kind": "doc", "title": "Obtén datos de internet con Retrofit (codelab)",
         "url": "https://developer.android.com/codelabs/basic-android-kotlin-compose-getting-data-internet",
         "author": "Android Developers (Google)",
         "description": "Consumir una API REST con Retrofit y parsear JSON en Android con Kotlin.",
         "order_index": 2},
        {"kind": "doc", "title": "Corrutinas de Kotlin en Android",
         "url": "https://developer.android.com/kotlin/coroutines",
         "author": "Android Developers (Google)",
         "description": "Concurrencia para operaciones de red/IO sin bloquear el hilo principal.",
         "order_index": 3},
        {"kind": "video", "title": "Retrofit con Kotlin y Corrutinas — llamadas a una API",
         "url": "https://www.youtube.com/watch?v=MRzcCnkZQlA",
         "author": "YouTube (español)",
         "description": "Consumir API REST + JSON con Retrofit y corrutinas, en español.",
         "order_index": 4},
    ],
    # M5 — Temas avanzados y despliegue
    5: [
        {"kind": "doc", "title": "Guía de arquitectura de apps (MVVM)",
         "url": "https://developer.android.com/topic/architecture",
         "author": "Android Developers (Google)",
         "description": "Arquitectura recomendada: capas UI/dominio/datos, ViewModel y flujo unidireccional.",
         "order_index": 0},
        {"kind": "doc", "title": "ViewModel (componente de arquitectura)",
         "url": "https://developer.android.com/topic/libraries/architecture/viewmodel",
         "author": "Android Developers (Google)",
         "description": "ViewModel: estado que sobrevive a cambios de configuración; ciclo de vida.",
         "order_index": 1},
        {"kind": "doc", "title": "Fundamentos de pruebas en Android",
         "url": "https://developer.android.com/training/testing/fundamentals",
         "author": "Android Developers (Google)",
         "description": "Tests locales vs instrumentados; tipos de prueba y buenas prácticas.",
         "order_index": 2},
        {"kind": "doc", "title": "Optimizar la app con R8 (sucesor de ProGuard)",
         "url": "https://developer.android.com/build/shrink-code",
         "author": "Android Developers (Google)",
         "description": "Reducción/ofuscación de código con R8: isMinifyEnabled y reglas keep.",
         "order_index": 3},
        {"kind": "doc", "title": "Sube tu app a Play Console (App Bundle/AAB)",
         "url": "https://developer.android.com/studio/publish/upload-bundle",
         "author": "Android Developers (Google)",
         "description": "Generar el Android App Bundle firmado y subirlo a Google Play Console.",
         "order_index": 4},
        {"kind": "doc", "title": "Publica tu app (visión general)",
         "url": "https://developer.android.com/studio/publish",
         "author": "Android Developers (Google)",
         "description": "Proceso de publicación: preparar release, AAB y distribución en Google Play.",
         "order_index": 5},
        {"kind": "video", "title": "Registrarse en Google Play Console y publicar tu app — Español",
         "url": "https://www.youtube.com/watch?v=hmY8k3KSllY",
         "author": "YouTube (español)",
         "description": "Guía en español: registro en Play Console y publicación paso a paso.",
         "order_index": 6},
    ],
}


async def seed():
    async with AsyncSessionLocal() as db:
        existing = await db.execute(select(LearningResource))
        if existing.scalars().first():
            print("Ya hay recursos. Nada que hacer.")
            return
        admin_result = await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
        admin = admin_result.scalar_one_or_none()
        created_by = admin.id if admin else None
        total = 0
        for module_id, items in RESOURCES_BY_MODULE.items():
            for item in items:
                db.add(LearningResource(
                    module_id=module_id, topic_id=None,
                    kind=item["kind"], title=item["title"], url=item["url"],
                    author=item.get("author"), description=item.get("description"),
                    order_index=item.get("order_index", 0),
                    created_by=created_by, is_active=True,
                ))
                total += 1
        await db.commit()
        print(f"Recursos sembrados: {total}")


if __name__ == "__main__":
    asyncio.run(seed())
