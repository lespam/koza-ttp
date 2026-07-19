import csv
import json
import os
import random
import datetime
from datetime import timezone
from typing import Any

import pygraphviz as pgv
from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.core import serializers
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils.safestring import mark_safe
from django.views import View, generic
from django.views.generic.edit import FormView

from .forms import CalendarioForm, ConfiguracionForm, LigaForm, ProgramaFacadeForm
from .models import Calendario, Condicion, Configuracion, Equipo, Juego, Liga, Serie, Torneo, User
from .services import run_genetic_algorithm_logic

# ==========================================
# VISTA PRINCIPAL (DASHBOARD INTEGRADO)
# ==========================================
class DashboardView(View):
    """
    Vista principal que integra la configuración por defecto y 
    la ejecución del algoritmo genético al presionar el botón en el dashboard.
    """
    def get(self, request, *args, **kwargs):
        # 1. Obtener la configuración por defecto (ID 5)
        config = get_object_or_404(Configuracion, pk=5)
        
        # Empezamos asumiendo que mostraremos el calendario base de la configuración
        calendario_actual = config.calendario
        
        # 2. Si el usuario presiona "Ejecutar Optimización" (?ejecutar=true)
        if request.GET.get('ejecutar') == 'true':
            # Llamamos al servicio (el cual ya lee el CSV, ejecuta el modelo y calcula métricas)
            resultado = run_genetic_algorithm_logic(config)
            
            # Si el servicio generó o actualizó el calendario, lo recuperamos del diccionario
            if 'calendario' in resultado:
                calendario_actual = resultado['calendario']
        else:
            resultado = {'svg_content': None, 'distancia': 0, 'diferencia': 0}
        
        # 3. Obtener los juegos del calendario (con las propiedades corregidas de tu BD)
        if calendario_actual:
            # Filtramos por la relación inversa correcta a través de las Series
            juegos = Juego.objects.filter(serie__calendario=calendario_actual).order_by('fecha_de_inicio')[:50]
        else:
            juegos = []

        context = {
            "configuracion": config,
            "calendario": calendario_actual, 
            "juegos": juegos,
            "svg_content": resultado.get('svg_content'),
            "distancia": resultado.get('distancia', 0),
            "diferencia": resultado.get('diferencia', 0)
        }
        
        return render(request, 'tesis/dashboard.html', context)

def my_view(request):
    ruta_svg = os.path.join(settings.BASE_DIR, 'media', 'svg', 'arbol.svg')
    try:
        with open(ruta_svg, "r", encoding="utf-8") as svg_file:
            svg_content = svg_file.read()
    except FileNotFoundError:
        svg_content = "<svg><text x='10' y='20' fill='red'>Archivo SVG no encontrado</text></svg>"

    context = {'svg_content': mark_safe(svg_content)}
    return render(request, 'tesis/svg_template.html', context)

# ==========================================
# EQUIPOS - CRUD
# ==========================================
class EquipoIndexView(generic.ListView):
    def get_queryset(self):
        return Equipo.objects.all()

class EquipoCreateView(SuccessMessageMixin, generic.CreateView):
    model = Equipo
    template_name_suffix = "_create_form"
    success_url = reverse_lazy("tesis:equipo_list")
    success_message = "Equipo creado con éxito"
    fields = "__all__"

class EquipoDetailView(generic.DetailView):
    model = Equipo
    template_name = "tesis/equipo_detail.html"
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["calcula"] = self.object.test_communication_equipo()
        return context

class EquipoUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Equipo
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_message = "Equipo actualizado con éxito"
    def get_success_url(self):
        return reverse_lazy("tesis:equipo_detail", kwargs={"pk": self.object.pk})

class EquipoDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Equipo
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:equipo_list")
    success_message = "Equipo %(nombre)s eliminado"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        nombre = self.object.team_name if self.object.team_name else ""
        return self.success_message % dict(cleaned_data, nombre=nombre)

# ==========================================
# LIGA - CRUD
# ==========================================
class LigaIndexView(generic.ListView):
    def get_queryset(self):
        return Liga.objects.order_by("id")

class LigaCreateView(SuccessMessageMixin, generic.CreateView):
    model = Liga
    fields = "__all__"
    template_name_suffix = "_create_form"
    success_url = reverse_lazy("tesis:liga_list")
    success_message = "Liga %(nombre)s creada con éxito"

class LigaDetailView(generic.DetailView):
    model = Liga
    template_name = "tesis/liga_detail.html"
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["calcula"] = self.object.test_communication_liga()
        return context

class LigaUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Liga
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_message = "Liga %(nombre)s actualizada con éxito"
    def get_success_url(self):
        return reverse_lazy("tesis:liga_detail", kwargs={"pk": self.object.pk})

class LigaDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Liga
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:liga_list")
    success_message = "Liga %(nombre)s eliminada"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, nombre=self.object.nombre)

class LigaFormView(SuccessMessageMixin, generic.FormView):
    template_name = "tesis/liga_form.html"
    form_class = LigaForm
    success_url = reverse_lazy("tesis:liga_list")
    success_message = "%(nombre)s creada con éxito"
    def form_valid(self, form):
        form.send_data()
        return super().form_valid(form)

# ==========================================
# TORNEO - CRUD
# ==========================================
class TorneoIndexView(generic.ListView):
    def get_queryset(self):
        return Torneo.objects.order_by("id")

class TorneoCreateView(SuccessMessageMixin, generic.CreateView):
    model = Torneo
    fields = "__all__"
    template_name_suffix = "_create_form"
    success_url = reverse_lazy("tesis:torneo_list")
    success_message = "Torneo %(nombre)s creada con éxito"

class TorneoDetailView(generic.DetailView):
    model = Torneo
    template_name = "tesis/torneo_detail.html"

class TorneoUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Torneo
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_message = "Torneo %(nombre)s actualizada con éxito"

class TorneoDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Torneo
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:torneo_list")
    success_message = "Torneo %(nombre)s eliminada"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, nombre=self.object.nombre)

# ==========================================
# CONFIGURACIÓN - CRUD
# ==========================================
class ConfiguracionIndexView(generic.ListView):
    def get_queryset(self):
        return Configuracion.objects.all()

class ConfiguracionCreateView(SuccessMessageMixin, generic.CreateView):
    model = Configuracion
    template_name_suffix = "_create_form"
    success_url = reverse_lazy("tesis:configuracion_list")
    form_class = ConfiguracionForm

    def get_initial(self):
        initial = super().get_initial()
        calendario_id = self.kwargs.get('pk')
        if calendario_id:
            initial['calendario'] = Calendario.objects.get(id=calendario_id)
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        calendario_id = self.kwargs.get('pk')
        if calendario_id:
            form.fields['calendario'].initial = calendario_id
        return form

    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        calendario_id = self.kwargs.get('pk')
        if calendario_id:
            return f"Configuración creada con éxito para el calendario {calendario_id}"
        return f"Configuración {self.object.id} creada con éxito"
            
    def form_valid(self, form):
        calendario_id = self.kwargs.get('pk')
        if calendario_id:
            calendario = get_object_or_404(Calendario, id=calendario_id)
            form.instance.calendario = calendario
        return super().form_valid(form)

class ConfiguracionDetailView(generic.DetailView):
    model = Configuracion

class ConfiguracionUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Configuracion
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_message = "Configuración %(nombre)s actualizada con éxito"

class ConfiguracionDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Configuracion
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:configuracion_list")
    success_message = "Configuración %(nombre)s eliminada"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, nombre=self.object.nombre)

