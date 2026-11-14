"""Demo corta: 3 pasos, todo ya elegido.

1. Equipos: 10 equipos de las Grandes Ligas ya marcados (máximo 10). El nombre es opcional.
2. Configuración: el torneo y el algoritmo, con valores ya puestos.
3. Resultado: el calendario que arma el algoritmo más nuevo.

La persona puede dar "Siguiente" tres veces sin cambiar nada. Lo que elige se
guarda solo en su sesión: la demo no escribe en la base de datos.
"""
import csv
from functools import lru_cache
from pathlib import Path

from django import forms
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _
from django.views import View

from programa_genetico.demo_turnos import (CONFIG_CAMPOS, MAX_EQUIPOS, MIN_EQUIPOS,
                                           config_desde_dict, correr_demo)

from .guia import Accesible

ARCHIVO_EQUIPOS = Path(settings.BASE_DIR) / "static" / "csv" / "teams.csv"
# Diez equipos repartidos por todo el país: así el viaje importa
PRESELECCION = ["SEA", "SFN", "LAN", "ARI", "TEX", "CHN", "ATL", "MIA", "NYA", "BOS"]
NOMBRE_POR_DEFECTO = _("Mi torneo de prueba")


@lru_cache(maxsize=1)
def equipos_mlb():
    """{código: (nombre, ciudad del estadio, lat, lon)} de los 30 equipos, en orden alfabético."""
    with open(ARCHIVO_EQUIPOS, encoding="utf-8") as archivo:
        filas = list(csv.DictReader(archivo))
    filas.sort(key=lambda f: f["Team Name"])
    return {f["Team Abbreviation"]: (f["Team Name"], f["Arena Location"], float(f["Lat"]), float(f["Lon"]))
            for f in filas}


def opciones_de_equipos():
    return [(codigo, f"{nombre} ({lugar})") for codigo, (nombre, lugar, _la, _lo) in equipos_mlb().items()]


PASOS = [
    ("equipos", _("Equipos")),
    ("configuracion", _("Configuración")),
    ("resultado", _("Resultado")),
]


def estado(request):
    return request.session.get("demo", {})


def guardar(request, **datos):
    sesion = estado(request)
    sesion.update(datos)
    request.session["demo"] = sesion


def pasos(actual):
    orden = [clave for clave, _n in PASOS]
    return [{"numero": i, "nombre": nombre, "actual": clave == actual,
             "hecho": orden.index(clave) < orden.index(actual),
             "url": reverse(f"tesis:demo_{clave}" if clave != "equipos" else "tesis:dashboard")}
            for i, (clave, nombre) in enumerate(PASOS, start=1)]


# --- Formularios -------------------------------------------------------------------

class EquiposDemoForm(Accesible, forms.Form):
    nombre = forms.CharField(label=_("Nombre del torneo"), required=False, max_length=80,
                             help_text=_("Opcional. Si lo dejas así, se usa este nombre."))
    equipos = forms.MultipleChoiceField(
        label=_("Equipos del torneo"), widget=forms.CheckboxSelectMultiple, choices=lambda: opciones_de_equipos(),
        help_text=_("Ya marcamos 10. Puedes cambiarlos: de 3 a 10 equipos."))

    def clean_equipos(self):
        equipos = self.cleaned_data["equipos"]
        if len(equipos) < MIN_EQUIPOS:
            raise forms.ValidationError(gettext("Elige al menos %(n)d equipos.") % {"n": MIN_EQUIPOS})
        if len(equipos) > MAX_EQUIPOS:
            raise forms.ValidationError(gettext("Elige como máximo %(n)d equipos.") % {"n": MAX_EQUIPOS})
        return equipos


def campo_de_formulario(campo):
    if campo["tipo"] == "int":
        return forms.IntegerField(label=campo["etiqueta"], help_text=campo["ayuda"],
                                  min_value=campo["minimo"], max_value=campo["maximo"])
    return forms.ChoiceField(label=campo["etiqueta"], help_text=campo["ayuda"],
                             choices=campo["opciones"], widget=forms.RadioSelect)


GRUPO_DE = {campo["clave"]: campo["grupo"] for campo in CONFIG_CAMPOS}


class ConfiguracionDemoBase(Accesible, forms.Form):
    def grupo(self, nombre):
        return [self[clave] for clave in self.fields if GRUPO_DE.get(clave) == nombre]

    def campos_del_torneo(self):
        return self.grupo("torneo")

    def campos_del_algoritmo(self):
        return self.grupo("algoritmo")


# Se arma con CONFIG_CAMPOS del algoritmo: cada campo trae su valor ya elegido
ConfiguracionDemoForm = type("ConfiguracionDemoForm", (ConfiguracionDemoBase,),
                             {campo["clave"]: campo_de_formulario(campo) for campo in CONFIG_CAMPOS})


