import datetime
from unittest import mock

from django.urls import reverse
from django.test import TestCase
from django.urls import URLPattern

from programa_genetico.programagenetico import ProgramaGenetico

from .models import Calendario, Configuracion, Equipo, Juego, Liga, Serie, Torneo
from .urls import urlpatterns


def crear_datos_de_ejemplo():
    """Dos equipos, una liga, un torneo, un calendario con una serie de 2 juegos
    y una configuración: lo mínimo para recorrer todas las páginas."""
    local = Equipo.objects.create(team_abbreviation="SEA", team_name="Seattle", lat=47.59, lon=-122.33)
    visita = Equipo.objects.create(team_abbreviation="CHC", team_name="Chicago", lat=41.94, lon=-87.65)
    liga = Liga.objects.create(nombre="Liga de prueba")
    liga.equipos.add(local, visita)
    torneo = Torneo.objects.create(
        nombre="Torneo de prueba", fecha_inicio=datetime.date(2026, 4, 1),
        fecha_fin=datetime.date(2026, 4, 30), numero_de_juegos=2, numero_de_series=1,
        metodo="haversine", unidad="km")
    torneo.liga.add(liga)
    calendario = Calendario.objects.create(torneo=torneo)
    serie = Serie.objects.create(calendario=calendario, numero_de_serie=1)
    for dia in (1, 2):
        inicio = datetime.datetime(2026, 4, dia, 19, tzinfo=datetime.timezone.utc)
        Juego.objects.create(serie=serie, fecha_de_inicio=inicio,
                             fecha_de_fin=inicio + datetime.timedelta(hours=3),
                             equipo_en_casa=local, equipo_visita=visita)
    configuracion = Configuracion.objects.create(
        calendario=calendario, nombre="Prueba", poblacion=10, generaciones=1,
        probabilidad_de_cruce=0.8, probabilidad_de_reproduccion=0.2)
    return configuracion


class PaginaDeInicio(TestCase):
    def test_portada(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "el algoritmo no le ganó al azar")
        self.assertContains(r, 'id="boton-tema"')
        for nombre in ("documentacion:index", "tesis:guia", "documentacion:historico"):
            self.assertContains(r, f'href="{reverse(nombre)}"')

    def test_enlaces_viejos_a_la_demo_siguen_funcionando(self):
        r = self.client.get("/?configuracion=4&ejecutar=true")
        self.assertRedirects(r, "/demo/?configuracion=4&ejecutar=true", fetch_redirect_response=False)


class PaginaDeDemo(TestCase):
    def test_base_vacia_muestra_como_empezar(self):
        r = self.client.get("/demo/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Todavía no hay ninguna configuración")
        self.assertContains(r, "Para presentarlo a tu equipo")

    def test_elige_la_configuracion_con_juegos(self):
        Configuracion.objects.create(nombre="Sin calendario", poblacion=1, generaciones=1,
                                     probabilidad_de_cruce=0, probabilidad_de_reproduccion=0)
        configuracion = crear_datos_de_ejemplo()
        r = self.client.get("/demo/")
        self.assertEqual(r.context["configuracion"], configuracion)
        self.assertEqual(len(r.context["juegos"]), 2)
        self.assertContains(r, f"?configuracion={configuracion.pk}&amp;ejecutar=true")

    def test_ejecutar_optimizacion_no_da_error(self):
        # Regresión: "Server Error (500)" por DEAP 1.4.1 con Python 3.11 o más nuevo.
        configuracion = crear_datos_de_ejemplo()
        # La gráfica del árbol necesita pygraphviz y escribe en media/; no es parte de esta prueba.
        with mock.patch.object(ProgramaGenetico, "genera_grafica"):
            r = self.client.get(f"/demo/?configuracion={configuracion.pk}&ejecutar=true")
        self.assertEqual(r.status_code, 200)

    def test_configuracion_inexistente_da_404(self):
        self.assertEqual(self.client.get("/demo/?configuracion=999").status_code, 404)


class TodasLasPaginas(TestCase):
    """Cada página de la herramienta abre sin error. Se omiten las que borran datos
    o ejecutan el algoritmo genético (tardan y cambian la base)."""

    omitidas = ("delete", "generar", "programacion_genetica", "obtener_", "<slug:paso>")

    def test_ninguna_pagina_da_error(self):
        configuracion = crear_datos_de_ejemplo()
        calendario = configuracion.calendario
        pks = {
            "equipo": Equipo.objects.first().pk, "liga": Liga.objects.first().pk,
            "torneo": calendario.torneo.pk, "configuracion": configuracion.pk,
            "calendario": calendario.pk, "serie": calendario.series.first().pk,
            "juego": Juego.objects.first().pk,
        }
        for patron in urlpatterns:
            ruta = str(patron.pattern)
            if not isinstance(patron, URLPattern) or any(o in ruta for o in self.omitidas):
                continue
            if "condicion/<int:pk>" in ruta:
                continue  # no hay condiciones en los datos de ejemplo
            prefijo = ruta.split("/")[0]
            url = "/" + ruta.replace("<int:pk>", str(pks.get(prefijo, calendario.pk)))
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