class GenerarJuegosView(View):
    def get(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            configuracion = Configuracion.objects.get(pk=kwargs['pk'])
            if configuracion and configuracion.calendario:
                configuracion.generar_calendario_aleatorio()
                return HttpResponseRedirect(reverse("tesis:calendario_detail", args=(configuracion.calendario.id,)))
        return HttpResponseRedirect(reverse("tesis:configuracion_list"))

class GenerarNuevosJuegosView(View):
    def get(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            configuracion = Configuracion.objects.get(pk=kwargs['pk'])
            if configuracion and configuracion.calendario:
                nueva_configuracion, nuevo_calendario = configuracion.duplicar_calendario_configuracion_y_generar_nuevo_calendario()
                return HttpResponseRedirect(reverse("tesis:calendario_detail", args=(nuevo_calendario.id,)))
        return HttpResponseRedirect(reverse("tesis:configuracion_list"))

# ==========================================
# JUEGOS - CRUD
# ==========================================
class JuegoIndexView(generic.ListView):
    def get_queryset(self):
        return Juego.objects.all()

class JuegoCreateView(SuccessMessageMixin, generic.CreateView):
    model = Juego
    fields = "__all__"
    template_name_suffix = "_create_form"
    success_message = "Juego creado con éxito"
    
    def get_success_url(self):
        calendario_id = self.kwargs.get('pk')
        if calendario_id:
            return reverse_lazy("tesis:calendario_detail", kwargs={"pk": calendario_id})
        return reverse_lazy("tesis:juego_list")
        
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        calendario_id = self.kwargs.get('pk')
        if calendario_id:
            return f"Juego del calendario {calendario_id} creado con éxito"
        return "Juego creado con éxito"

    def get_initial(self):
        initial = super().get_initial()
        calendario_id = self.kwargs.get('pk')
        if calendario_id:
            initial['calendario'] = calendario_id    
        return initial

    def form_valid(self, form):
        calendario_id = self.kwargs.get('pk')
        if calendario_id:
            calendario = get_object_or_404(Calendario, id=calendario_id)
            form.instance.calendario = calendario
            form.instance.torneo = calendario.torneo
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        calendario_id = self.kwargs.get('pk')
        if calendario_id:
            calendario = Calendario.objects.get(id=calendario_id)
            context["calendario"] = calendario
            context["torneo"] = calendario.torneo
            context["equipos"] = calendario.torneo.obtener_equipos_del_torneo()
        return context

class JuegoDetailView(generic.DetailView):
    model = Juego
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["calcula"] = self.object.test_communication_juego()
        return context

class JuegoUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Juego
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_message = "Juego actualizado con éxito"
    def get_success_url(self):
        return reverse_lazy("tesis:juego_detail", kwargs={"pk": self.object.pk})

class JuegoDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Juego
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:juego_list")
    success_message = "Juego de la serie %(serie)s eliminado"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, serie=self.object.serie)

# ==========================================
# CALENDARIO - CRUD
# ==========================================
class CalendarioIndexView(generic.ListView):
    context_object_name = "calendario_list"
    def get_queryset(self):
        return Calendario.objects.all()

class CalendarioCreateView(SuccessMessageMixin, generic.CreateView):
    model = Calendario
    fields = "__all__"
    template_name_suffix = "_create_form"
    success_url = reverse_lazy("tesis:calendario_list")

    def get_initial(self):
        initial = super().get_initial()
        torneo_id = self.kwargs.get('pk')
        if torneo_id:
            initial['torneo'] = torneo_id
        return initial

    def get_form(self, form_class=CalendarioForm):
        form = super().get_form(form_class)
        torneo_id = self.kwargs.get('pk')
        if torneo_id:
            form.fields['torneo'].initial = torneo_id
        return form

    def form_valid(self, form):
        torneo_id = self.kwargs.get('id_torneo')
        if torneo_id:
            torneo = Torneo.objects.get(id=torneo_id)
            form.instance.torneo = torneo
        self.success_message = f"Calendario creado con éxito para el torneo {form.instance.torneo.nombre}"
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        torneo_id = self.kwargs.get('pk')
        if torneo_id:
            context["torneo"] = Torneo.objects.get(id=torneo_id)
        return context

class CalendarioDetailView(generic.DetailView):
    model = Calendario
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        calendario_id = self.kwargs.get('pk')
        if calendario_id:
            calendario = Calendario.objects.get(id=calendario_id)
            context["calendario"] = calendario
            context["torneo"] = calendario.torneo
            context["juegos"] = Juego.objects.filter(serie__calendario=calendario)
        return context

class CalendarioUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Calendario
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_message = "Calendario %(var)s actualizado con éxito"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, var=self.object.id)

class CalendarioDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Calendario
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:calendario_list")
    success_message = "Calendario %(nombre)s eliminada"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, nombre=self.object.id)

def obtener_equipos(request):
    id_torneo = request.GET.get('id_torneo')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        torneo = Torneo.objects.get(id=id_torneo)
        equipos = list(torneo.obtener_equipos_del_torneo().values('team_name', 'team_abbreviation'))
        return JsonResponse(json.dumps(equipos), safe=False)
    return HttpResponse('Wrong request')

def obtener_fechas(request):
    id_torneo = request.GET.get('id_torneo')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        torneo = Torneo.objects.get(id=id_torneo)
        fechas = list(torneo.obtener_fechas_del_torneo())
        return JsonResponse(json.dumps(fechas), safe=False)
    return HttpResponse('Wrong request')

# ==========================================
# SERIE - CRUD
# ==========================================
class SerieIndexView(generic.ListView):
    def get_queryset(self):
        return Serie.objects.all()

class SerieCreateView(SuccessMessageMixin, generic.CreateView):
    model = Serie
    fields = "__all__"
    template_name_suffix = "_create_form"
    success_url = reverse_lazy("tesis:serie_list")
    success_message = "Serie del calendario %(calendario)s creada con éxito"

