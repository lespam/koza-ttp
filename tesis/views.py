import csv
from datetime import timezone
import datetime
import json
import random
from typing import Any

import pygraphviz as pgv
#from IPython.display import Image

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.views import View, generic
from django.contrib import messages
from django.core import serializers
from django.http import JsonResponse

from .models import Serie, User, Equipo, Liga, Calendario, Torneo, Configuracion, Juego, Condicion
from django.views.generic.edit import FormView
from .forms import CalendarioForm, ConfiguracionForm, LigaForm, ProgramaFacadeForm
from django.contrib.messages.views import SuccessMessageMixin
from django.core import serializers

from django.utils.safestring import mark_safe

from django.conf import settings
import os  # Lo importamos aquí directo solo para asegurar que no falte


"""Create Views:
Implement the views in tesis/views.py. 
These views will handle HTTP requests and render templates."""

def my_view(request):
    # Read the SVG file content
    with open(f"{path}/media/svg/arbol.svg", "r") as svg_file:
        svg_content = svg_file.read()

    # Mark the SVG content as safe
    svg_content_safe = mark_safe(svg_content)

    # Pass the safe SVG content to the template
    context = {'svg_content': svg_content_safe}
    return render(request, 'tesis/svg_template.html', context)

# Path: mi_proyecto/tesis/views.py
# from django.shortcuts import render
# Create a view for the home page to render the index.html template.
def index(request):
    return render(request, "tesis/index.html")
def tesis_index(request):
    return render(request, "tesis/tesis_index.html")
    #template_name = "tesis/user.html"
# Equipos - CRUD
# List
class EquipoIndexView(generic.ListView):
    def get_queryset(self):
        return Equipo.objects.all()
# Create
class EquipoCreateView(SuccessMessageMixin, generic.CreateView):
    model = Equipo
    template_name_suffix = "_create_form"
    success_url = reverse_lazy("tesis:equipo_list")
    success_message = "Equipo creado con éxito"
    fields = "__all__"
# Read
class EquipoDetailView(generic.DetailView):
    model = Equipo
    template_name = "tesis/equipo_detail.html"
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["calcula"] = self.object.test_communication_equipo()
        return context
# Update
class EquipoUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Equipo
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_message = "Equipo actualizado con éxito"

    def get_success_url(self):
        return reverse_lazy("tesis:equipo_detail", kwargs={"pk": self.object.pk})
# Delete
class EquipoDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Equipo
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:equipo_list")
    success_message = "Equipo %(nombre)s eliminado"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        if self.object.team_name:
            return self.success_message % dict(cleaned_data, nombre = self.object.team_name)
        else:
            return self.success_message % dict(cleaned_data, nombre = "" )
    
# Liga - CRUD
# List
class LigaIndexView(generic.ListView):
    def get_queryset(self):
        return Liga.objects.order_by("id")
# Create
class LigaCreateView(SuccessMessageMixin, generic.CreateView):
    model = Liga
    fields = "__all__"
    template_name_suffix = "_create_form"
    success_url = reverse_lazy("tesis:liga_list")
    success_message = "Liga %(nombre)s creada con éxito"
# # Read
class LigaDetailView(generic.DetailView):
    model = Liga
    template_name = "tesis/liga_detail.html"
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["calcula"] = self.object.test_communication_liga()
        return context
# Update
class LigaUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Liga
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_url = generic.UpdateView.success_url
    success_message = "Liga %(nombre)s actualizada con éxito"
    def get_success_url(self):
        return reverse_lazy("tesis:liga_detail", kwargs={"pk": self.object.pk})
# Delete
class LigaDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Liga
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:liga_list")
    success_message = "Liga %(nombre)s eliminada"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, nombre = self.object.nombre)
# Torneo - CRUD
# List
class TorneoIndexView(generic.ListView):
    def get_queryset(self):
        return Torneo.objects.order_by("id")
# Create
class TorneoCreateView(SuccessMessageMixin, generic.CreateView):
    model = Torneo
    fields = "__all__"
    template_name_suffix = "_create_form"
    success_url = reverse_lazy("tesis:torneo_list")
    success_message = "Torneo %(nombre)s creada con éxito"
# Read
class TorneoDetailView(generic.DetailView):
    model = Torneo
    template_name = "tesis/torneo_detail.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# Update
class TorneoUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Torneo
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_url = generic.UpdateView.success_url
    success_message = "Torneo %(nombre)s actualizada con éxito"
