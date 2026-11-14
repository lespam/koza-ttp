"""Datos de la página "Investigación actual".

Cifras de las pruebas del PR #38 (python -m programa_genetico.comparar_turnos,
comparar_turnos_pg y comparar_turnos_temperatura). Viaje total de los 30 equipos
en millones de km, medido igual que el calendario oficial 2023.
"""
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

KM_OFICIAL = 1.74

BARRAS = [
    {"nombre": _("Bloques, con reglas"), "km": 2.19, "oficial": False},
    {"nombre": _("Bloques mezclados, con reglas"), "km": 2.00, "oficial": False},
    {"nombre": _("Calendario oficial 2023"), "km": KM_OFICIAL, "oficial": True},
    {"nombre": _("Turnos + movimientos al azar"), "km": 1.70, "oficial": False},
    {"nombre": _("Turnos + PG (solo mejoras)"), "km": 1.696, "oficial": False},
    {"nombre": _("Turnos + recocido a mano"), "km": 1.580, "oficial": False},
    {"nombre": _("Turnos + PG que aprende la temperatura"), "km": 1.575, "oficial": False},
]

TEXTOS = {
    "pausar": _("Pausar"),
    "reproducir": _("Reproducir"),
    "millones_km": _("millones de km"),
    "antes": _("Antes: todos juegan 3 días en cada turno"),
    "ahora": _("Ahora: series de 2, 3 y 4 juegos, con descansos"),
    "turno": _("Turno"),
    "entre_semana": _("entre semana"),
    "fin_de_semana": _("fin de semana"),
    "turno_a": _("Turno A"),
    "turno_b": _("Turno B"),
    "paso_inicio": _("1. Elegimos un equipo y dos turnos"),
    "paso_cadena": _("2. Seguimos la cadena: A, B, A, B…"),
    "paso_cambio": _("3. Las series de la cadena cambian de turno"),
    "costo": _("Costo del calendario"),
    "mejor": _("mejor"),
    "valle_local": _("primer valle"),
    "valle_profundo": _("valle más profundo"),
    "avance": _("Avance de la corrida"),
    "inicio": _("inicio"),
    "fin": _("fin"),
    "a_mano": _("a mano"),
    "pg_pocos": _("PG, 5 %"),
    "pg_muchos": _("PG, 50 %"),
}


class Investigacion(TemplateView):
    template_name = "documentacion/investigacion.html"
    extra_context = {"seccion": "avances"}

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto["datos_investigacion"] = {"barras": BARRAS, "oficial": KM_OFICIAL, "textos": TEXTOS}
        return contexto
