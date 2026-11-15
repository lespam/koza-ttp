"""Datos para el calendario dinámico (static/js/calendario.js).

Lo usan la página de un calendario guardado y el resultado de la demo.
"""
from django.utils.translation import gettext as _


def textos():
    return {
        "anterior": _("Mes anterior"),
        "siguiente": _("Mes siguiente"),
        "mes": _("Mes"),
        "equipo": _("Ver un equipo"),
        "todos": _("Todos los equipos"),
        "casa": _("En casa"),
        "visita": _("De visita"),
        "contra": _("contra {rival}"),
        "en": _("en {rival}"),
        "juego": _("{casa} recibe a {visita}"),
        "resumen": _("{n} juegos en {mes}."),
        "resumen_equipo": _("{equipo}: {n} juegos en {mes}, {casa} en casa y {visita} de visita."),
        "leyenda": _("Primero va el equipo que juega en casa."),
        "leyenda_equipo": _("Cada juego dice si el equipo juega en casa o de visita."),
        "sin_juegos": _("No hay juegos este mes."),
    }


def datos(juegos, equipos):
    """juegos: [(fecha, código en casa, código de visita)]; equipos: {código: nombre}."""
    return {
        "juegos": [[f.strftime("%Y-%m-%d"), h, v] for f, h, v in sorted(juegos)],
        "equipos": dict(equipos),
        "textos": textos(),
    }
