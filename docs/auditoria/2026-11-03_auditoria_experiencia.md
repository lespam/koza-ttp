# Auditoría de la experiencia: punto de control 1

**Fecha:** 3 de noviembre de 2026
**Estado:** punto de control. No es el diseño final.
**Versión revisada:** rama `dev`, commit `f146420` ("Prepare koza-ttp for Azure and 43 languages").
**Marcos de evaluación:**

1. **Accesibilidad:** WCAG 2.2, nivel AA.
2. **HCI:** las 10 heurísticas de usabilidad de Nielsen.
3. **Interacción humano-IA:** las guías de Microsoft (HAX, 18 guías) y la guía People + AI de Google.

---

## 1. Para qué sirve este documento

Este documento registra cómo está la experiencia **hoy**, antes de limpiar el motor.

El proyecto tiene otra línea de trabajo abierta: limpiar el código del motor de PG y probar operadores nuevos, con una rama para la versión de la tesis y otra para la versión mejorada. Esa línea puede cambiar los resultados y, por lo tanto, lo que el sitio debe contar.

**Cómo usarlo después:**

1. Cuando termine la limpieza del motor y las pruebas nuevas, repetir la auditoría con el mismo método (sección 9).
2. Marcar cada hallazgo como **resuelto**, **sigue igual** o **ya no aplica**.
3. Con esa lista, decidir la experiencia final.

La columna **"Revisar tras el motor"** indica los hallazgos que dependen de los resultados nuevos. Los que dicen "No" se pueden corregir en cualquier momento.

## 2. Decisiones ya tomadas

| Fecha | Decisión |
|---|---|
| 3 nov 2026 | El sitio presenta el resultado negativo de la tesis de forma abierta. |
| 3 nov 2026 | El sitio mostrará dos versiones lado a lado: "Tesis (2026)" y "Versión mejorada". |
| 3 nov 2026 | El rediseño paso a paso queda en pausa hasta revisar de nuevo esta auditoría. |

## 3. Cómo se hizo

1. Se levantó la app de la rama `dev` en local, con la base de datos de ejemplo `oldolddb.sqlite3` (5 configuraciones, 30 equipos, 7 calendarios).
2. Se revisaron 17 direcciones del sitio, en escritorio (1280 px) y en móvil (375 px).
3. Se corrió **axe-core 4.10** en las páginas que cargan, con las reglas de WCAG 2.0, 2.1 y 2.2 (A y AA) y buenas prácticas.
4. Se recorrió la página de inicio solo con teclado (tecla Tab).
5. Se ejecutó una optimización completa desde el botón y se midió el tiempo.
6. Se comparó el texto del sitio con el código del motor y con la tesis.

**Límites:**

- No se probó con lectores de pantalla reales (NVDA, VoiceOver) ni con personas usuarias.
- La hoja `normalize.css` no cargó en el entorno de prueba porque viene de un CDN externo. El efecto visual es menor.
- La base de datos es de ejemplo, no la de producción.

## 4. Resumen

| Severidad | Cantidad | Significado |
|---|---|---|
| Crítica | 5 | Bloquea el uso o comunica algo falso. |
| Alta | 8 | Excluye a un grupo de personas o daña la confianza. |
| Media | 11 | Dificulta el uso, pero hay forma de seguir. |
| Baja | 4 | Detalle de pulido. |
| **Total** | **28** | |

**Los cinco hallazgos más importantes** (los cinco críticos):

1. **IA-1:** el panel muestra parámetros que el motor no usa.
2. **IA-2:** el texto promete "la solución óptima" y la tesis demostró lo contrario.
3. **F-1:** 8 de las 17 direcciones dan error 500.
4. **F-2:** la página de inicio depende de que exista la configuración con ID 4.
5. **H-1:** la optimización tarda unos 16 segundos sin ningún aviso, y puede llegar a una hora.

## 5. Lo que ya funciona bien