# Delete
class TorneoDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Torneo
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:torneo_list")
    success_message = "Torneo %(nombre)s eliminada"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, nombre = self.object.nombre)
# Configuracion - CRUD
# List
class ConfiguracionIndexView(generic.ListView):
    def get_queryset(self):
        return Configuracion.objects.all()
# Create
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
            return "Configuracion creada con éxito para el calendario " + str(calendario_id)
        else:
            return "Configuracion %(id)s creada con éxito" % dict(cleaned_data, id = self.object.id)
            
    def form_valid(self, form):
        calendario_id = self.kwargs.get('pk')
        if calendario_id:
            calendario = get_object_or_404(Calendario, id=calendario_id)
            form.instance.calendario = calendario
        return super().form_valid(form)
# Read
class ConfiguracionDetailView(generic.DetailView):
    model = Configuracion
    # validate a form and return the context
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        return context
# GenerarJuegosView    
class GenerarJuegosView(View):
    def get(self, request, *args, **kwargs):
        # If the request was made through the ProgramacionGenetica view 
        # to create a duplicate of the current configuration and generate a new calendar
        if kwargs.get('pk'):
            configuracion = Configuracion.objects.get(pk=kwargs['pk'])
            if configuracion:
                print(f"GenerarJuegosView - configuracion: {configuracion.id} ")
                if configuracion.calendario:
                    configuracion.generar_calendario_aleatorio()
                    return HttpResponseRedirect(reverse("tesis:calendario_detail", args=(configuracion.calendario.id,)))
            return HttpResponseRedirect(reverse("tesis:configuracion_list"))
        # If the request was made through the ConfiguracionDetailView
        # to generate the games of the current configuration
class GenerarNuevosJuegosView(View):
    def get(self, request, *args, **kwargs):
        # If the request was made through the ProgramacionGenetica view 
        # to create a duplicate of the current configuration and generate a new calendar
        if kwargs.get('pk'):
            configuracion = Configuracion.objects.get(pk=kwargs['pk'])
            if configuracion:
                print(f"GenerarJuegosView - configuracion: {configuracion.id} ")
                if configuracion.calendario:
                    nueva_configuracion, nuevo_calendario = configuracion.duplicar_calendario_configuracion_y_generar_nuevo_calendario()
                    return HttpResponseRedirect(reverse("tesis:calendario_detail", args=(nuevo_calendario.id,)))
            return HttpResponseRedirect(reverse("tesis:configuracion_list"))
        # If the request was made through the ConfiguracionDetailView
        # to generate the games of the current configuration return 404
        return HttpResponseRedirect(reverse("tesis:configuracion_list"))
    
class CrearArbol(View):
    def get(self, request, *args, **kwargs):
        # If the request was made through the ProgramacionGenetica view 
        # get the calendar games and create a tree structure and return the image
        if kwargs.get('pk'):
            configuracion = Configuracion.objects.get(pk=kwargs['pk'])
            if configuracion:
                print(f"CrearArbol - configuracion: {configuracion.id} ")
                if configuracion.calendario:
                    # We call the ProgramacionGenetica to create a tree from calendario
                    el_calendario = configuracion.calendario
                    # We call the ProgramacionGenetica to create a tree from calendario
                    arbol = el_calendario.obtener_expresion()
                    distancia = el_calendario.calcular_distancia(arbol)
                    #distancia = 0.5
                    context = {"arbol": arbol, "configuracion": configuracion, "distancia": distancia}
                    return render(request, "tesis/crear_arbol.html", context)
        context = {"arbol": 'Vacio', "configuracion": 'Vacio', "distancia": 0.5}
        return render(request, "tesis/crear_arbol.html", context)
