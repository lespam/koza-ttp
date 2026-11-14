# Backlog: demo pública

Fecha: 2026-11-09. Pedido por Les.
Plan pensado para ejecutarse con **Sonnet a esfuerzo bajo**: una tarea = un PR pequeño.

## Reglas para quien ejecute (léelas antes de cada tarea)

1. Haz **una sola tarea por PR**. No mezcles tareas.
2. Toca solo los archivos que dice la tarea. Si necesitas otro, explica por qué en el PR.
3. Textos visibles en español, en lenguaje claro: oraciones cortas, sin jerga sin explicar.
4. Todo texto visible va dentro de `{% translate %}` o `_()`. **No edites** archivos de `locale/`: Les corre la acción manual "Traducir".
5. Accesibilidad (WCAG 2.2 AA): texto de 16px o más, nada en mayúsculas largas, íconos siempre con palabra, formularios con `<label>`.
6. Prueba con `python manage.py test` antes de abrir el PR. Agrega las pruebas que pide la tarea.
7. **No hagas deploy.** El deploy es manual (`deploy.yml` con `workflow_dispatch`).
8. Si algo de la tarea no cuadra con el código, detente y pregunta. No adivines.

## Orden recomendado

| # | Tarea | Depende de |
|---|-------|------------|
| A1 | Portada con la nueva narrativa | — |
| A2 | Historia: paso 7 con la nueva narrativa | — |
| A3 | Avisos de la demo y la guía | — |
| A4 | "Mi tesis dijo la verdad" vive solo en Histórico | A1, A2 |
| C1 | Límites de equipos y juegos en un solo lugar | — |
| C2 | Aplicar los límites en la guía manual | C1 |
| C3 | Aplicar los límites antes de ejecutar el motor | C1 |
| B1 | Las 7 configuraciones y el nombre aleatorio | C1 |
| B2 | Crear todo a partir de una configuración | B1 |
| B3 | Página para elegir una configuración | B2 |
| B4 | Ver la ejecución | B3 |
| D1 | Tarjeta "Versión completa: Próximamente" | B3 |

---

## Bloque A. Cambiar la narrativa

**Idea:** ahora el mensaje principal es "tenemos un motor que funciona". La tesis fue el **piloto inicial**. La frase "Mi tesis dijo la verdad" queda **solo** en la documentación de la tesis (página Histórico).

Datos que ya existen y se deben reusar (no escribir cifras a mano): `project/estado_motor.py`, variable `MOTOR`. En plantillas se leen como `motor.mejorado.frente_al_azar`, `motor.tesis.frente_al_azar`, etc.

### A1. Portada con la nueva narrativa

- **Archivos:** `tesis/templates/tesis/inicio.html`, `tesis/tests.py` (clase `PaginaDeInicio`).
- **Qué hacer:**
  1. Cambia el `<h1>` (línea 12). Texto propuesto: "Calendarios de béisbol con programación genética: **el motor mejorado viaja {{ motor.mejorado.frente_al_azar }}**." Usa `blocktranslate` con variable.
  2. Cambia el párrafo `.entrada`. Texto propuesto: "Koza-TTP nació como mi tesis en el ITAM. Ese primer piloto no superó al azar. La versión por bloques sí lo supera, y aquí puedes probarla."
  3. Cambia `{% block descripcion %}`: quita "resultado honesto". Propuesta: "Koza-TTP: programación genética para calendarios de béisbol. Empezó como tesis de Leslie Dickinson (ITAM) y hoy tiene un motor que supera al azar."
- **Listo cuando:** la portada no contiene "dijo la verdad" y muestra la cifra de `motor.mejorado`. Prueba nueva en `PaginaDeInicio`: `assertNotContains(r, "dijo la verdad")`.

### A2. Historia: paso 7 con la nueva narrativa

- **Archivos:** `tesis/templates/tesis/historia.html` (sección `#paso-7`, cerca de la línea 74), `tesis/tests.py` (clase `HistoriaPasoAPaso`).
- **Qué hacer:**
  1. Título del paso 7: de "La tesis dijo la verdad" a "Del piloto a un motor que funciona".
  2. Pon primero el párrafo del motor mejorado y después el de la tesis.
  3. En el párrafo de la tesis di "El piloto de la tesis (2026) no fue mejor que elegir calendarios al azar: …".
  4. En `{% block descripcion %}` (línea 4) quita "resultado honesto de la tesis"; usa "del piloto de la tesis al motor mejorado".
