# Archivo de la tesis

Copias de preservación de los materiales de la tesis. Todas llevan marca de agua.

| Archivo | Descripción | Fecha |
|---|---|---|
| `2026-05_tesis_version_pre-oficial.pdf` | Documento escrito de la tesis, **versión pre-oficial** (114 páginas). No es la versión oficial publicada por el ITAM | Mayo de 2026 |
| `2026-07-23_defensa_presentacion.pdf` | Presentación de la defensa (12 diapositivas) | 23 de julio de 2026 |

- **Autora:** Leslie Dickinson (tesis publicada como Leslie Pamela Brenes Valencia)
- **Asesor:** Dr. Andrés Gómez de Silva Garza
- **Institución:** Instituto Tecnológico Autónomo de México (ITAM), Ingeniería en Computación

## Uso de imágenes de terceros

Este es un proyecto académico y de divulgación **sin fines de lucro**. Las imágenes de terceros que aparecen en la presentación (logotipos, fotografías y capturas) pertenecen a sus respectivos autores y titulares. Se usan solo con fines educativos y de ilustración. Las fuentes están en la última página del PDF.

Si eres titular de alguna imagen y quieres que se retire, abre un *issue* en este repositorio y se atenderá.

## Marca de agua

`marca_de_agua.py` agrega la marca a cualquier PDF:

```bash
python docs/tesis/marca_de_agua.py original.pdf salida.pdf ["Asunto"] ["Etiqueta"]
```

Ejemplo usado para la tesis:

```bash
python docs/tesis/marca_de_agua.py Tesis_ITAM_Leslie_2026.pdf 2026-05_tesis_version_pre-oficial.pdf \
  "Documento de tesis, ITAM, 2026 (versión pre-oficial)" "Versión pre-oficial"
```

El original sin marca no se guarda en este repositorio.