- La página declara el idioma (`lang`) y la dirección de lectura (`dir="rtl"` en árabe).
- El selector de idioma tiene etiqueta accesible y botón alternativo sin JavaScript.
- Los enlaces `hreflang` ayudan a los buscadores a encontrar cada idioma.
- La página de inicio no tiene desplazamiento horizontal en móvil.
- El botón principal tiene un foco visible de 3 px.
- Los estilos y scripts están en archivos separados y hay una política de seguridad de contenido (CSP).
- El contenido técnico (primitivas, terminales, ciclo evolutivo) ya está escrito y es una buena base para la sección de la tesis.

## 6. Hallazgos

### 6.1 Funcionamiento

| ID | Severidad | Hallazgo | Evidencia | Revisar tras el motor |
|---|---|---|---|---|
| F-1 | Crítica | 8 de 17 direcciones dan error 500: `/equipo/`, `/liga/`, `/torneo/`, `/configuracion/`, `/configuracion/4/`, `/calendario/`, `/juego/`. Las listas enlazan a `tesis:index`, que ya no existe porque la ruta se renombró a `dashboard`. `/programa_facade/` falla porque falta su plantilla. | `tesis/templates/tesis/equipo_list.html:85` y otras 5 listas | No |
| F-2 | Crítica | La página de inicio busca la configuración con ID 4. Con una base vacía, como `old_db.sqlite3`, el sitio responde 404 en `/`. El comentario dice "ID 5". | `tesis/views.py:34-35` | No |
| F-3 | Alta | Cada ejecución sobrescribe un solo archivo, `media/svg/arbol.svg`. Si dos personas ejecutan a la vez, una ve el árbol de la otra. | `tesis/services.py:16` | Sí |
| F-4 | Media | No hay navegación entre secciones. Desde la página de inicio no se llega a equipos, torneos ni calendarios. Las páginas de administración no tienen estilos. | captura de `/calendario/1/` | No |

### 6.2 Interacción humano-IA

| ID | Severidad | Hallazgo | Guía | Evidencia | Revisar tras el motor |
|---|---|---|---|---|---|
| IA-1 | Crítica | El panel muestra población 10, 1 generación, cruce 0 y mutación 0. El motor ignora esos valores y siempre usa población 100, 20 generaciones, cruce 0.8 y mutación 0.2. La persona cree que controla algo que no controla. | HAX 1 y 2: dejar claro qué hace el sistema | `dashboard.html:51-72` contra `programagenetico.py:451-452` | Sí |
| IA-2 | Crítica | El texto dice que el proceso se repite "hasta hallar la solución óptima y más eficiente". En la tesis, la PG no superó a la búsqueda aleatoria. | HAX 2: dejar claro qué tan bien funciona | `dashboard.html:39` | Sí |
| IA-3 | Alta | El resultado aparece solo, sin una referencia para compararlo. La persona no sabe si 7,934 km es bueno o malo. | People + AI: explicar el resultado | resultado de la ejecución medida | Sí |
| IA-4 | Alta | El árbol se muestra como imagen SVG sin texto alternativo ni resumen. Una persona que no ve la imagen no recibe nada del resultado. | HAX 11: explicar por qué el sistema hizo lo que hizo | `dashboard.html:111-112` (74 textos, sin `role` ni `aria-label`) | Sí |
| IA-5 | Media | El texto describe "efímeras" y la primitiva `agregar_lista`. El motor no registra efímeras y la primitiva se llama `obtener_calendario`, como dice la tesis. | HAX 2 | `dashboard.html:156`, `:166` contra `programagenetico.py:309-313` | Sí |
| IA-6 | Media | No hay forma de cancelar, repetir con otra semilla ni comparar dos ejecuciones. | HAX 8 y 9: permitir corregir y descartar | `dashboard.html:130` | Sí |
| IA-7 | Baja | El tono exagera ("inteligencia artificial avanzada", "la magia computacional", "ciclo de vida evasivo"). Esto sube expectativas que el resultado no cumple. | HAX 1 | `dashboard.html:35-39`, `:146`, `:174` | Sí |

### 6.3 Accesibilidad (WCAG 2.2 AA)