# RunProgramaGenetico
class RunProgramaGenetico(View):
    def get(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            configuracion = Configuracion.objects.get(pk=kwargs['pk'])
            if configuracion:
                print(f"RunProgramaGenetico - configuracion: {configuracion.id} ")
                if configuracion.calendario:
                    # We call the ProgramacionGenetica to create a tree from calendario
                    el_calendario = configuracion.calendario
                    # We call the ProgramacionGenetica to create a tree from calendario
                    
                    
                    resultado_ejecucion = el_calendario.ejecutar_programa_genetico()
                    print(f'resultado ddddddd: {resultado_ejecucion}')
                    diferencia_del_promedio_contra_el_esperado = resultado_ejecucion[1]
                    arbol = str(resultado_ejecucion[0])
                    print(f'aaaarrrrbbbooooll: {arbol}')

                    print("Paso 1: Entrando a calcular distancia...")
                    # Comenta la función original un momento para ver si es la culpable:
                    # distancia = el_calendario.calcular_distancia(arbol)
                    distancia = 0.5  # Valor dummy de prueba
                    print("Paso 1 completado con éxito")

                    print("Paso 2: Armando la ruta con OS...")
                    ruta_svg = os.path.join(settings.BASE_DIR, 'media', 'svg', 'arbol.svg')
                    print("Paso 2 completado con éxito")

                    try:
                        print("entered TRY")
                        with open(ruta_svg, "r", encoding="utf-8") as file:
                            svg_content = file.read()
                        # Usamos mark_safe para que el HTML lo interprete como gráfico y no como texto crudo
                        svg_content_safe = mark_safe(svg_content)
                    except FileNotFoundError:
                        # Fallback seguro en caso de que el archivo aún no se haya terminado de escribir
                        svg_content_safe = mark_safe("<svg><text x='10' y='20' fill='red'>Generando estructura del árbol...</text></svg>")

                    # Y luego pasas svg_content_safe a tu context
                    # context = { ... "svg_content": svg_content_safe, ... }
                    
                    #context = {"arbol": arbol, "configuracion": configuracion, "distancia": distancia, "svg_content": svg_content_safe, "fitness_num_juegos", fitness_num_juegos)
                    context = {"arbol": arbol, "configuracion": configuracion, "distancia": distancia, "svg_content": svg_content_safe, "diferencia_del_promedio_contra_el_esperado": diferencia_del_promedio_contra_el_esperado}
                    
                    return render(request, "tesis/crear_arbol_PG.html", context)
        context = {"arbol": 'Vacio', "configuracion": 'Vacio', "distancia": 0.0, "svg_content": "Vacio", "diferencia_del_promedio_contra_el_esperado":"Vacio"}
        return render(request, "tesis/crear_arbol_PG.html", context)
    
# RunProgramaGeneticoAlt
class RunProgramaGeneticoAlt(View):
    def get(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            configuracion = Configuracion.objects.get(pk=kwargs['pk'])
            if configuracion:
                print(f"RunProgramaGenetico ALT - configuracion: {configuracion.id} ")
                if configuracion.calendario:
                    # We call the ProgramacionGenetica to create a tree from calendario
                    el_calendario = configuracion.calendario
                    # We call the ProgramacionGenetica to create a tree from calendario
                    
                    arbol = el_calendario.ejecutar_programa_genetico_alt()
                    distancia = el_calendario.calcular_distancia(arbol)
                    equipos = configuracion.calendario.torneo.obtener_equipos_del_torneo()
                    #distancia = 0.5
                    context = {"arbol": arbol, 
                               "configuracion": configuracion, 
                               "distancia": distancia,
                               "equipos": equipos}
                    return render(request, "tesis/crear_arbol_PG_ALT.html", context)
        context = {"arbol": 'Vacio', "configuracion": 'Vacio', "distancia": 0.5}
        return render(request, "tesis/crear_arbol_PG_ALT.html", context)
 
# Update
class ConfiguracionUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Configuracion
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_url = generic.UpdateView.success_url
    success_message = "Configuracion %(nombre)s actualizada con éxito"
# Delete
class ConfiguracionDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Configuracion
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:configuracion_list")
    success_message = "Configuracion %(nombre)s eliminada"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, nombre = self.object.nombre)
# Juego - CRUD
# List
class JuegoIndexView(generic.ListView):
    def get_queryset(self):
        return Juego.objects.all()
# Create
class JuegoCreateView(SuccessMessageMixin, generic.CreateView):
    model = Juego
    fields = "__all__"
    template_name_suffix = "_create_form"
    success_url = generic.CreateView.success_url
    success_message = "Juego creado con éxito"
    
    def get_success_url(self):
        # We go back to the Calendario that generated this Juego
        calendario_id = self.kwargs.get('pk')
        if calendario_id:
            # change success message
            return reverse_lazy("tesis:calendario_detail", kwargs={"pk": calendario_id})
        else:
            return reverse_lazy("tesis:juego_list")
        
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        calendario_id = self.kwargs.get('pk')
        if calendario_id:
            calendario = Calendario.objects.get(id=calendario_id)
            return "Juego del calendario " + str(calendario.pk) + " creado con éxito"
        else:
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
            torneo = calendario.torneo
            form.instance.calendario = calendario
            form.instance.torneo = torneo
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        calendario_id = self.kwargs.get('pk')
        if calendario_id:
            calendario = Calendario.objects.get(id=calendario_id)
            context["calendario"] = calendario
            context["torneo"] = calendario.torneo
            context["equipos"] = calendario.torneo.obtener_equipos_del_torneo()
        else:
            context["calendario"] = None
            context["torneo"] = None
            context["equipos"] = None
        return context
# Read
class JuegoDetailView(generic.DetailView):
    model = Juego
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["calcula"] = self.object.test_communication_juego()
        return context
# Update
class JuegoUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Juego
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_url = generic.UpdateView.success_url
    #success_message = "Juego del calendario %(calendario)s actualizado con éxito"
    success_message = "Juego actualizado con éxito"
    def get_success_url(self):
        return reverse_lazy("tesis:juego_detail", kwargs={"pk": self.object.pk})
# Delete
class JuegoDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Juego
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:juego_list")
    success_message = "Juego de la serie %(serie)s eliminado"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, serie = self.object.serie)
