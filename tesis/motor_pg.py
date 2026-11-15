"""El motor PG por dentro: el árbol de la regla aprendida y cómo evolucionó.

La PG del algoritmo por turnos (programa_genetico/motor_turnos_temperatura.py)
diseña la regla de "temperatura": cuántos km de empeoramiento acepta el
recocido en cada paso. Esta página dibuja ese árbol y repite una evolución real
generación por generación.

Las cifras están en static/data/evolucion_pg.json. Se generaron con
/mnt/project-files/motor_pg/generaciones/grabar_evolucion.py (30 equipos de las
Grandes Ligas, 2 calendarios de práctica). Guardan solo árboles y costos.
"""
import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

ARCHIVO = Path(settings.BASE_DIR) / "static" / "data" / "evolucion_pg.json"


@lru_cache(maxsize=1)
def cargar():
    with open(ARCHIVO, encoding="utf-8") as f:
        return json.load(f)


def textos():
    """Textos que motor_pg.js escribe dentro de los dibujos."""
    return {
        # Nombres de las piezas del árbol (las primitivas y terminales de la PG)
        "piezas": {
            "suma": _("suma"), "resta": _("resta"), "por": _("por"), "entre": _("entre"),
            "minimo": _("mínimo"), "maximo": _("máximo"), "decae": _("decae"),
            "avance": _("avance"), "aceptados": _("aceptados"),
        },
        "arbol": _("Árbol de la regla: cada caja es una operación y las hojas son datos o números"),
        "grafica": _("Costo de cada árbol en cada generación"),
        "eje_x": _("Generación"),
        "eje_y": _("Costo (millones de km)"),
        "mejor": _("El mejor árbol de cada generación"),
        "mediana": _("La mitad de los árboles está por debajo de esta línea"),
        "a_mano": _("Regla hecha a mano (referencia)"),
        "arbolito": _("Un árbol de la población"),
        "fuera": _("Árboles con costo más alto que el borde de arriba"),
        "estado": _("Generación {gen} de {total}. Mejor costo: {mejor} millones de km. Mediana: {mediana}."),
        "origenes": _("De dónde vienen sus {n} árboles: {lista}."),
        "origen": {
            "elite": _("{n} de élite (los 2 mejores pasan igual)"),
            "cruce": _("{n} de cruce"),
            "mutacion": _("{n} de mutación"),
            "seleccion": _("{n} copiados por torneo"),
            "nuevo": _("{n} nuevos al azar"),
        },
        "vino_de": {
            "elite": _("Es de élite: ya era el mejor y pasó igual."),
            "cruce": _("Nació de un cruce entre dos árboles."),
            "mutacion": _("Nació de una mutación."),
            "seleccion": _("Es la copia de un árbol que ganó un torneo."),
            "nuevo": _("Es un árbol nuevo, hecho al azar."),
        },
        "mejor_de": _("Mejor árbol de la generación {gen}: {nodos} piezas."),
        "lugar_de": _("Árbol en el lugar {pos} de la generación {gen}: {nodos} piezas."),
        "lugar": _("Lugar {pos} de {n} en la generación {gen}"),
        "opcion": _("Lugar {pos}: {costo} millones de km"),
        "costo_de": _("Costo: {costo} millones de km."),
        "padre": _("Su padre fue el árbol en el lugar {a} de la generación {gen}."),
        "padres": _("Sus padres fueron los árboles en los lugares {a} y {b} de la generación {gen}."),
        "genealogia": _("Árbol genealógico: una fila por generación y una línea de cada árbol a sus padres"),
        "gen_corta": _("Gen {gen}"),
        "clase0": _("Mejor que la regla hecha a mano"),
        "clase1": _("Hasta 1 % peor"),
        "clase2": _("Hasta 5 % peor"),
        "clase3": _("Más de 5 % peor"),
        "linaje": _("La familia del árbol elegido"),
        "reproducir": _("Reproducir"),
        "pausar": _("Pausar"),
    }


class MotorPGView(TemplateView):
    template_name = "tesis/motor_pg.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        datos = cargar()
        gens = datos["generaciones"]
        ctx.update({
            "seccion": "demo",
            "datos": datos,
            "total": len(gens),
            "ultima": len(gens) - 1,
            "inicio": round(gens[0]["mejor"] / 1e6, 3),
            "fin": round(gens[-1]["mejor"] / 1e6, 3),
            "a_mano": round(datos["a_mano"] / 1e6, 3),
            "filas": [{"gen": g["generacion"], "mejor": round(g["mejor"] / 1e6, 3),
                       "mediana": round(g["mediana"] / 1e6, 3), "arbol": g["individuos"][0]["arbol"]} for g in gens],
            "motor_pg_datos": {
                "regla": datos["regla_aprendida"], "a_mano": datos["a_mano"],
                "generaciones": [{"mejor": g["mejor"], "mediana": g["mediana"],
                                  "individuos": [[i["arbol"], i["costo"], i["origen"], i.get("id"), i.get("padres", [])]
                                                 for i in g["individuos"]]}
                                 for g in gens],
                "textos": textos(),
            },
        })
        return ctx
