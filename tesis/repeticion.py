"""Repetición de la temporada 2023: el motor contra el calendario real de las Grandes Ligas.

Solo usa datos reales (pedido de Les): los 30 equipos y estadios de 2023 y el
calendario oficial de ese año como referencia. Muestra una corrida ya guardada
del motor por bloques, así la página no hace cálculos largos en cada visita.

Las cifras están en static/data/temporada_2023.json. Se generaron una vez con
el script de /mnt/project-files/motor_pg/mlb2023/datos_demo.py y guardan solo
números calculados (km y rachas por equipo), no el calendario de MLB.
"""
import json
from pathlib import Path

from django.conf import settings
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from .historia import estadios

ARCHIVO_DATOS = Path(settings.BASE_DIR) / "static" / "data" / "temporada_2023.json"


def cargar_datos():
    with open(ARCHIVO_DATOS, encoding="utf-8") as f:
        return json.load(f)


def maximo(equipos, clave):
    return max(v[clave] for v in equipos.values())


def textos_js():
    """Textos que repeticion.js escribe dentro de los dibujos."""
    return {
        "grafica": _("Kilómetros de la temporada por generación del motor, comparados con el calendario oficial y con el azar"),
        "oficial": _("Calendario oficial"),
        "azar": _("Mejor al azar"),
        "motor": _("Motor por bloques"),
        "generacion": _("Generación"),
        "estado": _("Generación {gen} de {total}: {km} km"),
        "incumple": _("Todavía no cumple el número de juegos de cada equipo."),
        "millones": _("millones de km"),
        "ejes": _("Eje vertical: de {min} a {max} millones de km. Eje horizontal: generaciones 0 a {ultima}."),
        "mapa": _("Mapa: cada círculo es un equipo; más grande significa más kilómetros en la temporada"),
        "equipo_km": _("{equipo}: {km} km"),
        "reproducir": _("Reproducir"),
        "pausar": _("Pausar"),
    }


class RepeticionView(TemplateView):
    template_name = "tesis/repeticion.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        datos = cargar_datos()
        nombres = {e["codigo"]: e["equipo"] for e in estadios()}
        filas = []
        for codigo, nombre in sorted(nombres.items(), key=lambda x: x[1]):
            filas.append({"codigo": codigo, "equipo": nombre,
                          "oficial": datos["oficial"]["equipos"][codigo]["km"],
                          "motor": datos["motor"]["equipos"][codigo]["km"]})
        km_o, km_m, km_a = datos["oficial"]["km"], datos["motor"]["km"], datos["azar"]["km"]
        ctx.update({
            "seccion": "demo",
            "millones": {"oficial": round(km_o / 1e6, 2), "motor": round(km_m / 1e6, 2), "azar": round(km_a / 1e6, 2)},
            "motor_vs_azar": round(100 * (km_a - km_m) / km_a),
            "oficial_vs_motor": round(100 * (km_m - km_o) / km_m),
            "datos": datos,
            "gira_oficial": maximo(datos["oficial"]["equipos"], "visita"),
            "casa_oficial": maximo(datos["oficial"]["equipos"], "casa"),
            "gira_motor": maximo(datos["motor"]["equipos"], "visita"),
            "casa_motor": maximo(datos["motor"]["equipos"], "casa"),
            "generaciones": len(datos["motor"]["generaciones"]),
            "por_equipo": filas,
            "repeticion_datos": {
                "estadios": [{k: e[k] for k in ("codigo", "equipo", "lat", "lon")} for e in estadios()],
                "oficial": datos["oficial"], "motor": datos["motor"], "azar": datos["azar"],
                "textos": textos_js(),
            },
        })
        return ctx