# --- Vistas ------------------------------------------------------------------------

class DemoEquiposView(View):
    """Paso 1. Los enlaces viejos (/demo/?configuracion=…) van al tablero de la tesis."""

    def get(self, request):
        if request.GET.get("ejecutar") or request.GET.get("configuracion"):
            return redirect(f"{reverse('tesis:dashboard_tesis')}?{request.GET.urlencode()}")
        datos = estado(request)
        form = EquiposDemoForm(initial={"nombre": datos.get("nombre") or NOMBRE_POR_DEFECTO,
                                        "equipos": datos.get("equipos") or PRESELECCION})
        return self.mostrar(form)

    def post(self, request):
        form = EquiposDemoForm(request.POST)
        if not form.is_valid():
            return self.mostrar(form)
        guardar(request, nombre=form.cleaned_data["nombre"].strip(), equipos=form.cleaned_data["equipos"])
        return redirect("tesis:demo_configuracion")

    def mostrar(self, form):
        return render(self.request, "tesis/demo/equipos.html", {
            "seccion": "demo", "pasos": pasos("equipos"), "numero": 1, "total": len(PASOS),
            "form": form, "maximo": MAX_EQUIPOS})


class DemoConfiguracionView(View):
    def get(self, request):
        datos = estado(request)
        if not datos.get("equipos"):
            return redirect("tesis:dashboard")
        valores = vars(config_desde_dict(datos.get("config")))
        return self.mostrar(ConfiguracionDemoForm(initial=valores))

    def post(self, request):
        if not estado(request).get("equipos"):
            return redirect("tesis:dashboard")
        form = ConfiguracionDemoForm(request.POST)
        if not form.is_valid():
            return self.mostrar(form)
        guardar(request, config=dict(form.cleaned_data))
        return redirect("tesis:demo_resultado")

    def mostrar(self, form):
        return render(self.request, "tesis/demo/configuracion.html", {
            "seccion": "demo", "pasos": pasos("configuracion"), "numero": 2, "total": len(PASOS),
            "form": form, "equipos": nombres(estado(self.request)["equipos"])})


def nombres(codigos):
    tabla = equipos_mlb()
    return [tabla[c][0] for c in codigos if c in tabla]


class DemoResultadoView(View):
    def get(self, request):
        datos = estado(request)
        codigos = [c for c in datos.get("equipos", []) if c in equipos_mlb()]
        if not MIN_EQUIPOS <= len(codigos) <= MAX_EQUIPOS:
            return redirect("tesis:dashboard")
        tabla = equipos_mlb()
        config = config_desde_dict(datos.get("config"))
        resultado = correr_demo({c: (tabla[c][2], tabla[c][3]) for c in codigos}, config)
        nombre_de = {c: tabla[c][0] for c in codigos}
        juegos = [{"fecha": fecha, "local": nombre_de[local], "visita": nombre_de[visita]}
                  for fecha, local, visita in resultado.juegos]
        return render(request, "tesis/demo/resultado.html", {
            "seccion": "demo", "pasos": pasos("resultado"), "numero": 3, "total": len(PASOS),
            "nombre": datos.get("nombre") or NOMBRE_POR_DEFECTO,
            "equipos": [nombre_de[c] for c in codigos],
            "config": config, "regla": etiqueta_de_regla(config.regla),
            "resultado": resultado, "mejora": round(resultado.mejora * 100, 1),
            "km_azar": round(resultado.km_azar), "km_final": round(resultado.km_final),
            "juegos": juegos, "total_juegos": len(juegos), "primeros": juegos[:20],
            "curva": curva(resultado.historial),
        })


def curva(historial, ancho=600, alto=200, margen=8):
    """Puntos de una línea SVG con los kilómetros de cada paso (sin JavaScript)."""
    if len(historial) < 2:
        return None
    pasos_ = [p for p, _r, _km in historial]
    kms = [km for _p, _r, km in historial]
    x0, x1, y0, y1 = min(pasos_), max(pasos_), min(kms), max(kms)
    rango_x, rango_y = (x1 - x0) or 1, (y1 - y0) or 1
    puntos = " ".join(
        f"{margen + (p - x0) / rango_x * (ancho - 2 * margen):.1f},"
        f"{margen + (y1 - km) / rango_y * (alto - 2 * margen):.1f}"
        for p, km in zip(pasos_, kms))
    return {"puntos": puntos, "ancho": ancho, "alto": alto,
            "km_max": round(y1), "km_min": round(y0), "pasos": x1}


def etiqueta_de_regla(valor):
    for campo in CONFIG_CAMPOS:
        if campo["clave"] == "regla":
            return dict(campo["opciones"]).get(valor, "")
    return ""