- **Listo cuando:** `/historia/` no contiene "dijo la verdad". Prueba con `assertNotContains`.

### A3. Avisos de la demo y la guía

- **Archivos:** `tesis/templates/tesis/dashboard.html` (bloque `.aviso-honesto`, líneas 37 a 44), `tesis/templates/tesis/guia/configuracion.html` (bloque `.aviso-honesto`), `documentacion/templates/documentacion/base.html` (línea 18, `og:description`).
- **Qué hacer:** donde diga "motor de la tesis", di "motor del piloto (la tesis)". No cambies la lógica `{% if motor.en_la_demo == "tesis" %}`. En `og:description` cambia "con resultados honestos" por "del piloto de la tesis al motor mejorado".
- **Listo cuando:** las pruebas existentes pasan y ninguna de esas páginas dice "dijo la verdad".

### A4. "Mi tesis dijo la verdad" vive solo en Histórico

- **Archivos:** `documentacion/templates/documentacion/historico.html`, `tesis/tests.py`.
- **Qué hacer:** agrega al inicio de Histórico una sección corta con `<h2>` "Mi tesis dijo la verdad". Contenido: el piloto no superó al azar ({{ motor.tesis.frente_al_azar }}) y reportarlo así fue la decisión correcta. Máximo 3 oraciones.
- **Listo cuando:** prueba nueva que recorre `/`, `/historia/`, `/demo/`, `/guia/` y `/documentacion/` y confirma que **ninguna** dice "dijo la verdad", y que `/documentacion/historico/` **sí** lo dice. (Revisa en `documentacion/urls.py` la URL exacta.)

---

## Bloque C. Limitar el cómputo

**Idea:** la demo pública no debe dejar que alguien pida un torneo enorme. Se limita el **número de equipos** y el **número total de juegos**.

Fórmula de juegos totales de un torneo (ya existe en `Torneo`):
`juegos_totales = equipos × numero_de_series × numero_de_juegos ÷ 2`

### C1. Límites en un solo lugar

- **Archivos nuevos:** `tesis/limites.py`. Pruebas en `tesis/tests.py` (clase nueva `LimitesDeLaDemo`).
- **Qué hacer:**
  ```python
  MAXIMO_DE_EQUIPOS = 12      # valor propuesto; Les confirma
  MAXIMO_DE_JUEGOS = 300      # juegos totales del torneo; Les confirma

  def juegos_totales(equipos: int, series: int, juegos_por_serie: int) -> int: ...
  def dentro_del_limite(equipos: int, series: int, juegos_por_serie: int) -> bool: ...
  def revisar_torneo(torneo) -> list[str]:
      """Devuelve la lista de mensajes de error (vacía si está bien)."""
  ```
  `revisar_torneo` cuenta los equipos con `torneo.obtener_equipos_del_torneo()`.
- **Listo cuando:** pruebas de `juegos_totales` (por ejemplo 4 equipos, 3 series, 2 juegos = 12) y de los dos límites.

### C2. Aplicar los límites en la guía manual

- **Archivos:** `tesis/guia.py` (`LigaGuiaForm.clean_equipos` y `TorneoGuiaForm.clean`), `tesis/tests.py` (clase `GuiaDeCincoPasos`).
- **Qué hacer:**
  1. En `clean_equipos`: error si hay más de `MAXIMO_DE_EQUIPOS`. Mensaje: "En la demo pública el máximo es {n} equipos."
  2. En `TorneoGuiaForm.clean`: calcula los juegos totales con los equipos de la liga de la sesión. Para eso el formulario necesita saber cuántos equipos hay: pásalo como argumento `equipos=` desde `GuiaPasoView.formulario`. Mensaje: "Este torneo tendría {n} juegos. En la demo pública el máximo es {m}."
  3. Agrega a ambos campos un `help_text` con el máximo.
- **Listo cuando:** pruebas con 13 equipos (error) y con un torneo que pasa de 300 juegos (error).

### C3. Aplicar los límites antes de ejecutar el motor

