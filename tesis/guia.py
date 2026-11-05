"""Flujo guiado de 5 pasos: del registro de equipos al calendario.

Usa los mismos modelos que las páginas de administración, pero muestra un paso a la
vez, con su estado y con lenguaje claro. Lo que la persona crea se recuerda en la
sesión, así cada visitante sigue su propio recorrido aunque la base sea compartida.
"""
from django import forms
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View

from .models import Calendario, Configuracion, Equipo, Juego, Liga, Torneo

MINIMO_DE_EQUIPOS = 2


# --- Formularios -------------------------------------------------------------------

class Accesible:
    """Une cada campo con su ayuda y su error (aria-describedby) y marca los
    campos con error (aria-invalid), para que un lector de pantalla los lea."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            ids = []
            if campo.help_text:
                ids.append(f"id_{nombre}-ayuda")
            if self.is_bound and nombre in self.errors:
                ids.append(f"id_{nombre}-error")
                campo.widget.attrs["aria-invalid"] = "true"
            if ids:
                campo.widget.attrs["aria-describedby"] = " ".join(ids)


class EquipoGuiaForm(Accesible, forms.ModelForm):
    class Meta:
        model = Equipo
        fields = ["team_abbreviation", "team_name", "city", "lat", "lon"]
        labels = {
            "team_abbreviation": _("Abreviatura (por ejemplo, SEA)"),
            "team_name": _("Nombre del equipo"),
            "city": _("Ciudad"),
            "lat": _("Latitud del estadio"),
            "lon": _("Longitud del estadio"),
        }
        help_texts = {
            "lat": _("En grados decimales. Ejemplo: 47.59"),
            "lon": _("En grados decimales. Ejemplo: -122.33"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["team_abbreviation"].required = True


class LigaGuiaForm(Accesible, forms.ModelForm):
    class Meta:
        model = Liga
        fields = ["nombre", "equipos"]
        labels = {"nombre": _("Nombre de la liga"), "equipos": _("Equipos de la liga")}
        widgets = {"equipos": forms.CheckboxSelectMultiple}

    def clean_equipos(self):
        equipos = self.cleaned_data["equipos"]
        if len(equipos) < MINIMO_DE_EQUIPOS:
            raise forms.ValidationError(_("Elige al menos 2 equipos."))
        return equipos


class TorneoGuiaForm(Accesible, forms.ModelForm):
    class Meta:
        model = Torneo
        fields = ["nombre", "fecha_inicio", "fecha_fin", "numero_de_juegos", "numero_de_series"]
        labels = {
            "nombre": _("Nombre del torneo"),
            "fecha_inicio": _("Primer día"),
            "fecha_fin": _("Último día"),
            "numero_de_juegos": _("Juegos por serie"),
            "numero_de_series": _("Series por equipo"),
        }
        widgets = {
            "fecha_inicio": forms.DateInput(attrs={"type": "date"}),
            "fecha_fin": forms.DateInput(attrs={"type": "date"}),
        }

    def clean(self):
        datos = super().clean()
        inicio, fin = datos.get("fecha_inicio"), datos.get("fecha_fin")
        if inicio and fin and fin < inicio:
            self.add_error("fecha_fin", _("El último día debe ser igual o posterior al primero."))
        for campo in ("numero_de_juegos", "numero_de_series"):
            if datos.get(campo) is not None and datos[campo] < 1:
                self.add_error(campo, _("Debe ser 1 o más."))
        return datos


class ConfiguracionGuiaForm(Accesible, forms.ModelForm):
    class Meta:
        model = Configuracion
        fields = ["nombre", "poblacion", "generaciones", "probabilidad_de_cruce",
                  "probabilidad_de_reproduccion"]
        labels = {
            "nombre": _("Nombre de la configuración"),
            "poblacion": _("Tamaño de la población"),
            "generaciones": _("Número de generaciones"),
            "probabilidad_de_cruce": _("Probabilidad de cruce (0 a 1)"),
            "probabilidad_de_reproduccion": _("Probabilidad de mutación (0 a 1)"),
        }

    def clean(self):
        datos = super().clean()
        for campo in ("probabilidad_de_cruce", "probabilidad_de_reproduccion"):
            if datos.get(campo) is not None and not 0 <= datos[campo] <= 1:
                self.add_error(campo, _("Debe estar entre 0 y 1."))
        for campo in ("poblacion", "generaciones"):
            if datos.get(campo) is not None and datos[campo] < 1:
                self.add_error(campo, _("Debe ser 1 o más."))
        return datos


# --- Estado del recorrido ----------------------------------------------------------

PASOS = [
    ("equipos", _("Equipos")),
    ("liga", _("Liga")),
    ("torneo", _("Torneo")),
    ("configuracion", _("Configuración")),
    ("calendario", _("Calendario")),
]


def recorrido(request):
    """Los objetos que esta persona creó en la guía (o None)."""
    sesion = request.session.get("guia", {})

    def buscar(modelo, clave):
        pk = sesion.get(clave)
        return modelo.objects.filter(pk=pk).first() if pk else None

    return {
        "liga": buscar(Liga, "liga"),
        "torneo": buscar(Torneo, "torneo"),
        "configuracion": buscar(Configuracion, "configuracion"),
    }


def recordar(request, **objetos):
    sesion = request.session.get("guia", {})
    sesion.update({clave: objeto.pk for clave, objeto in objetos.items()})
    request.session["guia"] = sesion


def pasos_con_estado(request, actual):
    datos = recorrido(request)
    configuracion = datos["configuracion"]
    hecho = {
        "equipos": Equipo.objects.count() >= MINIMO_DE_EQUIPOS,
        "liga": datos["liga"] is not None,
        "torneo": datos["torneo"] is not None,
        "configuracion": configuracion is not None,
        "calendario": bool(configuracion and configuracion.calendario
                           and Juego.objects.filter(serie__calendario=configuracion.calendario).exists()),
    }
    return [
        {"numero": i, "clave": clave, "nombre": nombre, "hecho": hecho[clave],
         "actual": clave == actual, "url": reverse("tesis:guia_paso", args=[clave])}
        for i, (clave, nombre) in enumerate(PASOS, start=1)
    ], hecho, datos


def primer_paso_pendiente(hecho):
    for clave, _nombre in PASOS:
        if not hecho[clave]:
            return clave
    return PASOS[-1][0]


# --- Vistas ------------------------------------------------------------------------

class GuiaInicioView(View):
    def get(self, request):
        pasos, hecho, _datos = pasos_con_estado(request, actual=None)
        return render(request, "tesis/guia/inicio.html", {
            "seccion": "guia", "pasos": pasos,
            "siguiente": reverse("tesis:guia_paso", args=[primer_paso_pendiente(hecho)]),
        })


class GuiaPasoView(View):
    """Un paso de la guía. Si falta un paso anterior, manda a ese paso."""

    requisitos = {"liga": "equipos", "torneo": "liga", "configuracion": "torneo",
                  "calendario": "configuracion"}

    def dispatch(self, request, paso):
        if paso not in dict(PASOS):
            return redirect("tesis:guia")
        self.paso = paso
        self.pasos, self.hecho, self.datos = pasos_con_estado(request, actual=paso)
        requisito = self.requisitos.get(paso)
        if requisito and not self.hecho[requisito]:
            messages.info(request, _("Primero completa este paso."))
            return redirect("tesis:guia_paso", primer_paso_pendiente(self.hecho))
        return super().dispatch(request, paso)

    # Cada paso: (formulario, cómo guardarlo)
    def formulario(self, data=None):
        if self.paso == "equipos":
            return EquipoGuiaForm(data)
        if self.paso == "liga":
            return LigaGuiaForm(data, instance=self.datos["liga"])
        if self.paso == "torneo":
            return TorneoGuiaForm(data, instance=self.datos["torneo"])
        if self.paso == "configuracion":
            return ConfiguracionGuiaForm(data, instance=self.datos["configuracion"])
        return None

    def get(self, request, paso):
        return self.mostrar(self.formulario())

    def post(self, request, paso):
        if self.paso == "calendario":
            return self.generar_juegos()
        form = self.formulario(request.POST)
        if not form.is_valid():
            return self.mostrar(form)
        objeto = form.save(commit=False)
        if self.paso == "equipos":
            objeto.save()
            messages.success(request, _("Equipo agregado."))
            return redirect("tesis:guia_paso", "equipos")
        if self.paso == "liga":
            objeto.save()
            form.save_m2m()
            recordar(request, liga=objeto)
        elif self.paso == "torneo":
            objeto.metodo = objeto.metodo or "haversine"
            objeto.unidad = objeto.unidad or "km"
            objeto.save()
            objeto.liga.set([self.datos["liga"]])
            recordar(request, torneo=objeto)
        elif self.paso == "configuracion":
            torneo = self.datos["torneo"]
            if objeto.calendario_id is None or objeto.calendario.torneo_id != torneo.pk:
                objeto.calendario = Calendario.objects.create(torneo=torneo)
            objeto.save()
            recordar(request, configuracion=objeto)
        siguiente = PASOS[[c for c, _n in PASOS].index(self.paso) + 1][0]
        return redirect("tesis:guia_paso", siguiente)

    def generar_juegos(self):
        configuracion = self.datos["configuracion"]
        calendario = configuracion.calendario
        # Volver a generar reemplaza los juegos anteriores de este calendario
        calendario.series.all().delete()
        configuracion.generar_calendario_aleatorio()
        messages.success(self.request, _("Juegos generados."))
        return redirect("tesis:guia_paso", "calendario")

    def mostrar(self, form):
        contexto = {"seccion": "guia", "pasos": self.pasos, "paso": self.paso,
                    "numero": [c for c, _n in PASOS].index(self.paso) + 1,
                    "total": len(PASOS), "form": form, **self.datos}
        if self.paso == "equipos":
            contexto["equipos"] = Equipo.objects.order_by("-pk")[:10]
            contexto["total_equipos"] = Equipo.objects.count()
            contexto["puede_seguir"] = self.hecho["equipos"]
        if self.paso == "calendario":
            calendario = self.datos["configuracion"].calendario
            contexto["calendario"] = calendario
            contexto["juegos"] = (Juego.objects.filter(serie__calendario=calendario)
                                  .select_related("equipo_en_casa", "equipo_visita")
                                  .order_by("fecha_de_inicio")[:50])
            contexto["total_juegos"] = Juego.objects.filter(serie__calendario=calendario).count()
        return render(self.request, f"tesis/guia/{self.paso}.html", contexto)
