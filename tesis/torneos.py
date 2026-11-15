"""Torneos ya configurados para la demo.

Se inspiran en las ligas que analiza la tesis (apéndice I: LMB, LMP, LVBP y NPB),
en la de Corea que cita (Kim, 2019) y en las Grandes Ligas. La demo acepta de 3
a 10 equipos, así que de las ligas más grandes se toma una zona o una liga.

Las coordenadas son las del estadio o, si no, las de su ciudad (aproximadas):
solo sirven para medir el viaje en línea recta.
"""
import csv
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.utils.translation import gettext_lazy as _

ARCHIVO_MLB = Path(settings.BASE_DIR) / "static" / "csv" / "teams.csv"
# Diez equipos repartidos por todo el país: así el viaje importa
PRESELECCION_MLB = ["SEA", "SFN", "LAN", "ARI", "TEX", "CHN", "ATL", "MIA", "NYA", "BOS"]


@lru_cache(maxsize=1)
def _equipos_mlb():
    with open(ARCHIVO_MLB, encoding="utf-8") as archivo:
        filas = sorted(csv.DictReader(archivo), key=lambda f: f["Team Name"])
    return {f["Team Abbreviation"]: (f["Team Name"], f["Arena Location"], float(f["Lat"]), float(f["Lon"]))
            for f in filas}


# (código, nombre, ciudad, latitud, longitud)
LMP = [
    ("HER", "Naranjeros de Hermosillo", "Hermosillo, Sonora", 29.0729, -110.9559),
    ("CUL", "Tomateros de Culiacán", "Culiacán, Sinaloa", 24.8091, -107.3940),
    ("MAZ", "Venados de Mazatlán", "Mazatlán, Sinaloa", 23.2494, -106.4111),
    ("MXL", "Águilas de Mexicali", "Mexicali, Baja California", 32.6245, -115.4523),
    ("JAL", "Charros de Jalisco", "Zapopan, Jalisco", 20.6767, -103.4600),
    ("GSV", "Algodoneros de Guasave", "Guasave, Sinaloa", 25.5675, -108.4697),
    ("MOC", "Cañeros de Los Mochis", "Los Mochis, Sinaloa", 25.7904, -108.9858),
    ("NAV", "Mayos de Navojoa", "Navojoa, Sonora", 27.0728, -109.4437),
    ("OBR", "Yaquis de Obregón", "Ciudad Obregón, Sonora", 27.4828, -109.9304),
    ("MTY", "Sultanes de Monterrey", "Monterrey, Nuevo León", 25.7180, -100.3106),
]

LMB_SUR = [
    ("MEX", "Diablos Rojos del México", "Ciudad de México", 19.4040, -99.0860),
    ("OAX", "Guerreros de Oaxaca", "Oaxaca, Oaxaca", 17.0732, -96.7266),
    ("YUC", "Leones de Yucatán", "Mérida, Yucatán", 20.9874, -89.6155),
    ("TAB", "Olmecas de Tabasco", "Villahermosa, Tabasco", 17.9892, -92.9281),
    ("PUE", "Pericos de Puebla", "Puebla, Puebla", 19.0700, -98.1700),
    ("CAM", "Piratas de Campeche", "Campeche, Campeche", 19.8454, -90.5237),
    ("QRO", "Tigres de Quintana Roo", "Cancún, Quintana Roo", 21.1619, -86.8515),
    ("LEO", "Bravos de León", "León, Guanajuato", 21.1250, -101.6860),
    ("VER", "El Águila de Veracruz", "Veracruz, Veracruz", 19.1738, -96.1342),
]

LVBP = [
    ("LEO", "Leones del Caracas", "Caracas", 10.4880, -66.8890),
    ("MAG", "Navegantes del Magallanes", "Valencia, Carabobo", 10.1620, -68.0077),
    ("ARA", "Tigres de Aragua", "Maracay, Aragua", 10.2469, -67.5958),
    ("LAR", "Cardenales de Lara", "Barquisimeto, Lara", 10.0678, -69.3474),
    ("ZUL", "Águilas del Zulia", "Maracaibo, Zulia", 10.6666, -71.6125),
    ("ANZ", "Caribes de Anzoátegui", "Puerto La Cruz, Anzoátegui", 10.2135, -64.6328),
    ("LAG", "Tiburones de La Guaira", "La Guaira", 10.6000, -66.9300),
    ("MAR", "Bravos de Margarita", "Porlamar, Nueva Esparta", 10.9577, -63.8697),
]