- **Archivos:** `tesis/views.py` (`DashboardView.get`, `RunProgramaGenetico`, `RunProgramaGeneticoAlt`, `GenerarJuegosView`, `GenerarNuevosJuegosView`), `tesis/tests.py`.
- **Por qué:** las páginas de administración (CRUD) también crean torneos sin límite. El freno final va donde se ejecuta el motor.
- **Qué hacer:** antes de ejecutar, llama `revisar_torneo(config.calendario.torneo)`. Si hay errores, **no ejecutes**: muestra los mensajes con `messages.error` y la página normal.
- **Listo cuando:** prueba con un torneo de 13 equipos: `?ejecutar=true` no llama al motor (usa `mock.patch` sobre `run_genetic_algorithm_logic`, como ya hacen las pruebas de `PaginaDeDemo`).

---

## Bloque B. Guía con 7 configuraciones listas

**Idea:** la persona **elige una de 7 configuraciones** y **ve cómo se ejecuta**. La guía de 5 pasos para registrar todo **se queda**, como opción "Hazlo tú mismo". El nombre del torneo es **siempre aleatorio**.

### B1. Las 7 configuraciones y el nombre aleatorio

- **Archivos nuevos:** `tesis/escenarios.py`. Pruebas en `tesis/tests.py` (clase nueva `Escenarios`).
- **Qué hacer:**
  1. Una lista `ESCENARIOS` con 7 diccionarios. Cada uno tiene: `clave` (slug), `titulo`, `descripcion` (1 oración), `equipos` (lista de abreviaturas de `static/csv/teams.csv`), `numero_de_series`, `numero_de_juegos`, `dias` (duración del torneo), `poblacion`, `generaciones`, `cruce`, `mutacion`.
  2. Propuesta de los 7 (Les puede cambiarlos):

     | clave | título | equipos |
     |-------|--------|---------|
     | `costa-oeste` | Costa Oeste | SEA, SFN, OAK, LAN, ANA, SDN |
     | `costa-este` | Costa Este | NYA, NYN, BOS, PHI, BAL, WAS |
     | `centro` | Centro del país | CHN, CHA, MIL, SLN, MIN, KCA |
     | `texas-y-sur` | Texas y el sur | HOU, TEX, ATL, MIA, TBA |
     | `rivales-lejanos` | Rivales lejanos | SEA, MIA, BOS, SD |
     | `liga-americana-chica` | Liga Americana (8 equipos) | BOS, NYA, TOR, CLE, DET, HOU, SEA, OAK |
     | `mapa-completo` | El mapa completo (12 equipos) | SEA, SFN, LAN, SDN, ARI, COL, TEX, CHN, ATL, MIA, NYA, BOS |

     Las abreviaturas son las de `teams.csv` (estilo Retrosheet: `NYA`, `LAN`, `SFN`…). No uses las de MLB (`NYY`, `LAD`).
  3. Función `nombre_aleatorio(rng=random)` que arma un nombre con dos listas cortas, por ejemplo "Copa" / "Torneo" / "Serie" + "del Pacífico" / "de las Montañas" / "del Río" … + año actual. Las palabras van con `gettext` para poder traducirse.
- **Listo cuando:** prueba que valida que los 7 escenarios: tienen abreviaturas que existen en `teams.csv`, y cumplen `dentro_del_limite` de C1. Prueba que `nombre_aleatorio(random.Random(1))` siempre da el mismo nombre.

### B2. Crear todo a partir de una configuración

- **Archivos:** `tesis/escenarios.py` (función nueva), `tesis/tests.py`.
- **Qué hacer:** función `crear_desde_escenario(clave) -> Configuracion` que:
  1. Busca o crea cada `Equipo` por `team_abbreviation`, con nombre, ciudad, lat y lon de `teams.csv` (usa `get_or_create`).
  2. Crea `Liga` (nombre = título del escenario), `Torneo` (nombre = `nombre_aleatorio()`, `fecha_inicio` = hoy, `fecha_fin` = hoy + `dias`, `metodo="haversine"`, `unidad="km"`), `Calendario` y `Configuracion`.
  3. Llama `configuracion.generar_calendario_aleatorio()`.
  4. Todo dentro de `transaction.atomic()`.
- **Listo cuando:** prueba que crea un escenario y confirma: el torneo tiene los equipos del escenario, el calendario tiene juegos, y dos llamadas dan nombres de torneo distintos (con `rng` distinto) sin duplicar equipos.

### B3. Página para elegir una configuración