# Calendario - CRUD
# List
class CalendarioIndexView(generic.ListView):
    context_object_name = "calendario_list"
    def get_queryset(self):
        return Calendario.objects.all()
    def get_lista_de_equipos(self):
        return Equipo.objects
# Create
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
    def seleccionar_torneo(self):
        # Cada que seleccionamos otro calendario del dropdown, se actualiza el torneo
        torneo_id = self.kwargs.get('pk')
        if torneo_id:
            torneo = Torneo.objects.get(id=torneo_id)
            return torneo
    def form_valid(self, form):
        # get the new value of the torneo_id
        torneo_id = self.kwargs.get('id_torneo')
        
        if torneo_id:
            torneo = Torneo.objects.get(id=torneo_id)
            form.instance.torneo = torneo
        success_message = "Calendario creado con éxito"  +  " para el torneo " + form.instance.torneo.nombre
        #success_message = success_message
        self.success_message = success_message
        validation = super().form_valid(form)
        return validation
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        torneo_id = self.kwargs.get('pk')
        if torneo_id:
            torneo = Torneo.objects.get(id=torneo_id)
            context["torneo"] = torneo
            #context["equipos"] = torneo.obtener_equipos_del_torneo()
        else:
            context["torneo"] = None
            #context["equipos"] = None
        return context
    
def obtener_equipos(request):
    id_torneo = request.GET.get('id_torneo')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        torneo = Torneo.objects.get(id=id_torneo)
        equipos = list(torneo.obtener_equipos_del_torneo().values('team_name', 'team_abbreviation'))
        data = json.dumps(equipos)
        #print(data)
        return JsonResponse(data, safe=False)
    return HttpResponse('Wrong request')

def obtener_fechas(request):
    id_torneo = request.GET.get('id_torneo')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        torneo = Torneo.objects.get(id=id_torneo)
        fechas = list(torneo.obtener_fechas_del_torneo())
        data = json.dumps(fechas)
        #print(data)
        return JsonResponse(data, safe=False)
    return HttpResponse('Wrong request')
# Read
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
            #context["equipos"] = calendario.torneo.obtener_equipos_del_torneo()
        else:
            context["calendario"] = None
            context["torneo"] = None
            #context["equipos"] = None
        return context
# Update
class CalendarioUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Calendario
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_url = generic.UpdateView.success_url
    success_message = "Calendario %(var)s actualizado con éxito"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, var = self.object.id)
# Delete
class CalendarioDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Calendario
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:calendario_list")
    success_message = "Calendario %(nombre)s eliminada"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, nombre = self.object.id)
# Liga - CRUD
# List
class LigaIndexView(generic.ListView):
    def get_queryset(self):
        return Liga.objects.order_by("id")
# Create
class LigaCreateView(SuccessMessageMixin, generic.CreateView):
    model = Liga
    fields = "__all__"
    template_name_suffix = "_create_form"
    success_url = reverse_lazy("tesis:liga_list")
    success_message = "%(nombre)s creada con éxito"
# Read
class LigaDetailView(generic.DetailView):
    model = Liga
    template_name = "tesis/liga_detail.html"
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["calcula"] = self.object.test_communication_liga()
        return context