class SerieDetailView(generic.DetailView):
    model = Serie
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["juegos"] = Juego.objects.filter(serie=self.object)
        context["calcula"] = self.object.test_communication_serie()
        return context

class SerieUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Serie
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_message = "Serie del calendario %(calendario)s actualizada con éxito"
    def get_success_url(self):
        return reverse_lazy("tesis:serie_detail", kwargs={"pk": self.object.pk})

class SerieDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Serie
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:serie_list")
    success_message = "Serie del calendario %(nombre)s eliminada"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, nombre=self.object.calendario)

# ==========================================
# CONDICIÓN - CRUD
# ==========================================
class CondicionIndexView(generic.ListView):
    def get_queryset(self):
        return Condicion.objects.all()

class CondicionCreateView(SuccessMessageMixin, generic.CreateView):
    model = Condicion
    fields = "__all__"
    template_name_suffix = "_create_form"
    success_url = reverse_lazy("tesis:condicion_list")
    success_message = "Condición creada con éxito"

class CondicionDetailView(generic.DetailView):
    model = Condicion
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["calcula"] = self.object.test_communication_condicion()
        return context

class CondicionUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Condicion
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_message = "Condición actualizada con éxito"
    def get_success_url(self):
        return reverse_lazy("tesis:condicion_detail", kwargs={"pk": self.object.pk})

class CondicionDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Condicion
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:condicion_list")
    success_message = "Condición eliminada"


# ==========================================
# PROGRAMACIÓN GENÉTICA (Vistas Auxiliares)
# ==========================================
class ProgramaFacadeView(generic.TemplateView):
    template_name = "tesis/programa_facade.html"

class ProgramaFacadeFormView(SuccessMessageMixin, generic.FormView):
    form_class = ProgramaFacadeForm
    template_name = "tesis/programa_facade_form.html"
    success_url = reverse_lazy("tesis:programa_facade_form")
    success_message = "Creada con éxito"
    def form_valid(self, form):
        form.iniciaPrograma()
        return super().form_valid(form)

class CrearArbol(View):
    def get(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            configuracion = Configuracion.objects.get(pk=kwargs['pk'])
            if configuracion and configuracion.calendario:
                el_calendario = configuracion.calendario
                arbol = el_calendario.obtener_expresion()
                distancia = el_calendario.calcular_distancia(arbol)
                context = {"arbol": arbol, "configuracion": configuracion, "distancia": distancia}
                return render(request, "tesis/crear_arbol.html", context)
        return render(request, "tesis/crear_arbol.html", {"arbol": 'Vacío', "distancia": 0.0})

class RunProgramaGenetico(View):
    def get(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            configuracion = Configuracion.objects.get(pk=kwargs['pk'])
            if configuracion and configuracion.calendario:
                resultado_ejecucion = configuracion.calendario.ejecutar_programa_genetico()
                diferencia = resultado_ejecucion[1]
                arbol = str(resultado_ejecucion[0])
                distancia = 0.5 
                
                ruta_svg = os.path.join(settings.BASE_DIR, 'media', 'svg', 'arbol.svg')
                try:
                    with open(ruta_svg, "r", encoding="utf-8") as file:
                        svg_content_safe = mark_safe(file.read())
                except FileNotFoundError:
                    svg_content_safe = mark_safe("<svg><text fill='red'>Generando estructura...</text></svg>")

                context = {
                    "arbol": arbol, 
                    "configuracion": configuracion, 
                    "distancia": distancia, 
                    "svg_content": svg_content_safe, 
                    "diferencia_del_promedio_contra_el_esperado": diferencia
                }
                return render(request, "tesis/crear_arbol_PG.html", context)
        return render(request, "tesis/crear_arbol_PG.html", {})

class RunProgramaGeneticoAlt(View):
    def get(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            configuracion = Configuracion.objects.get(pk=kwargs['pk'])
            if configuracion and configuracion.calendario:
                arbol = configuracion.calendario.ejecutar_programa_genetico_alt()
                distancia = configuracion.calendario.calcular_distancia(arbol)
                equipos = configuracion.calendario.torneo.obtener_equipos_del_torneo()
                context = {"arbol": arbol, "configuracion": configuracion, "distancia": distancia, "equipos": equipos}
                return render(request, "tesis/crear_arbol_PG_ALT.html", context)
        return render(request, "tesis/crear_arbol_PG_ALT.html", {})