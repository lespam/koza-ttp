# Sitio estático: cómo se actualiza

Desde noviembre de 2026 el sitio público es **estático** (solo HTML, CSS, JS y datos).
Se publica gratis en **GitHub Pages**. El sitio con servidor (Django en Azure) quedó
congelado en la rama `sitio-django-2026-11-15`.

## El proceso

1. **En tu computadora, corre el experimento.** Cada experimento guarda sus
   resultados en `static/data/`. Por ejemplo:
   - `python manage.py precalcular_demo` → los 6 torneos de la demo
     (`static/data/demo/<torneo>.json`). Acepta `--pasos` y `--torneos`.
   - `python /mnt/project-files/motor_pg/generaciones/grabar_evolucion.py` → la
     evolución del motor PG (`static/data/evolucion_pg.json`).
2. **Revisa en local** (opcional):
   `python manage.py generar_estatico --idiomas es-mx en` y abre
   `sitio_estatico/` con `python -m http.server -d sitio_estatico 8000`.
3. **Sube los cambios a `main`** (PR como siempre).
4. **Publica:** GitHub → Actions → **"Publicar sitio estático"** → Run workflow.
   Un push o un merge **no** publica solo.

## Qué incluye y qué no

- **Sí:** portada, historia, demo (6 torneos ya calculados), temporada 2023,
  motor PG por dentro, documentación. En los 45 idiomas.
- **No (necesitan servidor):** la guía de 5 pasos, el registro de equipos, ligas y
  calendarios, y el tablero de la tesis que corre el algoritmo en vivo. Siguen en
  la rama congelada.

## Configuración de una sola vez (Les)

1. GitHub → Settings → Pages → Source: **GitHub Actions**.
2. DNS de `lesliedickinson.dev`: registro **CNAME** `koza-ttp` → `lespam.github.io`.
3. Cuando el sitio estático funcione, se puede apagar la VM de Azure.