# Update
class LigaUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Liga
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_url = generic.UpdateView.success_url
    success_message = "%(nombre)s actualizada con éxito"
# Delete
class LigaDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Liga
    template_name_suffix = "_confirm_delete"
    success_message = "%(nombre)s eliminada"
    success_url = reverse_lazy("tesis:liga_list")
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, nombre = self.object.nombre)    
# ---
# Vistas para la integracion de la aplicacion del planificador de calendarios con un programa genetico
# ---
# Experimental view connection
# Experimental form view
class LigaFormView(SuccessMessageMixin, generic.FormView):
    template_name = "tesis/liga_form.html"
    form_class = LigaForm
    success_url = reverse_lazy("tesis:liga_list")
    success_message = "%(nombre)s creada con éxito"
    def crea_liga(self):
        liga = Liga
        liga.save()
    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.send_data()
        return super().form_valid(form)
# Programa Facade
class ProgramaFacadeView(generic.TemplateView):
    template_name = "tesis/programa_facade.html"
# Programa Facade Form
class ProgramaFacadeFormView(SuccessMessageMixin, generic.FormView):
    # Le pedimos al usuario los datos
    form_class = ProgramaFacadeForm
    template_name = "tesis/programa_facade_form.html"
    success_url = reverse_lazy("tesis:programa_facade_form")
    success_message = "Creada con éxito"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data)
    def form_valid(self, form):
        form.iniciaPrograma()
        return super().form_valid(form)
        #latest_question_list = Question.objects.order_by("-pub_date")[:5]
        #context = {"latest_question_list": latest_question_list}
        #return render(request, "polls/index.html", context)
# Experimental view POST
def crear(request, **kwargs):
    pk = kwargs.get('pk')
    if pk:
        initial = {'torneo': pk}
    else:
        initial = {}
    form = CalendarioForm(request.POST or None, initial=initial)
    if form.is_valid():
        form.save()
        messages.success(request, "Calendario creado con éxito")
        
        return HttpResponseRedirect(reverse("tesis:torneo_detail", args=(form.instance.torneo.id,)))
    else:
        math = 25+100
        return render(request, "tesis/calendario_create_form.html", {"form": form, "math": math})

# Serie - CRUD
# List
class SerieIndexView(generic.ListView):
    def get_queryset(self):
        return Serie.objects.all()
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        return context

# Create
class SerieCreateView(SuccessMessageMixin, generic.CreateView):
    model = Serie
    fields = "__all__"
    template_name_suffix = "_create_form"
    success_url = reverse_lazy("tesis:serie_list")
    success_message = "Serie del calendario %(calendario)s creada con éxito"

# Read
class SerieDetailView(generic.DetailView):
    model = Serie
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["juegos"] = Juego.objects.filter(serie=self.object)
        context["calcula"] = self.object.test_communication_serie()
        return context

# Update
class SerieUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Serie
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_url = generic.UpdateView.success_url
    success_message = "Serie del calendario %(calendario)s actualizada con éxito"

    def get_success_url(self):
        return reverse_lazy("tesis:serie_detail", kwargs={"pk": self.object.pk})

# Delete
class SerieDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Serie
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:serie_list")
    success_message = "Serie del calendario %(nombre)s eliminada"

    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, nombre=self.object.calendario)

# Condicion - CRUD
# List
class CondicionIndexView(generic.ListView):
    def get_queryset(self):
        return Condicion.objects.all()

# Create
class CondicionCreateView(SuccessMessageMixin, generic.CreateView):
    model = Condicion
    fields = "__all__"
    template_name_suffix = "_create_form"
    success_url = reverse_lazy("tesis:condicion_list")
    success_message = "Condicion del calendario %(calendario)s creada con éxito"

# Read
class CondicionDetailView(generic.DetailView):
    model = Condicion
    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["calcula"] = self.object.test_communication_condicion()
        return context

# Update
class CondicionUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Condicion
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_url = generic.UpdateView.success_url
    success_message = "Condicion del calendario %(calendario)s actualizada con éxito"
    def get_success_url(self):
        return reverse_lazy("tesis:condicion_detail", kwargs={"pk": self.object.pk})
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, calendario=self.object.calendario)

# Delete
class CondicionDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Condicion
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:condicion_list")
    success_message = "Condicion del calendario %(calendario)s eliminada"

    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, calendario=self.object.calendario)
    
