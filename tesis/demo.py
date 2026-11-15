"""Demo corta: 3 pasos, todo ya elegido.

1. Torneo: un torneo ya configurado (Grandes Ligas por omisión). El nombre es opcional.
2. Equipos y reglas: los equipos del torneo ya marcados (máximo 10) y la
   configuración del torneo y del algoritmo, con valores ya puestos.
3. Resultado: el calendario que arma el algoritmo más nuevo.

La persona puede dar "Siguiente" tres veces sin cambiar nada. Lo que elige se
guarda solo en su sesión: la demo no escribe en la base de datos.
"""
from django import forms
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext, gettext_lazy as _
from django.views import View

from programa_genetico.demo_turnos import (CONFIG_CAMPOS, MAX_EQUIPOS, MIN_EQUIPOS,
                                           config_desde_dict, correr_demo)

from .calendario_dinamico import datos as datos_del_calendario
from .guia import Accesible
from .mapa_torneo import datos as datos_del_mapa
from .torneos import PRESELECCION_MLB, TORNEO_POR_DEFECTO, TORNEOS, equipos_de, torneo

PRESELECCION = PRESELECCION_MLB  # nombre que usaban las pruebas
NOMBRE_POR_DEFECTO = _("Mi torneo de prueba")


def equipos_mlb():
    return equipos_de("mlb")


def opciones_de_equipos(clave):
    return [(codigo, f"{nombre} ({lugar})") for codigo, (nombre, lugar, _la, _lo) in equipos_de(clave).items()]


