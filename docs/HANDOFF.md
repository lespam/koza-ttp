# Handoff: re-evolución de Koza-TTP

Documento de traspaso para continuar este proyecto en otros hilos o proyectos. Resume el contexto, las decisiones tomadas y lo pendiente.

Última actualización: 3 de noviembre de 2026.

---

## 1. Contexto

- **Proyecto:** Koza-TTP. Aplica Programación Genética (PG), según el modelo de John Koza (1992), al Problema de Transportación de Torneo (PTT) en béisbol de MLB.
- **Autora:** Leslie Dickinson. La tesis se publicó como **Leslie Pamela Brenes Valencia**.
- **Tesis:** *Programación Genética en la planificación de temporadas de béisbol. Problema de viabilidad y optimización.* Ingeniería en Computación, ITAM.
- **Asesor:** Dr. Andrés Gómez de Silva Garza.
- **Defensa:** 23 de julio de 2026, Ciudad de México. **Aprobada.**
- **Repositorio:** `lespam/koza-ttp`. Rama de trabajo: `claude/laughing-feynman-27w7o8`.

## 2. Objetivo de esta etapa

Que el trabajo no quede en el olvido. Debe servir para tres cosas:

1. **Ejemplo** para otros estudiantes e investigadores.
2. **Divulgación** de la programación genética.
3. **Portafolio profesional** de la autora.

La autora quiere un sitio con tres secciones:

1. **Historia:** una línea de tiempo del proyecto.
2. **La tesis:** problema, método y resultados en lenguaje claro.
3. **Experiencia interactiva única:** mostrar cómo funciona la PG y cómo se aplicaría a la MLB.

## 3. Cómo trabajar con la autora

- Responder en **español**, con lenguaje claro y directo.
- **Un tema a la vez.** Máximo 4 puntos por respuesta.
- Párrafos cortos, de 2 a 3 oraciones. Listas numeradas para pasos.
- Sin metáforas ni resúmenes redundantes al final.
- Terminar con **una sola pregunta** para confirmar el siguiente paso.
- Explicar con ejemplos reales del código cuando algo no queda claro.

## 4. Lo que dice la tesis (presentación de defensa)

- **Problema:** MLB programa 2,430 juegos para 30 equipos en unos 180 días. El PTT es NP-duro (Thielen y Westphal, 2011). Ejemplo de 2016: Seattle viajó 76,683 km y Chicago (Cubs) 39,015 km.
- **Representación:** cada calendario es un árbol de sintaxis en DEAP.
  - Primitivas: `crear_juego` (aridad 4) y `obtener_calendario` (aridad 2).
  - Terminales: fechas, equipos y la lista vacía `[]`.
- **Función de aptitud multiobjetivo** C(T) = (C1, C2):
  - C1, viabilidad: −Σ |v0 − vi|. Cada equipo debe jugar exactamente v0 juegos.
  - C2, distancia total de traslado con la fórmula haversine.
- **Arquitectura:** tres módulos lógicos (Planificador, Calculadora y Módulo PG) separados de la interfaz web en Django 4.1, con SQLite.
- **Resultados** (30 equipos, 163 juegos por equipo, 5 por serie, 20 generaciones):

  | Método | CXPB | MUTPB | C1 | Distancia (C2) | Tiempo |
  |---|---|---|---|---|---|
  | Búsqueda aleatoria | 0.0 | 0.0 | 0 (válido) | 2,663,470.70 km | 200.25 s |
  | Programación genética | 0.8 | 0.2 | 0 (válido) | 3,182,738.33 km | 3,337.81 s |

- **Hallazgo principal:** la PG no superó al azar. El mejor calendario siempre salió de la generación 0. Los operadores genéricos (`cxOnePointLeafBiased`, `mutNodeReplacement`) modifican nodos "a ciegas" y rompen la viabilidad. Los pesos (100.0, −1.0) y el Hall of Fame solo conservaron soluciones iniciales, y el algoritmo quedó en un óptimo local.
- **Trabajo futuro:** operadores contextuales que permuten series o bloques válidos. También se menciona la computación cuántica.

**Valor para la divulgación:** el resultado negativo es una historia honesta y didáctica. La experiencia interactiva puede mostrar por qué falla la PG con operadores ciegos y cómo la mejorarían los operadores contextuales.

## 5. Estado del código (verificado)

### 5.1 La arquitectura sí está desacoplada

Se probó el motor fuera de la app web, con 6 equipos (NYA, BOS, TOR, BAL, TBA, NYN), 2 series de 3 juegos y abril de 2027.

- Importar `programa_genetico.planificador.ModuloPlanificador` funciona **sin Django configurado**.
- Con una configuración mínima de Django, la evolución corre 20 generaciones en unos 14 segundos. Resultado: diferencial de juegos 0 y 6,862 km.
- `tesis/models.py` solo traduce la base de datos a llamadas del planificador.

### 5.2 Solo dos puntos siguen atados a Django