| ID | Severidad | Hallazgo | Criterio | Evidencia | Revisar tras el motor |
|---|---|---|---|---|---|
| A-1 | Alta | El árbol solo se abre con el ratón. Es un `div` con evento de clic: el teclado no llega a él. | 2.1.1 Teclado | recorrido con Tab: idioma → tabla → botón; el árbol nunca recibe foco | No |
| A-2 | Alta | La ventana del árbol (modal) no tiene `role="dialog"`, no atrapa el foco, no cierra con Escape y su botón de cerrar es un `span` con "×". | 2.1.1, 2.4.3, 4.1.2 | `dashboard.html:192`, `static/js/app.js` | No |
| A-3 | Alta | Las páginas en otros idiomas dicen `lang="en"`, pero el texto sigue en español porque las traducciones no están hechas (65 textos vacíos en inglés). Un lector de pantalla lee el español con pronunciación inglesa. | 3.1.1 Idioma de la página | `/en/`, `locale/en/LC_MESSAGES/django.po` | No |
| A-4 | Alta | El texto gris `#7f8c8d` sobre blanco tiene contraste 3.47:1. El mínimo es 4.5:1. Además mide 12 px. | 1.4.3 Contraste | `static/css/styles.css:211-212`, `:283` (axe: 2 elementos por página) | No |
| A-5 | Media | Ninguna página tiene región `main` ni enlace para saltar al contenido. | 1.3.1, 2.4.1 | axe: `landmark-one-main` y `region` en las 9 páginas | No |
| A-6 | Media | La tabla de juegos tiene desplazamiento, pero no se puede enfocar con el teclado. | 2.1.1 | axe: `scrollable-region-focusable` | No |
| A-7 | Media | Los parámetros usan controles deslizantes desactivados. Parecen editables pero no lo son, y un lector de pantalla los anuncia como "no disponible". | 4.1.2, 3.3.2 | `dashboard.html:51-72` | Sí |
| A-8 | Media | Los emojis van dentro de los títulos (⚾, 👋, 🛠️). El lector de pantalla los lee en voz alta antes de cada título. | 1.1.1 | encabezados de `dashboard.html` | No |
| A-9 | Baja | El botón "Enviar" del formulario de equipo mide 49 × 21 px. El mínimo es 24 × 24 px. Las páginas de formularios no tienen `h1`. | 2.5.8, 1.3.1 | `/equipo/create/` | No |
| A-10 | Baja | No hay estilos para `prefers-reduced-motion` ni para modo oscuro. | 2.3.3 (AAA, recomendado) | `static/css/styles.css` | No |

### 6.4 Usabilidad (HCI)

| ID | Severidad | Hallazgo | Heurística | Evidencia | Revisar tras el motor |
|---|---|---|---|---|---|
| H-1 | Crítica | "Ejecutar optimización" es un enlace (`?ejecutar=true`). La página se queda cargando unos **16 segundos** sin aviso, con solo 4 equipos. Con 30 equipos la tesis midió casi una hora. Como es un enlace, un buscador puede seguirlo y lanzar ejecuciones en el servidor. | 1. Visibilidad del estado del sistema | `dashboard.html:130`, ejecución medida: 15.7 s | Sí |
| H-2 | Alta | La guía de inicio pide "crear un equipo, una liga y un torneo en tus paneles administrativos", pero esos paneles dan error (F-1) y no hay enlaces a ellos (F-4). | 6. Reconocer antes que recordar | `dashboard.html` sección "Guía operativa" | No |
| H-3 | Media | El título del panel muestra "ID: 4" y "4T2S6G". Son datos internos que la persona no entiende. | 2. Lenguaje del mundo real | `dashboard.html:43`, `:80` | Sí |
| H-4 | Media | La página mezcla tres públicos: quien quiere entender la PG, quien evalúa el portafolio y quien quiere usar la herramienta. No hay un camino claro para cada uno. | 8. Diseño minimalista | estructura de `dashboard.html` | Sí |
| H-5 | Baja | `/serie/` y `/svg/` tienen desplazamiento horizontal en móvil. | 1.4.10 Reflow | capturas a 375 px | No |

