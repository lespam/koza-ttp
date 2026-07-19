from django.urls import path
from . import views

app_name = "tesis"

urlpatterns = [
    # Vista Principal del Dashboard (Unificada)
    path('', views.DashboardView.as_view(), name='dashboard'),

    # Equipos - CRUD
    path("equipo/", views.EquipoIndexView.as_view(), name="equipo_list"),
    path("equipo/create/", views.EquipoCreateView.as_view(), name="equipo_create"),
    path("equipo/<int:pk>/", views.EquipoDetailView.as_view(), name="equipo_detail"),
    path("equipo/<int:pk>/update/", views.EquipoUpdateView.as_view(), name="equipo_update"),
    path("equipo/<int:pk>/delete/", views.EquipoDeleteView.as_view(), name="equipo_delete"),
    
    # Ligas - CRUD
    path("liga/", views.LigaIndexView.as_view(), name="liga_list"),
    path("liga/create/", views.LigaCreateView.as_view(), name="liga_create"),
    path("liga/<int:pk>/", views.LigaDetailView.as_view(), name="liga_detail"),
    path("liga/<int:pk>/update/", views.LigaUpdateView.as_view(), name="liga_update"),
    path("liga/<int:pk>/delete/", views.LigaDeleteView.as_view(), name="liga_delete"),
    path("liga/form/", views.LigaFormView.as_view(), name="liga_form"),
    
    # Torneos - CRUD
    path("torneo/", views.TorneoIndexView.as_view(), name="torneo_list"),
    path("torneo/create/", views.TorneoCreateView.as_view(), name="torneo_create"),
    path("torneo/<int:pk>/", views.TorneoDetailView.as_view(), name="torneo_detail"),
    path("torneo/<int:pk>/update/", views.TorneoUpdateView.as_view(), name="torneo_update"),
    path("torneo/<int:pk>/delete/", views.TorneoDeleteView.as_view(), name="torneo_delete"),
    
    # Configuraciones - CRUD
    path("configuracion/", views.ConfiguracionIndexView.as_view(), name="configuracion_list"),
    path('configuracion/create/', views.ConfiguracionCreateView.as_view(), name='configuracion_create'),
    path('configuracion/create/<int:pk>/', views.ConfiguracionCreateView.as_view(), name='configuracion_create_param'),
    path("configuracion/<int:pk>/", views.ConfiguracionDetailView.as_view(), name="configuracion_detail"),
    path("configuracion/<int:pk>/update/", views.ConfiguracionUpdateView.as_view(), name="configuracion_update"),
    path("configuracion/<int:pk>/delete/", views.ConfiguracionDeleteView.as_view(), name="configuracion_delete"),
    
    # Acciones extra de Configuracion
    path("configuracion/<int:pk>/generar_juegos/", views.GenerarJuegosView.as_view(), name="configuracion_generar_juegos"),
    path("configuracion/<int:pk>/generar_nuevos/", views.GenerarNuevosJuegosView.as_view(), name="configuracion_generar_nuevos"),
    
    # Juegos - CRUD
    path("juego/", views.JuegoIndexView.as_view(), name="juego_list"),
    path("juego/create/", views.JuegoCreateView.as_view(), name="juego_create"),
    path("calendario/<int:pk>/juego/create/", views.JuegoCreateView.as_view(), name="juego_create_param"),
    path("juego/<int:pk>/", views.JuegoDetailView.as_view(), name="juego_detail"),
    path("juego/<int:pk>/update/", views.JuegoUpdateView.as_view(), name="juego_update"),
    path("juego/<int:pk>/delete/", views.JuegoDeleteView.as_view(), name="juego_delete"),
    
    # Calendarios - CRUD
    path("calendario/", views.CalendarioIndexView.as_view(), name="calendario_list"),
    path("calendario/create/", views.CalendarioCreateView.as_view(), name="calendario_create"),
    path("calendario/create/<int:pk>/", views.CalendarioCreateView.as_view(), name="calendario_create_param"),
    path("calendario/<int:pk>/", views.CalendarioDetailView.as_view(), name="calendario_detail"),
    path("calendario/<int:pk>/update/", views.CalendarioUpdateView.as_view(), name="calendario_update"),
    path("calendario/<int:pk>/delete/", views.CalendarioDeleteView.as_view(), name="calendario_delete"),
    
    # Peticiones AJAX para calendarios
    path('obtener_equipos/', views.obtener_equipos, name='obtener_equipos'),
    path('obtener_fechas/', views.obtener_fechas, name='obtener_fechas'),
    
    # Series - CRUD
    path("serie/", views.SerieIndexView.as_view(), name="serie_list"),
    path("serie/create/", views.SerieCreateView.as_view(), name="serie_create"),
    path("calendario/<int:pk>/serie/create/", views.SerieCreateView.as_view(), name="serie_create_param"),
    path("serie/<int:pk>/", views.SerieDetailView.as_view(), name="serie_detail"),
    path("serie/<int:pk>/update/", views.SerieUpdateView.as_view(), name="serie_update"),
    path("serie/<int:pk>/delete/", views.SerieDeleteView.as_view(), name="serie_delete"),
    
    # Condiciones - CRUD
    path("condicion/", views.CondicionIndexView.as_view(), name="condicion_list"),
    path("condicion/create/", views.CondicionCreateView.as_view(), name="condicion_create"),
    path("condicion/<int:pk>/", views.CondicionDetailView.as_view(), name="condicion_detail"),
    path("condicion/<int:pk>/update/", views.CondicionUpdateView.as_view(), name="condicion_update"),
    path("condicion/<int:pk>/delete/", views.CondicionDeleteView.as_view(), name="condicion_delete"),
    
    # Programación Genética Vistas Auxiliares y Fachadas
    path("programa_facade/", views.ProgramaFacadeView.as_view(), name="programa_facade"),
    path("programa_facade/form/", views.ProgramaFacadeFormView.as_view(), name="programa_facade_form"),
    path("programacion_genetica/<int:pk>", views.RunProgramaGenetico.as_view(), name="ejecutar_programa_genetico"),
    path("programacion_genetica/<int:pk>/arbol", views.CrearArbol.as_view(), name="crear_arbol"),
    path("programacion_genetica/<int:pk>/run-alt", views.RunProgramaGeneticoAlt.as_view(), name="ejecutar_programa_genetico_alt"),
    path("svg/", views.my_view, name="vista-svg"),
]