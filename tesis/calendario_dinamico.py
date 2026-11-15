"""Datos para el calendario dinámico (static/js/calendario.js).

Lo usan la página de un calendario guardado y el resultado de la demo.
"""
from django.utils.translation import gettext as _


def textos():
    return {
        "vista": _("Ver el calendario por"),
        "vista_semana": _("Semana"),
        "vista_mes": _("Mes"),
        "vista_anio": _("Año"),
        "anterior_semana": _("Semana anterior"),
        "siguiente_semana": _("Semana siguiente"),
        "anterior_mes": _("Mes anterior"),
        "siguiente_mes": _("Mes siguiente"),
        "anterior_anio": _("Año anterior"),
        "siguiente_anio": _("Año siguiente"),
        "ir_a": _("Ir al mes"),
        "equipo": _("Ver un equipo"),
        "todos": _("Todos los equipos"),
        "casa": _("En casa"),
        "visita": _("De visita"),
        "contra": _("contra {rival}"),
        "en": _("en {rival}"),
        "juego": _("{casa} recibe a {visita}"),
        "resumen": _("{n} juegos en {periodo}."),
        "resumen_equipo": _("{equipo}: {n} juegos en {periodo}, {casa} en casa y {visita} de visita."),
        "titulo_semana": _("Semana del {inicio} al {fin}"),
        "esta_semana": _("esta semana"),
        "titulo_anio": _("Año {anio}"),
        "n_juegos": _("{n} juegos"),
        "descanso": _("Sin juegos"),
        "abrir_semana": _("Abrir esa semana"),
        "leyenda": _("Primero va el equipo que juega en casa."),
        "leyenda_equipo": _("Cada juego dice si el equipo juega en casa o de visita."),
        "leyenda_anio": _("Los días con número en un cuadro tienen juegos. Toca un día para ver su semana."),
        "leyenda_anio_equipo": _("Cuadro lleno: juega en casa. Cuadro con borde punteado: juega de visita. Toca un día para ver su semana."),
        "sin_juegos": _("No hay juegos en estas fechas."),
    }


def datos(juegos, equipos):
    """juegos: [(fecha, código en casa, código de visita)]; equipos: {código: nombre}."""
    return {
        "juegos": [[f.strftime("%Y-%m-%d"), h, v] for f, h, v in sorted(juegos)],
        "equipos": dict(equipos),
        "textos": textos(),
    }
