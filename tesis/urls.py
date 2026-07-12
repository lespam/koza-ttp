"""
URL configuration for mi_proyecto project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from . import views
# ex: /myapp/
# ex: /tesis/
app_name = "tesis"
urlpatterns = [
    #path("", views.tesis_index, name="tesis_index"),
    # Equipos - LCRUD
    # List
    path("equipo/", views.EquipoIndexView.as_view(), name="equipo_list"),
    # Create
    path("equipo/create/", views.EquipoCreateView.as_view(), name="equipo_create"),
    # Read
    path("equipo/<int:pk>/", views.EquipoDetailView.as_view(), name="equipo_detail"),
    # Update
    path("equipo/<int:pk>/update/", views.EquipoUpdateView.as_view(), name="equipo_update"),
    # Delete
    path("equipo/<int:pk>/delete/", views.EquipoDeleteView.as_view(), name="equipo_delete"),
    # Ligas - LCRUD
    # List
    path("liga/", views.LigaIndexView.as_view(), name="liga_list"),
    # Create
    path("liga/create/", views.LigaCreateView.as_view(), name="liga_create"),
    # Read
    path("liga/<int:pk>/", views.LigaDetailView.as_view(), name="liga_detail"),
    # Update
    path("liga/<int:pk>/update/", views.LigaUpdateView.as_view(), name="liga_update"),
    # Delete
    path("liga/<int:pk>/delete/", views.LigaDeleteView.as_view(), name="liga_delete"),
    # Torneos - LCRUD
    # List
    path("torneo/", views.TorneoIndexView.as_view(), name="torneo_list"),
    # Create
    path("torneo/create/", views.TorneoCreateView.as_view(), name="torneo_create"),
    # Read
    path("torneo/<int:pk>/", views.TorneoDetailView.as_view(), name="torneo_detail"),
    # Update
    path("torneo/<int:pk>/update/", views.TorneoUpdateView.as_view(), name="torneo_update"),
    # Delete
    path("torneo/<int:pk>/delete/", views.TorneoDeleteView.as_view(), name="torneo_delete"),
    # Configuraciones - LCRUD
    # List
    path("configuracion/", views.ConfiguracionIndexView.as_view(), name="configuracion_list"),
    # Create
    path('configuracion/create/', views.ConfiguracionCreateView.as_view(), name='configuracion_create'),
    # int from the calendar
    path('configuracion/create/<int:pk>/', views.ConfiguracionCreateView.as_view(), name='configuracion_create'),
    # Read
    path("configuracion/<int:pk>/", views.ConfiguracionDetailView.as_view(), name="configuracion_detail"),
    path("configuracion/<int:pk>/generar_juegos/", views.GenerarJuegosView.as_view(), name="configuracion_generar_juegos"),
    path("configuracion/<int:pk>/generar_nuevos/", views.GenerarNuevosJuegosView.as_view(), name="configuracion_generar_nuevos"),
    
    #Programacion Genetica
    path("programacion_genetica/<int:pk>", views.ProgramacionGenetica.as_view(), name="programacion_genetica"),
    path("programacion_genetica/<int:pk>/arbol", views.CrearArbol.as_view(), name="crear_arbol"),
    path("programacion_genetica/<int:pk>/run", views.RunProgramaGenetico.as_view(), name="ejecutar_programa_genetico"),
    path("programacion_genetica/<int:pk>/run-alt", views.RunProgramaGeneticoAlt.as_view(), name="ejecutar_programa_genetico_alt"),
    path("svg/", views.my_view, name="vista-svg"),
    #path("programacion_genetica/", views.ProgramacionGenetica.as_view(), name="programacion_genetica"),
    
    
    # Update
    path("configuracion/<int:pk>/update/", views.ConfiguracionUpdateView.as_view(), name="configuracion_update"),
    # Delete
    path("configuracion/<int:pk>/delete/", views.ConfiguracionDeleteView.as_view(), name="configuracion_delete"),
    # Juegos - LCRUD
    # List
    path("juego/", views.JuegoIndexView.as_view(), name="juego_list"),
    # Create
    path("juego/create/", views.JuegoCreateView.as_view(), name="juego_create"),
    path("calendario/<int:pk>/juego/create/", views.JuegoCreateView.as_view(), name="juego_create"),
    # Read
    path("juego/<int:pk>/", views.JuegoDetailView.as_view(), name="juego_detail"),
    # Update
    path("juego/<int:pk>/update/", views.JuegoUpdateView.as_view(), name="juego_update"),
    # Delete
    path("juego/<int:pk>/delete/", views.JuegoDeleteView.as_view(), name="juego_delete"),
    # Calendarios - LCRUD
    # List
    path("calendario/", views.CalendarioIndexView.as_view(), name="calendario_list"),
    # Create
    path("calendario/create/", views.CalendarioCreateView.as_view(), name="calendario_create"),
    path("calendario/create/<int:pk>/", views.CalendarioCreateView.as_view(), name="calendario_create"),
    # get equipos request
     path('obtener_equipos/', views.obtener_equipos, name='obtener_equipos'),
     # get fechas request
        path('obtener_fechas/', views.obtener_fechas, name='obtener_fechas'),
    # Read
    path("calendario/<int:pk>/", views.CalendarioDetailView.as_view(), name="calendario_detail"),
    # Update
    path("calendario/<int:pk>/update/", views.CalendarioUpdateView.as_view(), name="calendario_update"),
    # Delete
    path("calendario/<int:pk>/delete/", views.CalendarioDeleteView.as_view(), name="calendario_delete"),
    # Series - LCRUD
    # List
    path("serie/", views.SerieIndexView.as_view(), name="serie_list"),
    # Create
    path("serie/create/", views.SerieCreateView.as_view(), name="serie_create"),
    path("calendario/<int:pk>/serie/create/", views.SerieCreateView.as_view(), name="serie_create"),
    # Read
    path("serie/<int:pk>/", views.SerieDetailView.as_view(), name="serie_detail"),
    # Update
    path("serie/<int:pk>/update/", views.SerieUpdateView.as_view(), name="serie_update"),
    # Delete
    path("serie/<int:pk>/delete/", views.SerieDeleteView.as_view(), name="serie_delete"),
    # Condicions - LCRUD
    # List
    path("condicion/", views.CondicionIndexView.as_view(), name="condicion_list"),
    # Create
    path("condicion/create/", views.CondicionCreateView.as_view(), name="condicion_create"),
    # Read
    path("condicion/<int:pk>/", views.CondicionDetailView.as_view(), name="condicion_detail"),
    # Update
    path("condicion/<int:pk>/update/", views.CondicionUpdateView.as_view(), name="condicion_update"),
    # Delete
    path("condicion/<int:pk>/delete/", views.CondicionDeleteView.as_view(), name="condicion_delete"),
    
    path("", views.index, name="index"),
    #path("user/create/", views.DetailView.as_view(), name="user_create"),
]

"""     # Calculadora - LCRUD
    # List
    path("calculadora/", views.CalculadoraIndexView.as_view(), name="calculadora_list"),
    # Create
    path("calculadora/create/", views.CalculadoraCreateView.as_view(), name="calculadora_create"),
    # Read
    path("calculadora/<int:pk>/", views.CalculadoraDetailView.as_view(), name="calculadora_detail"),
    # Update
    path("calculadora/<int:pk>/update/", views.CalculadoraUpdateView.as_view(), name="calculadora_update"),
    # Delete
    path("calculadora/<int:pk>/delete/", views.CalculadoraDeleteView.as_view(), name="calculadora_delete"), 
    
    if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)"""