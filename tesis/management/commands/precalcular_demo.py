"""Corre la demo de cada torneo ya configurado y guarda el resultado.

    python manage.py precalcular_demo                 # los 6 torneos
    python manage.py precalcular_demo --torneos kbo --pasos 400000

Escribe static/data/demo/<torneo>.json. Después: python manage.py generar_estatico.
"""
import time

from django.core.management.base import BaseCommand

from programa_genetico.demo_turnos import config_desde_dict, correr_demo
from tesis.demo_guardada import guardar
from tesis.torneos import TORNEOS, torneo


class Command(BaseCommand):
    help = "Calcula y guarda el resultado de la demo de cada torneo."

    def add_arguments(self, parser):
        parser.add_argument("--torneos", nargs="*", help="Claves de torneo (por omisión, todos).")
        parser.add_argument("--pasos", type=int, default=200_000,
                            help="Pasos de búsqueda (en local se pueden usar más que en la demo en vivo).")
        parser.add_argument("--semilla", type=int, default=1)

    def handle(self, *args, **opciones):
        for clave in opciones["torneos"] or [t["clave"] for t in TORNEOS]:
            t = torneo(clave)
            tabla = t["equipos"]()
            equipos = [c for c in t["marcados"] if c in tabla]
            config = config_desde_dict({**t["config"], "pasos": opciones["pasos"], "semilla": opciones["semilla"]})
            inicio = time.time()
            resultado = correr_demo({c: (tabla[c][2], tabla[c][3]) for c in equipos}, config)
            guardar(t["clave"], equipos, config, resultado)
            self.stdout.write(f"{t['clave']}: {resultado.km_final:,.0f} km "
                              f"(al azar {resultado.km_azar:,.0f}), reglas rotas {resultado.reglas_rotas}, "
                              f"{time.time() - inicio:.0f} s")