class FlujoCompleto(TestCase):
    """Del registro al calendario, como lo haría una persona con los formularios:
    equipos → liga → torneo → calendario → configuración → generar juegos → inicio."""

    def test_del_registro_al_calendario(self):
        equipos = [("SEA", 47.59, -122.33), ("CHC", 41.94, -87.65),
                   ("NYY", 40.83, -73.93), ("BOS", 42.35, -71.10)]
        for abreviatura, lat, lon in equipos:
            r = self.client.post("/equipo/create/", {"team_abbreviation": abreviatura,
                                                     "team_name": abreviatura, "lat": lat, "lon": lon})
            self.assertEqual(r.status_code, 302)

        r = self.client.post("/liga/create/", {"nombre": "Liga", "equipos": list(
            Equipo.objects.values_list("pk", flat=True))})
        self.assertEqual(r.status_code, 302)

        r = self.client.post("/torneo/create/", {
            "nombre": "Torneo", "liga": [Liga.objects.get().pk], "fecha_inicio": "2026-04-01",
            "fecha_fin": "2026-09-30", "dias_seleccionados": "Lunes, Martes",
            "numero_de_juegos": 6, "numero_de_series": 3, "metodo": "haversine", "unidad": "km"})
        self.assertEqual(r.status_code, 302)
        torneo = Torneo.objects.get()

        r = self.client.post(f"/calendario/create/{torneo.pk}/", {"torneo": torneo.pk})
        self.assertEqual(r.status_code, 302)
        calendario = Calendario.objects.get()

        r = self.client.post(f"/configuracion/create/{calendario.pk}/", {
            "calendario": calendario.pk, "nombre": "Prueba", "poblacion": 10, "generaciones": 1,
            "probabilidad_de_cruce": 0.8, "probabilidad_de_reproduccion": 0.2})
        self.assertEqual(r.status_code, 302)
        configuracion = Configuracion.objects.get()

        r = self.client.get(f"/configuracion/{configuracion.pk}/generar_juegos/")
        self.assertRedirects(r, f"/calendario/{calendario.pk}/")
        juegos = Juego.objects.filter(serie__calendario=calendario).count()
        self.assertGreater(juegos, 0)

        r = self.client.get(f"/calendario/{calendario.pk}/")
        self.assertEqual(r.status_code, 200)
        r = self.client.get(f"/demo/?configuracion={configuracion.pk}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context["juegos"]), min(juegos, 50))


class GuiaDeCincoPasos(TestCase):
    """La guía lleva de los equipos al calendario, un paso a la vez."""

    def test_recorrido_completo(self):
        r = self.client.get("/guia/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'aria-label="Pasos de la guía"')

        # Sin equipos no se puede saltar a la liga
        r = self.client.get("/guia/liga/")
        self.assertRedirects(r, "/guia/equipos/")

        for abreviatura, lat, lon in [("SEA", 47.59, -122.33), ("CHC", 41.94, -87.65),
                                      ("NYY", 40.83, -73.93), ("BOS", 42.35, -71.10)]:
            r = self.client.post("/guia/equipos/", {"team_abbreviation": abreviatura,
                                                    "team_name": abreviatura, "lat": lat, "lon": lon})
            self.assertRedirects(r, "/guia/equipos/")
        self.assertContains(self.client.get("/guia/equipos/"), "/guia/liga/")

        r = self.client.post("/guia/liga/", {"nombre": "Liga", "equipos": [Equipo.objects.first().pk]})
        self.assertContains(r, "Elige al menos 2 equipos.")
        self.assertContains(r, 'aria-invalid="true"')
        r = self.client.post("/guia/liga/", {"nombre": "Liga", "equipos": list(
            Equipo.objects.values_list("pk", flat=True))})
        self.assertRedirects(r, "/guia/torneo/")

        r = self.client.post("/guia/torneo/", {"nombre": "Torneo", "fecha_inicio": "2026-04-01",
                                               "fecha_fin": "2026-03-01", "numero_de_juegos": 2,
                                               "numero_de_series": 3})
        self.assertContains(r, "El último día debe ser igual o posterior al primero.")
        r = self.client.post("/guia/torneo/", {"nombre": "Torneo", "fecha_inicio": "2026-04-01",
                                               "fecha_fin": "2026-09-30", "numero_de_juegos": 2,
                                               "numero_de_series": 3})
        self.assertRedirects(r, "/guia/configuracion/")
        torneo = Torneo.objects.get()
        self.assertEqual(list(torneo.liga.all()), [Liga.objects.get()])

        r = self.client.post("/guia/configuracion/", {
            "nombre": "Prueba", "poblacion": 10, "generaciones": 1,
            "probabilidad_de_cruce": 1.5, "probabilidad_de_reproduccion": 0.2})
        self.assertContains(r, "Debe estar entre 0 y 1.")
        r = self.client.post("/guia/configuracion/", {
            "nombre": "Prueba", "poblacion": 10, "generaciones": 1,
            "probabilidad_de_cruce": 0.8, "probabilidad_de_reproduccion": 0.2})
        self.assertRedirects(r, "/guia/calendario/")
        configuracion = Configuracion.objects.get()
        self.assertEqual(configuracion.calendario.torneo, torneo)

        r = self.client.post("/guia/calendario/")
        self.assertRedirects(r, "/guia/calendario/")
        juegos = Juego.objects.filter(serie__calendario=configuracion.calendario).count()
        self.assertGreater(juegos, 0)
        r = self.client.get("/guia/calendario/")
        self.assertContains(r, f"?configuracion={configuracion.pk}")
        self.assertEqual(r.context["total_juegos"], juegos)

        # Volver a generar reemplaza los juegos, no los duplica
        self.client.post("/guia/calendario/")
        self.assertEqual(Juego.objects.filter(serie__calendario=configuracion.calendario).count(), juegos)

    def test_paso_desconocido_vuelve_al_inicio(self):
        self.assertRedirects(self.client.get("/guia/otro/"), "/guia/")
