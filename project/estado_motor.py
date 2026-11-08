"""Una sola fuente de verdad sobre qué tan bien funciona cada versión del motor.

La portada, la demo y la página de avances leen estos datos. Cuando haya un
resultado nuevo, se cambia aquí y las tres páginas quedan de acuerdo.
Fuente de las cifras: PR #14 (python -m programa_genetico.comparar_bloques --semillas 3).
"""
from django.utils.translation import gettext_lazy as _

MOTOR = {
    "tesis": {
        "nombre": _("Versión de la tesis (2026)"),
        # 19.5 % más distancia que la búsqueda aleatoria (tabla del Histórico)
        "frente_al_azar": _("19.5\u00a0% más distancia que elegir calendarios al azar"),
        "supera_al_azar": False,
    },
    "mejorado": {
        "nombre": _("Motor por bloques (versión mejorada)"),
        "frente_al_azar": _("13\u00a0% menos viaje que elegir calendarios al azar"),
        "corridas": 3,
        "equipos": 30,
        "supera_al_azar": True,
        "fecha": "2026-11-08",
    },
    # Motor que corre el botón "Ejecutar optimización" de la demo
    "en_la_demo": "tesis",
}


def motor(request):
    datos = dict(MOTOR)
    datos["demo"] = MOTOR[MOTOR["en_la_demo"]]
    return {"motor": datos}
