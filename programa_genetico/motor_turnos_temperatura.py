"""PG que aprende cuándo aceptar cambios peores (la "temperatura" del recocido).

En ``motor_turnos_pg`` las primitivas solo aceptan cambios que mejoran, y la PG
casi empata con movimientos al azar. El recocido simulado gana porque a veces
acepta cambios peores para salir de óptimos locales. Aquí la PG diseña esa
regla.

Individuo: un árbol ``TEMPERATURA(avance, aceptados)`` que devuelve cuántos km
de empeoramiento se toleran en cada paso:

- ``avance``: de 0 (inicio) a 1 (fin de la corrida).
- ``aceptados``: fracción reciente de movimientos aceptados.
- Primitivas: suma, resta, multiplicación, división protegida, mín, máx,
  ``decae(x) = e^(-x)``.
- Constantes al azar: una escala en km (0 a 30 000) y un número de 0 a 1.

Un cambio que empeora ``d`` km se acepta con probabilidad ``e^(-d / T)``, igual
que en el recocido. El recocido hecho a mano usa T = 20 000 · (50 / 20 000)^avance.

Entrenamiento: cada árbol corre un recocido corto (``pasos_entrenamiento``) en
calendarios de práctica; su fitness es el costo final (reglas rotas primero,
luego km). Prueba: el mejor árbol corre un recocido completo en calendarios
nuevos y se compara contra el recocido hecho a mano con el mismo esfuerzo.

No depende de Django.
"""

from __future__ import annotations

import math
import multiprocessing
import operator
import random
from dataclasses import dataclass, field
from typing import Callable, Optional

from deap import base, creator, gp, tools

from programa_genetico.motor_turnos import CalendarioTurnos, haversine_km, recocido, series_mlb_2023

PESO_REGLA = 20_000.0


def div_protegida(a, b):
    return a / b if abs(b) > 1e-9 else 1.0


def decae(x):
    return math.exp(-min(max(x, -50.0), 50.0))


def _escala_km():
    return round(random.uniform(0, 30_000), 0)


def _fraccion():
    return round(random.random(), 3)


def crear_pset() -> gp.PrimitiveSet:
    ps = gp.PrimitiveSet("TEMPERATURA", 2)
    ps.renameArguments(ARG0="avance", ARG1="aceptados")
    ps.addPrimitive(operator.add, 2, name="suma")
    ps.addPrimitive(operator.sub, 2, name="resta")
    ps.addPrimitive(operator.mul, 2, name="por")
    ps.addPrimitive(div_protegida, 2, name="entre")
    ps.addPrimitive(min, 2, name="minimo")
    ps.addPrimitive(max, 2, name="maximo")
    ps.addPrimitive(decae, 1)
    ps.addEphemeralConstant("escala_km", _escala_km)
    ps.addEphemeralConstant("fraccion", _fraccion)
    return ps


PSET = crear_pset()

if not hasattr(creator, "FitnessTemperatura"):
    creator.create("FitnessTemperatura", base.Fitness, weights=(-1.0,))
if not hasattr(creator, "IndividuoTemperatura"):
    creator.create("IndividuoTemperatura", gp.PrimitiveTree, fitness=creator.FitnessTemperatura)


def temperatura_a_mano(avance: float, _aceptados: float) -> float:
    return 20_000.0 * (50.0 / 20_000.0) ** avance


def nuevo_calendario(coords: dict, semilla: int) -> tuple:
    """Calendario inicial sin choques y el generador que sigue después de construirlo."""
    rng = random.Random(semilla)
    cal = CalendarioTurnos(series_mlb_2023(rng), sorted(coords),
                           lambda a, b: haversine_km(coords[a], coords[b]))
    if not cal.construir(rng):
        raise RuntimeError("No se pudo construir un calendario inicial sin choques.")
    return cal, rng


def correr_con_regla(coords: dict, semilla: int, pasos: int, temperatura: Callable) -> tuple:
    cal, rng = nuevo_calendario(coords, semilla)
    pen, km = recocido(cal, rng, pasos=pasos, temperatura=temperatura)
    return pen, km, cal


# ----------------------------------------------------------------------
# Evaluación en paralelo
# ----------------------------------------------------------------------
_TRABAJO: dict = {}


def _iniciar(coords, semillas, pasos):
    _TRABAJO.update(coords=coords, semillas=semillas, pasos=pasos)


def _evaluar_texto(texto: str) -> float:
    regla = gp.compile(gp.PrimitiveTree.from_string(texto, PSET), PSET)
    total = 0.0
    for s in _TRABAJO["semillas"]:
        pen, km, _ = correr_con_regla(_TRABAJO["coords"], s, _TRABAJO["pasos"], regla)
        total += PESO_REGLA * pen + km
    return total / len(_TRABAJO["semillas"])


@dataclass
class Resultado:
    mejor: gp.PrimitiveTree
    fitness: float
    historial: list = field(default_factory=list)


def evolucionar(coords: dict, semillas_practica=(100, 101), pasos_entrenamiento: int = 30_000,
                generaciones: int = 12, tam_poblacion: int = 24, prob_cruce: float = 0.8,
                prob_mutacion: float = 0.3, tam_torneo: int = 3, elite: int = 2, altura_max: int = 7,
                procesos: int = 4, semilla: Optional[int] = None,
                on_generation: Optional[Callable[[int, float, str], None]] = None) -> Resultado:
    random.seed(semilla)
    tb = base.Toolbox()
    tb.register("expr", gp.genHalfAndHalf, pset=PSET, min_=1, max_=3)
    tb.register("individual", tools.initIterate, creator.IndividuoTemperatura, tb.expr)
    tb.register("expr_mut", gp.genFull, min_=0, max_=2)
    pop = [tb.individual() for _ in range(tam_poblacion)]
    memo: dict = {}
    historial = []
    ctx = multiprocessing.get_context("fork")
    with ctx.Pool(procesos, initializer=_iniciar,
                  initargs=(coords, tuple(semillas_practica), pasos_entrenamiento)) as pool:
        for gen in range(generaciones):
            pendientes = sorted({str(i) for i in pop if str(i) not in memo})
            for texto, valor in zip(pendientes, pool.map(_evaluar_texto, pendientes)):
                memo[texto] = valor
            for ind in pop:
                ind.fitness.values = (memo[str(ind)],)
            mejor = min(pop, key=lambda i: i.fitness.values[0])
            historial.append((gen, mejor.fitness.values[0], str(mejor)))
            if on_generation is not None:
                on_generation(gen, mejor.fitness.values[0], str(mejor))
            if gen == generaciones - 1:
                break
            elites = [tb.clone(i) for i in sorted(pop, key=lambda i: i.fitness.values[0])[:elite]]
            hijos = [tb.clone(i) for i in tools.selTournament(pop, tam_poblacion - elite, tournsize=tam_torneo)]
            for i in range(1, len(hijos), 2):
                if random.random() < prob_cruce:
                    a, b = gp.cxOnePoint(tb.clone(hijos[i - 1]), tb.clone(hijos[i]))
                    if a.height <= altura_max:
                        hijos[i - 1] = a
                    if b.height <= altura_max:
                        hijos[i] = b
            for i, ind in enumerate(hijos):
                if random.random() < prob_mutacion:
                    nuevo, = gp.mutUniform(tb.clone(ind), expr=tb.expr_mut, pset=PSET)
                    if nuevo.height <= altura_max:
                        hijos[i] = nuevo
            pop = elites + hijos
    mejor = min(pop, key=lambda i: i.fitness.values[0])
    return Resultado(mejor=mejor, fitness=mejor.fitness.values[0], historial=historial)
