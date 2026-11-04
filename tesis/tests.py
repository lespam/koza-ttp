import datetime

from django.test import TestCase
from django.urls import URLPattern

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
    def test_base_vacia_muestra_como_empezar(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Crear una configuración")

    def test_elige_la_configuracion_con_juegos(self):
        Configuracion.objects.create(nombre="Sin calendario", poblacion=1, generaciones=1,
                                     probabilidad_de_cruce=0, probabilidad_de_reproduccion=0)
        configuracion = crear_datos_de_ejemplo()
        r = self.client.get("/")
        self.assertEqual(r.context["configuracion"], configuracion)
        self.assertEqual(len(r.context["juegos"]), 2)
        self.assertContains(r, f"?configuracion={configuracion.pk}&amp;ejecutar=true")

    def test_configuracion_inexistente_da_404(self):
        self.assertEqual(self.client.get("/?configuracion=999").status_code, 404)


class TodasLasPaginas(TestCase):
    """Cada página de la herramienta abre sin error. Se omiten las que borran datos
    o ejecutan el algoritmo genético (tardan y cambian la base)."""

    omitidas = ("delete", "generar", "programacion_genetica", "obtener_")

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