NPB_PACIFICO = [
    ("H", "Fukuoka SoftBank Hawks", "Fukuoka", 33.5954, 130.3622),
    ("E", "Tohoku Rakuten Golden Eagles", "Sendai", 38.2564, 140.9024),
    ("L", "Saitama Seibu Lions", "Tokorozawa", 35.7686, 139.4204),
    ("M", "Chiba Lotte Marines", "Chiba", 35.6453, 140.0310),
    ("B", "Orix Buffaloes", "Osaka", 34.6694, 135.4762),
    ("F", "Hokkaido Nippon-Ham Fighters", "Kitahiroshima", 42.9899, 141.5497),
]

KBO = [
    ("OB", "Doosan Bears", "Seúl (Jamsil)", 37.5122, 127.0719),
    ("LG", "LG Twins", "Seúl (Jamsil)", 37.5122, 127.0719),
    ("WO", "Kiwoom Heroes", "Seúl (Gocheok)", 37.4982, 126.8671),
    ("SK", "SSG Landers", "Incheon", 37.4370, 126.6932),
    ("KT", "KT Wiz", "Suwon", 37.2997, 127.0097),
    ("SS", "Samsung Lions", "Daegu", 35.8411, 128.6815),
    ("LT", "Lotte Giants", "Busan", 35.1940, 129.0615),
    ("NC", "NC Dinos", "Changwon", 35.2225, 128.5823),
    ("HT", "Kia Tigers", "Gwangju", 35.1682, 126.8891),
    ("HH", "Hanwha Eagles", "Daejeon", 36.3171, 127.4291),
]


def _tabla(lista):
    return {c: (nombre, lugar, lat, lon) for c, nombre, lugar, lat, lon in lista}


# config: valores ya elegidos para el paso 2 (la persona puede cambiarlos)
TORNEOS = [
    {"clave": "mlb", "nombre": _("Grandes Ligas (MLB), Estados Unidos y Canadá"),
     "descripcion": _("10 de los 30 equipos, de costa a costa. Puedes cambiar cuáles."),
     "fuente": _("La liga que usa la tesis para sus pruebas."),
     "equipos": _equipos_mlb, "marcados": PRESELECCION_MLB,
     "config": {"juegos_por_serie": 3, "series_por_pareja": 2}},
    {"clave": "lmp", "nombre": _("Liga Mexicana del Pacífico (LMP)"),
     "descripcion": _("10 equipos del noroeste de México. Series de 3 juegos en dos vueltas."),
     "fuente": _("Tesis, apéndice I.2."),
     "equipos": lambda: _tabla(LMP), "marcados": [c for c, *_r in LMP],
     "config": {"juegos_por_serie": 3, "series_por_pareja": 2}},
    {"clave": "lmb_sur", "nombre": _("Liga Mexicana de Béisbol (LMB), zona sur"),
     "descripcion": _("9 equipos, del centro de México a la península de Yucatán."),
     "fuente": _("Tesis, apéndice I.1."),
     "equipos": lambda: _tabla(LMB_SUR), "marcados": [c for c, *_r in LMB_SUR],
     "config": {"juegos_por_serie": 3, "series_por_pareja": 2}},
    {"clave": "lvbp", "nombre": _("Liga Venezolana de Béisbol Profesional (LVBP)"),
     "descripcion": _("8 equipos cercanos entre sí. Muchos juegos contra cada rival."),
     "fuente": _("Tesis, apéndice I.3."),
     "equipos": lambda: _tabla(LVBP), "marcados": [c for c, *_r in LVBP],
     "config": {"juegos_por_serie": 3, "series_por_pareja": 4}},
    {"clave": "npb_pacifico", "nombre": _("Béisbol profesional de Japón (NPB), Liga del Pacífico"),
     "descripcion": _("6 equipos, de Fukuoka a Hokkaido."),
     "fuente": _("Tesis, apéndice I.4."),
     "equipos": lambda: _tabla(NPB_PACIFICO), "marcados": [c for c, *_r in NPB_PACIFICO],
     "config": {"juegos_por_serie": 3, "series_por_pareja": 4}},
    {"clave": "kbo", "nombre": _("Organización Coreana de Béisbol (KBO)"),
     "descripcion": _("10 equipos. Dos comparten estadio en Seúl."),
     "fuente": _("La tesis cita el trabajo de Kim (2019) sobre esta liga."),
     "equipos": lambda: _tabla(KBO), "marcados": [c for c, *_r in KBO],
     "config": {"juegos_por_serie": 3, "series_por_pareja": 2}},
]
POR_CLAVE = {t["clave"]: t for t in TORNEOS}
TORNEO_POR_DEFECTO = "mlb"


def torneo(clave):
    return POR_CLAVE.get(clave) or POR_CLAVE[TORNEO_POR_DEFECTO]


def equipos_de(clave):
    """{código: (nombre, ciudad, lat, lon)} del torneo."""
    return torneo(clave)["equipos"]()