PASOS = [
    ("equipos", _("Torneo")),
    ("configuracion", _("Equipos y reglas")),
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

class TorneoDemoForm(Accesible, forms.Form):
    torneo = forms.ChoiceField(
        label=_("Torneo"), widget=forms.RadioSelect,
        choices=lambda: [(t["clave"], t["nombre"]) for t in TORNEOS],
        help_text=_("Cada torneo trae sus equipos y reglas ya elegidos. En el paso 2 puedes cambiarlos."))
    nombre = forms.CharField(label=_("Nombre del torneo"), required=False, max_length=80,
                             help_text=_("Opcional. Si lo dejas así, se usa este nombre."))


def validar_equipos(equipos):
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

    def clean_equipos(self):
        return validar_equipos(self.cleaned_data["equipos"])


def formulario_de_equipos_y_reglas(clave):
    """El formulario del paso 2 para un torneo: sus equipos y la configuración."""
    campos = {"equipos": forms.MultipleChoiceField(
        label=_("Equipos del torneo"), widget=forms.CheckboxSelectMultiple,
        choices=opciones_de_equipos(clave),
        help_text=_("Ya están marcados. Puedes quitar o agregar: de 3 a 10 equipos."))}
    campos.update({campo["clave"]: campo_de_formulario(campo) for campo in CONFIG_CAMPOS})
    return type("EquiposYReglasForm", (ConfiguracionDemoBase,), campos)


# Sin equipos: lo usan las pruebas de los campos del algoritmo
ConfiguracionDemoForm = type("ConfiguracionDemoForm", (ConfiguracionDemoBase,),
                             {campo["clave"]: campo_de_formulario(campo) for campo in CONFIG_CAMPOS})


# --- Vistas ------------------------------------------------------------------------

class DemoEquiposView(View):
    """Paso 1: elegir un torneo. Los enlaces viejos (/demo/?configuracion=…) van al tablero de la tesis."""

    def get(self, request):
        if request.GET.get("ejecutar") or request.GET.get("configuracion"):
            return redirect(f"{reverse('tesis:dashboard_tesis')}?{request.GET.urlencode()}")
        datos = estado(request)
        form = TorneoDemoForm(initial={"torneo": torneo(datos.get("torneo"))["clave"],
                                       "nombre": datos.get("nombre") or NOMBRE_POR_DEFECTO})
        return self.mostrar(form)

    def post(self, request):
        form = TorneoDemoForm(request.POST)
        if not form.is_valid():
            return self.mostrar(form)
        clave = form.cleaned_data["torneo"]
        datos = {"torneo": clave, "nombre": form.cleaned_data["nombre"].strip()}
        if clave != estado(request).get("torneo") or not estado(request).get("equipos"):
            # Otro torneo: sus equipos y reglas vuelven a los valores ya elegidos
            elegido = torneo(clave)
            datos.update(equipos=list(elegido["marcados"]), config=dict(elegido["config"]))
        guardar(request, **datos)
        return redirect("tesis:demo_configuracion")

    def mostrar(self, form):
        return render(self.request, "tesis/demo/equipos.html", {
            "seccion": "demo", "pasos": pasos("equipos"), "numero": 1, "total": len(PASOS),
            "form": form, "torneos": TORNEOS, "maximo": MAX_EQUIPOS})


class DemoConfiguracionView(View):
    """Paso 2: los equipos del torneo y las reglas, ya elegidos."""

    def get(self, request):
        datos = estado(request)
        if not datos.get("equipos"):
            return redirect("tesis:dashboard")
        valores = vars(config_desde_dict(datos.get("config")))
        Form = formulario_de_equipos_y_reglas(datos.get("torneo", TORNEO_POR_DEFECTO))
        return self.mostrar(Form(initial={**valores, "equipos": datos["equipos"]}))

    def post(self, request):
        datos = estado(request)
        if not datos.get("equipos"):
            return redirect("tesis:dashboard")
        form = formulario_de_equipos_y_reglas(datos.get("torneo", TORNEO_POR_DEFECTO))(request.POST)
        if not form.is_valid():
            return self.mostrar(form)
        config = {k: v for k, v in form.cleaned_data.items() if k != "equipos"}
        guardar(request, equipos=form.cleaned_data["equipos"], config=config)
        return redirect("tesis:demo_resultado")

    def mostrar(self, form):
        elegido = torneo(estado(self.request).get("torneo"))
        return render(self.request, "tesis/demo/configuracion.html", {
            "seccion": "demo", "pasos": pasos("configuracion"), "numero": 2, "total": len(PASOS),
            "form": form, "torneo": elegido})


def nombres(clave, codigos):
    tabla = equipos_de(clave)
    return [tabla[c][0] for c in codigos if c in tabla]


class DemoResultadoView(View):
    def get(self, request):
        datos = estado(request)
        tabla = equipos_de(datos.get("torneo"))
        codigos = [c for c in datos.get("equipos", []) if c in tabla]
        if not MIN_EQUIPOS <= len(codigos) <= MAX_EQUIPOS:
            return redirect("tesis:dashboard")
        config = config_desde_dict(datos.get("config"))
        resultado = correr_demo({c: (tabla[c][2], tabla[c][3]) for c in codigos}, config)
        nombre_de = {c: tabla[c][0] for c in codigos}
        juegos = [{"fecha": fecha, "local": nombre_de[local], "visita": nombre_de[visita]}
                  for fecha, local, visita in resultado.juegos]
        return render(request, "tesis/demo/resultado.html", {
            "seccion": "demo", "pasos": pasos("resultado"), "numero": 3, "total": len(PASOS),
            "nombre": datos.get("nombre") or NOMBRE_POR_DEFECTO, "torneo": torneo(datos.get("torneo")),
            "equipos": [nombre_de[c] for c in codigos],
            "config": config, "regla": etiqueta_de_regla(config.regla),
            "resultado": resultado, "mejora": round(resultado.mejora * 100, 1),
            "km_azar": round(resultado.km_azar), "km_final": round(resultado.km_final),
            "juegos": juegos, "total_juegos": len(juegos), "primeros": juegos[:20],
            "curva": curva(resultado.historial),
            "calendario_datos": datos_del_calendario(resultado.juegos, nombre_de),
            "mapa_datos": datos_del_mapa(torneo(datos.get("torneo"))["clave"], {c: tabla[c] for c in codigos}),
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