1. **Zona horaria:** `programa_genetico/planificador.py:5` y `:276` usan `django.utils.timezone.get_default_timezone()`. Se puede cambiar por un parámetro `zona_horaria`.
2. **Carpeta de salida:** `programa_genetico/programagenetico.py` usa `settings.BASE_DIR` en 5 lugares para guardar txt, csv, svg, pdf y jpg. Se puede cambiar por un parámetro `carpeta_salida`.

Con esos dos cambios, de unas 10 líneas, el motor queda 100% exportable.

### 5.3 Detalles encontrados

- `static/csv/teams.csv` usa **abreviaturas estilo Retrosheet**: `NYA`, `NYN`, `TBA`, `CHA`, `CHN`, `KCA`, `LAN`, `SDN`, `SFN`, `SLN`, `ANA`.
- `programa_genetico/calculadora.py` (`calcula_distancia`): si un equipo no existe en el CSV, lanza `UnboundLocalError` en lugar de un error claro. Además, el mensaje para el equipo A imprime el nombre del equipo B.
- `programa_genetico/planificador.txt` es una copia vieja de `planificador.py`. No usarla como referencia.
- `myapp/` es una copia casi idéntica de `tesis/`.
- El repositorio incluye `old_db.sqlite3`, `oldolddb.sqlite3` y `nohup.out` (215 KB).

### 5.4 Prueba mínima para reproducir

```python
import sys, datetime, pandas as pd
sys.path.insert(0, ".")  # raíz del repositorio
from django.conf import settings
settings.configure(TIME_ZONE="America/Mexico_City", BASE_DIR="salida")
from programa_genetico.planificador import ModuloPlanificador

t = pd.read_csv("static/csv/teams.csv")
eq = ["NYA", "BOS", "TOR", "BAL", "TBA", "NYN"]
coords = t[t["Team Abbreviation"].isin(eq)][["Team Abbreviation", "Lat", "Lon"]]
coords.columns = ["equipo", "lat", "lon"]

p = ModuloPlanificador()
p.establecer_equipos(eq)
p.establecer_fechas([(datetime.date(2027, 4, 1) + datetime.timedelta(d)).isoformat() for d in range(28)])
p.establecer_numero_de_juegos_por_equipo(3)
p.setNumeroDeSeriesPorEquipo(2)
p.establecer_coordenadas_equipos(coords)
print(p.ejecutar_programa_genetico())
```

Dependencias: `deap pandas numpy matplotlib haversine django pygraphviz`. `pygraphviz` requiere `graphviz` y `libgraphviz-dev` del sistema.

## 6. Decisiones tomadas

| Tema | Decisión |
|---|---|
| Nombre en la cita formal (APA y BibTeX) | "Brenes Valencia, L. P.", el nombre registrado en el ITAM |
| Nombre en el sitio, README y portafolio | "Leslie Dickinson", con la nota "Tesis publicada como Leslie Pamela Brenes Valencia" |
| Imágenes de terceros en la presentación | Se quedan. Hay un aviso de uso sin fines de lucro y un proceso de retiro por *issue* |
| Materiales de la tesis | Se guardan en `docs/tesis/` **con marca de agua**. Los originales sin marca no se suben |
| Sugerencia opcional | Crear un perfil ORCID para unir ambos nombres |

## 7. Decisiones abiertas

1. **Servidor o sitio estático.** La autora quiere mantener un servidor porque la idea original era una aplicación real que otro software de calendarización pudiera adaptar. La propuesta en discusión es una arquitectura híbrida:
   - Separar el motor como paquete de Python (`koza_ttp`), sin Django.
   - Un **sitio estático** (GitHub Pages) para la divulgación, con demos que corren en el navegador mediante Pyodide o un motor en JavaScript. Sirve para instancias pequeñas, como una división de 5 equipos.
   - Una **API** (Django o FastAPI) para que otro software use el motor con instancias grandes.

   **No está aprobada.** Confirmar con la autora antes de implementarla.
2. **Diseño de la experiencia interactiva.** Todavía no se discute.

## 8. Pendientes

1. **Documento escrito de la tesis (versión pre-oficial).** `Tesis_ITAM_Leslie_2026.pdf`, de 3.77 MB. La subida por el chat falló dos veces y la causa es desconocida. Alternativa: subirlo por GitHub a `docs/tesis/` en la rama de trabajo. Después, aplicarle la marca de agua, borrar el original y marcarlo como "versión pre-oficial".
2. **Línea de tiempo.** Pedir a la autora las fechas clave: inicio, protocolo, avances, defensa y aprobación. El historial de git solo cubre de mayo a julio de 2026.
3. Ajustar los dos puntos atados a Django (sección 5.2), si se aprueba la arquitectura híbrida.

## 9. Archivos creados en esta etapa

- `docs/tesis/2026-07-23_defensa_presentacion.pdf`: presentación de la defensa con marca de agua.
- `docs/tesis/marca_de_agua.py`: script para aplicar la marca. Uso: `python docs/tesis/marca_de_agua.py original.pdf salida.pdf`.
- `docs/tesis/README.md`: ficha de la tesis y aviso de uso de imágenes.
- `README.md`: autoría y cita actualizadas.
- `docs/HANDOFF.md`: este documento.
