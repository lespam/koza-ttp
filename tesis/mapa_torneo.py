"""Datos para el mapa de un torneo (static/js/mapa_torneo.js).

El contorno de la tierra y las fronteras de cada torneo están en
static/data/mapas_torneos.json. Se generaron una vez desde world-atlas 2.0.2
(Natural Earth, dominio público) con una proyección Mercator ajustada a los
estadios del torneo. Aquí se proyectan los estadios con esa misma fórmula.
"""
import json
import math
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.utils.translation import gettext as _

ARCHIVO = Path(settings.BASE_DIR) / "static" / "data" / "mapas_torneos.json"


@lru_cache(maxsize=1)
def _mapas():
    with open(ARCHIVO, encoding="utf-8") as archivo:
        return json.load(archivo)


def proyectar(mapa, lat, lon):
    """Mercator, igual que d3.geoMercator con la escala y el desplazamiento guardados."""
    x = mapa["escala"] * math.radians(lon) + mapa["tx"]
    y = mapa["ty"] - mapa["escala"] * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return round(x, 1), round(y, 1)


def textos():
    return {
        "titulo": _("Mapa de los estadios del torneo"),
        "equipo": _("Ver los viajes de un equipo"),
        "ninguno": _("Solo los estadios"),
        "viaje": _("{equipo}: {km} km de viaje en {n} traslados."),
        "sin_viaje": _("Toca un estadio o elige un equipo para ver sus viajes en la temporada."),
        "recorrido": _("Recorrido en orden"),
        "casa": _("casa"),
        "regreso": _("regreso a casa"),
        "leyenda": _("Cada punto es un estadio. La línea sigue al equipo de ciudad en ciudad, en el orden del calendario."),
    }


def datos(clave, equipos):
    """equipos: {código: (nombre, ciudad, lat, lon)} de los equipos del calendario."""
    mapa = _mapas().get(clave)
    if not mapa:
        return None
    puntos = []
    for codigo, (nombre, lugar, lat, lon) in equipos.items():
        x, y = proyectar(mapa, lat, lon)
        puntos.append({"c": codigo, "nombre": nombre, "lugar": lugar, "lat": lat, "lon": lon, "x": x, "y": y})
    return {
        "ancho": mapa["ancho"], "alto": mapa["alto"],
        "tierra": mapa["tierra"], "fronteras": mapa["fronteras"],
        "equipos": puntos, "textos": textos(),
    }