### 6.5 Contenido y portafolio

| ID | Severidad | Hallazgo | Evidencia | Revisar tras el motor |
|---|---|---|---|---|
| C-1 | Media | No hay enlace a la tesis, a la presentación ni al código. El pie solo dice "© 2026 Leslie Dickinson". | pie de `dashboard.html` | No |
| C-2 | Media | No se explica el problema (2,430 juegos, 30 equipos, Seattle viajó 76,683 km en 2016). Sin el problema, la solución no tiene contexto. | contenido de la tesis, cap. 1 | No |

## 7. Preguntas abiertas para la experiencia final

Estas preguntas se responden después de la limpieza del motor:

1. **¿Qué historia cuenta el sitio?** Si la versión mejorada supera al azar, la historia es "del fracaso a la mejora". Si no, es "por qué es difícil y qué aprendimos".
2. **¿La demo corre en el navegador o en el servidor?** Depende de cuánto tarde la versión mejorada con una división de 5 equipos.
3. **¿Qué parámetros puede cambiar la persona?** Solo tiene sentido mostrar controles que el motor realmente use (IA-1).
4. **¿Las páginas de administración siguen siendo públicas?** Hoy cualquiera puede crear y borrar equipos y torneos.

## 8. Mapa del sitio propuesto (pendiente de aprobar)

1. **Inicio** (`/`): qué es Koza-TTP y enlaces a las demás secciones.
2. **Historia** (`/historia/`): línea de tiempo del proyecto.
3. **La tesis** (`/tesis/`): problema, método y resultados en lenguaje claro.
4. **Experimenta** (`/experimenta/`): demo con una división pequeña, con la versión de la tesis y la mejorada lado a lado.
5. **Herramienta** (`/herramienta/`): el panel actual, corregido.

## 9. Cómo repetir esta auditoría

1. Levantar la app de la rama que se quiera revisar, con la misma base de ejemplo.
2. Visitar las mismas 17 direcciones y anotar el código HTTP de cada una.
3. Correr axe-core con las etiquetas `wcag2a`, `wcag2aa`, `wcag21aa`, `wcag22aa` y `best-practice`.
4. Recorrer la página de inicio solo con teclado.
5. Tomar capturas a 1280 px y a 375 px.
6. Ejecutar una optimización y medir el tiempo.
7. Comparar los parámetros que muestra el panel con los que usa el motor.
8. Actualizar la tabla de la sección 6 con el estado de cada hallazgo.

## Anexo A. Estado de cada dirección

| Dirección | Código | Nota |
|---|---|---|
| `/` | 200 | Con base de ejemplo. 404 con base vacía (F-2). |
| `/en/`, `/ar/` | 200 | Texto en español (A-3). |
| `/serie/`, `/condicion/`, `/equipo/create/`, `/calendario/1/`, `/pg/`, `/svg/`, `/myapp/` | 200 | Sin estilos. |
| `/equipo/`, `/liga/`, `/torneo/`, `/configuracion/`, `/configuracion/4/`, `/calendario/`, `/juego/` | 500 | `NoReverseMatch` (F-1). |
| `/programa_facade/` | 500 | `TemplateDoesNotExist` (F-1). |

## Anexo B. Resultados de axe-core

| Página | Problemas serios | Problemas moderados |
|---|---|---|
| `/`, `/en/`, `/ar/` | `color-contrast` (2), `scrollable-region-focusable` (1) | `landmark-one-main`, `region` |
| `/equipo/create/` | `target-size` (1) | `landmark-one-main`, `page-has-heading-one`, `region` (16) |
| `/serie/`, `/condicion/`, `/calendario/1/` | ninguno | `landmark-one-main`, `region` |
| `/pg/`, `/svg/` | ninguno | `landmark-one-main`, `page-has-heading-one` |

axe-core detecta cerca de un tercio de los problemas de accesibilidad. Los hallazgos A-1, A-2, A-3, A-7 y A-8 salieron de la revisión manual.