class ProgramacionGenetica(View):
    def get(self, request, *args, **kwargs):
        id = self.kwargs.get('pk')
        configuracion = get_object_or_404(Configuracion, id=id) if id else None
        context = {"configuracion": configuracion}
        return render(request, 'tesis/programacion_genetica.html', context)

    def post(self, request, *args, **kwargs):
        id = self.kwargs.get('pk')
        configuracion = get_object_or_404(Configuracion, id=id) if id else None
        configuracion, calendario = configuracion.duplicar_calendario_configuracion_y_generar_nuevo_calendario()
        return render(request, 'tesis/calendario_detail.html', {'calendario': calendario})
        
    def obtener_equipos_post(self, torneo_id):
        torneo = Torneo.objects.get(id=torneo_id)
        equipos = torneo.obtener_equipos_del_torneo()
        return equipos
    def post_equipos(self, request, *args, **kwargs):
        torneo_id = request.POST.get('torneo_id')
        print(f"torneo_id: {torneo_id}")
        results = obtener_equipos(torneo_id)
        return render(request, 'tesis/programacion_genetica.html', {'results': results})
    def obtener_fechas_de_juegos(fecha_inicio, fecha_fin):
        return [fecha_inicio + datetime.timedelta(days=i) for i in range((fecha_fin - fecha_inicio).days + 1)]
    def send_calendario(self, series, juegos):
        results = "Calendario enviado"
        return results
    
    def create_juegos_aleatorios(equipos, fechas):
        # Create a list of all possible pairs of teams
        all_pairs = [(team1, team2) for team1 in equipos for team2 in equipos if team1 != team2]
        # Shuffle the list of pairs
        random.shuffle(all_pairs)
        # Create a list of games, each with a date and a pair of teams
        games = [Juego(date, team1, team2) for date in fechas for team1, team2 in all_pairs]
        return games
    def encode_juegos(juegos):
        return ','.join([f"{juego.date},{juego.team1},{juego.team2}" for juego in juegos])
    def decode_juegos(encoded_juegos):
        return [Juego(*juego.split(',')) for juego in encoded_juegos.split(',')]
    def run_genetic_program(teams, dates):
    # Run your genetic program here
    # This is just a placeholder
        results = "Genetic program results"
        return results
    def export_results_to_csv(results, filename):
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Results'])
            writer.writerow([results])
    def draw_tree(tree):
        graph = pgv.AGraph()
        # Add nodes and edges to the graph based on your tree
        # This is just a placeholder
        graph.add_node('root')
        graph.add_edge('root', 'child1')
        graph.add_edge('root', 'child2')
        graph.draw('tree.svg', prog='dot', format='svg')
        return ""#Image('tree.svg')       
""" # Calculadora - CRUD
# List
class CalculadoraIndexView(generic.ListView):
    def get_queryset(self):
        return Calculadora.objects.all()
# Create
class CalculadoraCreateView(SuccessMessageMixin, generic.CreateView):
    model = Calculadora
    fields = "__all__"
    template_name_suffix = "_create_form"
    success_url = reverse_lazy("tesis:calculadora_list")
    success_message = "Calculadora %(nombre)s creada con éxito"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, nombre=self.object.id)
# Read
class CalculadoraDetailView(generic.DetailView):
    model = Calculadora
    # Calculation of the distance using the calcula_distancia function from the model.
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["calcula"] = self.object.calcula_distancia()
        return context
    
# Update
class CalculadoraUpdateView(SuccessMessageMixin, generic.UpdateView):
    model = Calculadora
    fields = "__all__"
    template_name_suffix = "_update_form"
    success_url = generic.UpdateView.success_url
    success_message = "Calculadora %(nombre)s actualizada con éxito"
    def get_success_url(self):
        return reverse_lazy("tesis:calculadora_detail", kwargs={"pk": self.object.pk})
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, nombre=self.object.pk)
# Delete
class CalculadoraDeleteView(SuccessMessageMixin, generic.DeleteView):
    model = Calculadora
    template_name_suffix = "_confirm_delete"
    success_url = reverse_lazy("tesis:calculadora_list")
    success_message = "Calculadora %(nombre)s eliminada"
    def get_success_message(self, cleaned_data: dict[str, str]) -> str:
        return self.success_message % dict(cleaned_data, nombre=self.object.pk)
         """