- **Archivos:** `tesis/guia.py` (vista nueva `GuiaEscenariosView`), `tesis/urls.py`, plantilla nueva `tesis/templates/tesis/guia/escenarios.html`, `tesis/templates/tesis/guia/inicio.html`, `tesis/tests.py`.
- **Qué hacer:**
  1. `GET /guia/` muestra las 7 configuraciones como un formulario con `radio buttons` (un `<fieldset>` con `<legend>`). Cada opción muestra título, descripción y "N equipos · M juegos".
  2. Debajo, un enlace "Hazlo tú mismo: registra todo en 5 pasos" que lleva al flujo actual (`/guia/equipos/`).
  3. `POST /guia/` con `escenario=<clave>` llama `crear_desde_escenario`, guarda en sesión con `recordar(request, liga=..., torneo=..., configuracion=...)` y redirige a la página de B4.
  4. Clave inválida: vuelve a mostrar el formulario con un error claro.
  5. Ajusta el texto de la tarjeta "Probar la herramienta" en `tesis/templates/tesis/inicio.html`: "Elige una de 7 configuraciones y mira cómo el motor arma el calendario. Sin cuenta."
- **Listo cuando:** pruebas de GET (aparecen 7 opciones), POST válido (redirige) y POST inválido (muestra error). Actualiza `GuiaDeCincoPasos.test_recorrido_completo` si cambió el texto que revisa.

### B4. Ver la ejecución

- **Archivos:** `tesis/guia.py`, plantilla nueva `tesis/templates/tesis/guia/ejecucion.html`, `tesis/urls.py`, `tesis/tests.py`.
- **Qué hacer (versión simple, sin JavaScript nuevo):**
  1. URL `guia/ejecucion/`. Lee la configuración de la sesión (`recorrido(request)`).
  2. Muestra los 5 pasos ya hechos, con ✓ y texto (Equipos, Liga, Torneo con su nombre aleatorio, Configuración, Calendario con N juegos). Reusa `_pasos.html` si sirve.
  3. Botón "Ejecutar el motor" que lleva a `/demo/?configuracion=<pk>&ejecutar=true`.
  4. Nota: "Tarda unos segundos."
- **Listo cuando:** prueba que, después del POST de B3, la página muestra el nombre del torneo y el enlace con `ejecutar=true`.

---

## Bloque D. Versión completa: "Próximamente"

### D1. Tarjeta "Versión completa: Próximamente"

- **Archivos:** `tesis/templates/tesis/guia/escenarios.html` (de B3), el CSS de la guía (busca la hoja que usa `guia/_base.html`), `tesis/tests.py`.
- **Qué hacer:** al final de la página de escenarios, una tarjeta con:
  - Título: "Versión completa".
  - Etiqueta visible: "Próximamente" (texto, no solo color).
  - Lista: cambiar los estadios, agregar equipos, más equipos y más juegos, ajustar los parámetros del motor.
  - **Sin botón de pago, sin formulario y sin enlace falso.** No uses `disabled` en un botón: solo texto.
- **Listo cuando:** prueba que `/guia/` contiene "Próximamente".

---

## Fuera de este backlog (anotado para después)

1. **La demo todavía ejecuta el motor de la tesis** (`project/estado_motor.py`, `"en_la_demo": "tesis"`). La nueva narrativa dice "tenemos uno que funciona", pero el botón "Ejecutar" no usa el motor por bloques. Conectar ese motor a la demo es otra tarea, más grande.
2. **El motor por bloques necesita 30 equipos** (2 ligas × 3 divisiones × 5 equipos). Con el límite de C1 (12 equipos) no podría correr en la demo pública. Hay que decidir cuál va primero.
3. El motor de la tesis ignora la población y las generaciones de la configuración (están fijas en `programa_genetico/programagenetico.py`, línea 557). Por eso este plan limita equipos y juegos, no parámetros.
4. Las páginas CRUD (`/equipo/create/`, etc.) siguen abiertas al público. C3 evita que ejecuten algo pesado, pero no evita que creen datos.

## Decisiones que confirma Les

1. Valores de `MAXIMO_DE_EQUIPOS` (propuesto 12) y `MAXIMO_DE_JUEGOS` (propuesto 300).
2. Las 7 configuraciones de B1.
3. Los textos propuestos del bloque A.
