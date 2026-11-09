"""Historia paso a paso: "Entender la idea en 2 minutos".

Cuenta el problema (mapa de estadios), la idea de la tesis (árboles, cruce,
mutación, generaciones) y el resultado. El texto vive en la plantilla para que
se traduzca; historia.js dibuja las escenas y usa los textos de `textos_js`.
"""
import csv
from pathlib import Path

from django.conf import settings
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from project.estado_motor import MOTOR

ARCHIVO_EQUIPOS = Path(settings.BASE_DIR) / "static" / "csv" / "teams.csv"


def estadios():
    """Los 30 estadios con sus coordenadas, del mismo CSV con que se cargó la base."""
    with open(ARCHIVO_EQUIPOS, encoding="utf-8") as f:
        return [
            {"codigo": fila["Team Abbreviation"], "equipo": fila["Team Name"],
             "estadio": fila["Arena Name"], "ciudad": fila["Arena Location"],
             "lat": float(fila["Lat"]), "lon": float(fila["Lon"])}
            for fila in csv.DictReader(f)
        ]


def textos_js():
    """Textos que historia.js escribe dentro de los dibujos."""
    return {
        "mapa": _("Mapa de los 30 estadios de las Grandes Ligas"),
        "gira": _("Gira de ejemplo de {equipo}: 12 visitas en orden al azar."),
        "elegiste": _("Elegiste {equipo}. Sigue al paso 2 para ver sus viajes."),
        "km": _("km"),
        "combinar": _("combinar"),
        "intercambiar": _("intercambiar"),
        "invertir": _("invertir localía"),
        "casa": _("casa"),
        "visita": _("visita"),
        "padre_a": _("Padre A"),
        "padre_b": _("Padre B"),
        "hijo": _("Hijo"),
        "arbol": _("Árbol de ejemplo: combinar, con dos ramas: intercambiar SEA–NYA con BOS–TEX, e invertir localía de LAN–CHN en casa."),
        "cruce": _("Cruce: el padre A da su rama izquierda y el padre B da su rama izquierda; el hijo combina las dos."),
        "mutacion": _("Mutación: en el árbol, la hoja SEA–NYA cambia a SEA–OAK."),
        "ver_otra_vez": _("Ver otra vez"),
        "generacion": _("Generación"),
        "eje_viaje": _("Viaje (azar = 100)"),
        "azar": _("Azar"),
        "poblacion": _("Población (48 árboles)"),
        "mas_color": _("Más color = menos viaje"),
        "motor_tesis": _("Motor de la tesis"),
        "motor_bloques": _("Motor por bloques"),
        "fin_tesis": str(MOTOR["tesis"]["frente_al_azar"]),
        "fin_bloques": str(MOTOR["mejorado"]["frente_al_azar"]),
        "progreso": _("{motor} · generación {g} de {total}"),
        "termino": _("{motor} · terminó: {resultado}."),
        "curva": _("{motor}: empieza en {inicio} y termina en {fin} (azar = 100). Resultado: {resultado}."),
        "barras": _("Distancia frente al azar: motor de la tesis {tesis}, elegir al azar 100, motor por bloques {bloques}."),
        "barra_tesis": _("Motor de la tesis (2026)"),
        "barra_azar": _("Elegir calendarios al azar"),
        "barra_bloques": _("Motor por bloques (preliminar)"),
        "teclado": _("También puedes usar las flechas del teclado."),
    }


class HistoriaView(TemplateView):
    template_name = "tesis/historia.html"

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto.update({
            "seccion": "historia",
            "estadios": estadios(),
            "historia_datos": {
                "estadios": estadios(),
                "textos": textos_js(),
                "indice": {
                    "tesis": MOTOR["tesis"]["distancia_vs_azar"],
                    "bloques": MOTOR["mejorado"]["distancia_vs_azar"],
                },
            },
        })
        return contexto
