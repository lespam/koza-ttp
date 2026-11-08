"""Motor de PG por bloques: cada ADF es un calendario.

Idea de Les Dickinson (nov. 2026): aprovechar la jerarquía de MLB
(2 ligas x 3 divisiones x 5 equipos) en el árbol de sintaxis.

Arquitectura de un individuo (al estilo de Koza, con forma fija):

    cal = ensamblar(ADF_liga(L1, L2), ADF_division(D1, D2), ADF_interliga(I1, I2))
    para cada serie s:  cal = ADF_serie(cal, s)
    cal = AJUSTE(cal)

- L1, L2, D1, D2, I1, I2 son **bloques aleatorios** de "todos contra todos".
  Cada bloque ya cumple la regla de su nivel (cada pareja juega una vez).
- ``ADF_liga``, ``ADF_division`` y ``ADF_interliga`` reciben 2 bloques y
  devuelven un bloque: los transforman (orden de series, localía) y los pegan
  o eligen. Ninguna primitiva cambia quién juega contra quién, así que las
  reglas por nivel se cumplen **por construcción**.
- ``ADF_serie(cal, serie)`` es una receta que se aplica a cada serie de la
  temporada completa, y ``AJUSTE`` es el árbol final.

Cuentas por equipo (series de 3 días):
- 2 vueltas de liga (15 series cada una): 2 series contra cada rival de su
  liga, incluidos los de su división, y 1 serie interliga (el que descansa).
- 2 vueltas de división (5 series cada una): 2 series más contra cada rival
  de división y 1 serie interliga (el que descansa).
- 1 bloque interliga de 14 series.
Total 30 + 10 + 14 = 54 series = 162 juegos: 48 de división, 60 del resto de
la liga y 54 interliga.
"""

from __future__ import annotations

import functools
import random
from dataclasses import dataclass, field
from typing import Callable, Optional

from deap import base, creator, gp, tools

from programa_genetico.motor_series import (
    Calendario, Instancia, Posicion, ReglaNivel, Serie, _pos_al_azar, _serie_al_azar,
    crear_primitivas_si_mejora, intercambiar_series, invertir_localia, otra_pos, siguiente,
)

# Reglas que el diseño por bloques cumple por construcción.
REGLAS_BLOQUES = {
    "division": ReglaNivel(juegos=48, tolerancia=0, min_series=4, max_series=4),
    "liga": ReglaNivel(juegos=60, tolerancia=0, min_series=2, max_series=2),
    "interliga": ReglaNivel(juegos=54, tolerancia=0, min_series=0, max_series=5),
}


# ----------------------------------------------------------------------
# Bloques aleatorios de "todos contra todos"
# ----------------------------------------------------------------------
def todos_contra_todos(equipos: list, rng: random.Random) -> list:
    """Rondas de todos contra todos (método del círculo).

    Devuelve una lista de rondas; cada ronda es (parejas, equipo_que_descansa).
    Con número impar de equipos, en cada ronda descansa uno distinto.
    """
    lista = list(equipos)
    rng.shuffle(lista)
    if len(lista) % 2:
        lista.append(None)
    n = len(lista)
    rondas = []
    for _ in range(n - 1):
        parejas, descansa = [], None
        for i in range(n // 2):
            a, b = lista[i], lista[n - 1 - i]
            if a is None or b is None:
                descansa = b if a is None else a
            else:
                parejas.append((a, b) if rng.random() < 0.5 else (b, a))
        rondas.append((parejas, descansa))
        lista = [lista[0]] + [lista[-1]] + lista[1:-1]
    rng.shuffle(rondas)
    return rondas


def _juntar_descansos(al: list, nl: list, rng: random.Random) -> list:
    """Empareja a los que descansan en una liga con los de la otra."""
    nl = list(nl)
    rng.shuffle(nl)
    return [(a, b) if rng.random() < 0.5 else (b, a) for a, b in zip(al, nl)]


@dataclass
class Jerarquia:
    divisiones: dict  # {"AL Este": [...], ...}

    @property
    def ligas(self) -> dict:
        ligas: dict = {}
        for nombre, equipos in self.divisiones.items():
            ligas.setdefault(nombre.split()[0], []).extend(equipos)
        return ligas

    def bloque_liga(self, rng: random.Random) -> Calendario:
        """15 series: cada pareja de cada liga juega una vez."""
        (_, al), (_, nl) = sorted(self.ligas.items())
        r_al, r_nl = todos_contra_todos(al, rng), todos_contra_todos(nl, rng)
        series = []
        for (p_al, d_al), (p_nl, d_nl) in zip(r_al, r_nl):
            series.append(tuple(p_al + p_nl + _juntar_descansos([d_al], [d_nl], rng)))
        return Calendario(series)

    def bloque_division(self, rng: random.Random) -> Calendario:
        """5 series: cada pareja de cada división juega una vez."""
        por_liga: dict = {}
        for nombre, equipos in sorted(self.divisiones.items()):
            por_liga.setdefault(nombre.split()[0], []).append(todos_contra_todos(equipos, rng))
        (_, divs_al), (_, divs_nl) = sorted(por_liga.items())
        series = []
        for r in range(len(divs_al[0])):
            parejas, desc_al, desc_nl = [], [], []
            for d in divs_al:
                parejas += d[r][0]
                desc_al.append(d[r][1])
            for d in divs_nl:
                parejas += d[r][0]
                desc_nl.append(d[r][1])
            series.append(tuple(parejas + _juntar_descansos(desc_al, desc_nl, rng)))
        return Calendario(series)

    def bloque_interliga(self, rng: random.Random, rondas: int = 14) -> Calendario:
        """``rondas`` series: cada equipo AL contra un NL distinto en cada serie."""
        (_, al), (_, nl) = sorted(self.ligas.items())
        al, nl = list(al), list(nl)
        rng.shuffle(al)
        rng.shuffle(nl)
        desplazamientos = rng.sample(range(len(nl)), rondas)
        series = []
        for d in desplazamientos:
            series.append(tuple((a, nl[(i + d) % len(nl)]) if rng.random() < 0.5
                                else (nl[(i + d) % len(nl)], a) for i, a in enumerate(al)))
        return Calendario(series)


# ----------------------------------------------------------------------
# Tipos de bloque (solo para que DEAP no mezcle niveles)
# ----------------------------------------------------------------------
class BloqueLiga(Calendario):
    pass


class BloqueDivision(Calendario):
    pass


class BloqueInterliga(Calendario):
    pass


class LigaDoble(Calendario):
    pass


class DivisionDoble(Calendario):
    pass


def concatenar(a, b):
    return Calendario(tuple(a) + tuple(b))


def crear_primitivas_de_bloque(instancia: Instancia):
    """Transformaciones dentro de un bloque. El costo es el viaje del bloque solo."""

    def invertir_si_mejora_bloque(bloque, s, p):
        otro = invertir_localia(bloque, s, p)
        return otro if instancia.viaje_total(otro) < instancia.viaje_total(bloque) else bloque

    def intercambiar_si_mejora_bloque(bloque, s1, s2):
        otro = intercambiar_series(bloque, s1, s2)
        return otro if instancia.viaje_total(otro) < instancia.viaje_total(bloque) else bloque

    def elegir_mejor(a, b):
        return a if instancia.viaje_total(a) <= instancia.viaje_total(b) else b

    return invertir_si_mejora_bloque, intercambiar_si_mejora_bloque, elegir_mejor


def _pset_bloque(nombre, tipo, tipo_salida, combinar, prims_bloque, ns, np_):
    inv_si, inter_si, _ = prims_bloque
    ps = gp.PrimitiveSetTyped(nombre, [tipo, tipo], tipo_salida)
    ps.addPrimitive(combinar, [tipo, tipo], tipo_salida, name=f"{combinar.__name__}_{nombre}")
    ps.addPrimitive(invertir_localia, [tipo, Serie, Posicion], tipo, name=f"invertir_localia_{nombre}")
    ps.addPrimitive(intercambiar_series, [tipo, Serie, Serie], tipo, name=f"intercambiar_series_{nombre}")
    ps.addPrimitive(inv_si, [tipo, Serie, Posicion], tipo, name=f"invertir_si_mejora_{nombre}")
    ps.addPrimitive(inter_si, [tipo, Serie, Serie], tipo, name=f"intercambiar_si_mejora_{nombre}")
    ps.addPrimitive(siguiente, [Serie], Serie)
    ps.addPrimitive(otra_pos, [Posicion], Posicion)
    ps.addEphemeralConstant(f"serie_{ns}", functools.partial(_serie_al_azar, ns), Serie)
    ps.addEphemeralConstant(f"pos_{np_}", functools.partial(_pos_al_azar, np_), Posicion)
    ps.renameArguments(ARG0="a", ARG1="b")
    return ps


def crear_psets_bloques(instancia: Instancia):
    """(ADF_liga, ADF_division, ADF_interliga, ADF_serie, AJUSTE)."""
    np_ = instancia.parejas_por_serie
    prims_bloque = crear_primitivas_de_bloque(instancia)
    _, _, elegir_mejor = prims_bloque
    elegir_mejor.__name__ = "elegir_mejor"

    adf_liga = _pset_bloque("ADF_liga", BloqueLiga, LigaDoble, concatenar, prims_bloque, 15, np_)
    adf_div = _pset_bloque("ADF_division", BloqueDivision, DivisionDoble, concatenar, prims_bloque, 5, np_)
    adf_inter = _pset_bloque("ADF_interliga", BloqueInterliga, BloqueInterliga, elegir_mejor,
                             prims_bloque, 14, np_)

    _, invertir_si_mejora, intercambiar_si_mejora = crear_primitivas_si_mejora(instancia)
    ns = instancia.num_series
    serie = gp.PrimitiveSetTyped("ADF_serie", [Calendario, Serie], Calendario)
    ajuste = gp.PrimitiveSetTyped("AJUSTE", [Calendario], Calendario)
    for ps in (serie, ajuste):
        ps.addPrimitive(invertir_localia, [Calendario, Serie, Posicion], Calendario)
        ps.addPrimitive(intercambiar_series, [Calendario, Serie, Serie], Calendario)
        ps.addPrimitive(invertir_si_mejora, [Calendario, Serie, Posicion], Calendario,
                        name="invertir_si_mejora")
        ps.addPrimitive(intercambiar_si_mejora, [Calendario, Serie, Serie], Calendario,
                        name="intercambiar_si_mejora")
        ps.addPrimitive(siguiente, [Serie], Serie)
        ps.addPrimitive(otra_pos, [Posicion], Posicion)
        ps.addEphemeralConstant(f"pos_{np_}", functools.partial(_pos_al_azar, np_), Posicion)
    ajuste.addEphemeralConstant(f"serie_{ns}", functools.partial(_serie_al_azar, ns), Serie)
    serie.renameArguments(ARG0="cal", ARG1="serie")
    ajuste.renameArguments(ARG0="cal")
    return adf_liga, adf_div, adf_inter, serie, ajuste


if not hasattr(creator, "FitnessBloques"):
    creator.create("FitnessBloques", base.Fitness, weights=(1.0, -1.0))
if not hasattr(creator, "IndividuoBloques"):
    creator.create("IndividuoBloques", list, fitness=creator.FitnessBloques)


@dataclass
class Bloques:
    """Los bloques aleatorios de una corrida (terminales L1, L2, D1, D2, I1, I2)."""
    liga: tuple
    division: tuple
    interliga: tuple

    @classmethod
    def aleatorios(cls, jerarquia: Jerarquia, rng: random.Random) -> "Bloques":
        return cls(liga=(BloqueLiga(jerarquia.bloque_liga(rng)), BloqueLiga(jerarquia.bloque_liga(rng))),
                   division=(BloqueDivision(jerarquia.bloque_division(rng)),
                             BloqueDivision(jerarquia.bloque_division(rng))),
                   interliga=(BloqueInterliga(jerarquia.bloque_interliga(rng)),
                              BloqueInterliga(jerarquia.bloque_interliga(rng))))

    def ensamblar_simple(self) -> Calendario:
        """Calendario sin evolucionar: L1+L2+D1+D2+I1."""
        return Calendario(tuple(self.liga[0]) + tuple(self.liga[1]) + tuple(self.division[0])
                          + tuple(self.division[1]) + tuple(self.interliga[0]))


@dataclass
class Resultado:
    mejor_calendario: Calendario
    mejor_individuo: list
    fitness: tuple
    fitness_inicial: tuple
    generacion_del_mejor: int
    evaluaciones: int
    historial: list = field(default_factory=list)


def evolucionar(instancia: Instancia,
                bloques: Bloques,
                generaciones: int = 50,
                tam_poblacion: int = 100,
                prob_cruce: float = 0.8,
                prob_mutacion: float = 0.2,
                tam_torneo: int = 3,
                elite: int = 1,
                altura_max: int = 8,
                semilla: Optional[int] = None,
                on_generation: Optional[Callable[[int, float, float], None]] = None,
                ) -> Resultado:
    random.seed(semilla)
    psets = crear_psets_bloques(instancia)
    exprs = [functools.partial(gp.genHalfAndHalf, pset=ps, min_=1, max_=3) for ps in psets]
    arboles = [functools.partial(tools.initIterate, gp.PrimitiveTree, e) for e in exprs]
    tb = base.Toolbox()
    tb.register("individual", tools.initCycle, creator.IndividuoBloques, arboles, n=1)

    evaluaciones = 0

    def ejecutar(ind):
        f_liga, f_div, f_inter, f_serie, f_ajuste = (gp.compile(t, ps) for t, ps in zip(ind, psets))
        cal = concatenar(concatenar(f_liga(*bloques.liga), f_div(*bloques.division)),
                         f_inter(*bloques.interliga))
        cal = Calendario(cal)
        for s in range(len(cal)):
            cal = f_serie(cal, Serie(s))
        return f_ajuste(cal)

    def evaluar(ind):
        nonlocal evaluaciones
        evaluaciones += 1
        return instancia.evaluar(ejecutar(ind))

    def ajustar(ind, nuevo):
        return nuevo if all(t.height <= altura_max for t in nuevo) else ind

    clave = lambda fit: (fit[0], -fit[1])
    pop = [tb.individual() for _ in range(tam_poblacion)]
    for ind in pop:
        ind.fitness.values = evaluar(ind)
    mejor = tb.clone(max(pop, key=lambda i: clave(i.fitness.values)))
    gen_mejor, historial = 0, []

    def registrar(gen):
        historial.append((gen, *mejor.fitness.values))
        if on_generation is not None:
            on_generation(gen, *mejor.fitness.values)

    registrar(0)
    for gen in range(1, generaciones):
        elites = [tb.clone(i) for i in sorted(pop, key=lambda i: clave(i.fitness.values), reverse=True)[:elite]]
        hijos = [tb.clone(i) for i in tools.selTournament(pop, tam_poblacion - elite, tournsize=tam_torneo)]
        for i in range(1, len(hijos), 2):
            if random.random() < prob_cruce:
                a, b = tb.clone(hijos[i - 1]), tb.clone(hijos[i])
                for t in range(len(a)):
                    a[t], b[t] = gp.cxOnePoint(a[t], b[t])
                hijos[i - 1], hijos[i] = ajustar(hijos[i - 1], a), ajustar(hijos[i], b)
                del hijos[i - 1].fitness.values, hijos[i].fitness.values
        for i, ind in enumerate(hijos):
            if random.random() < prob_mutacion:
                nuevo = tb.clone(ind)
                t = random.randrange(len(nuevo))
                expr = exprs[t]
                nuevo[t], = gp.mutUniform(nuevo[t], expr=lambda pset, type_: expr(type_=type_), pset=psets[t])
                hijos[i] = ajustar(ind, nuevo)
                del hijos[i].fitness.values
        for ind in hijos:
            if not ind.fitness.valid:
                ind.fitness.values = evaluar(ind)
        pop = elites + hijos
        mejor_gen = max(pop, key=lambda i: clave(i.fitness.values))
        if clave(mejor_gen.fitness.values) > clave(mejor.fitness.values):
            mejor, gen_mejor = tb.clone(mejor_gen), gen
        registrar(gen)

    return Resultado(mejor_calendario=ejecutar(mejor), mejor_individuo=mejor,
                     fitness=tuple(mejor.fitness.values),
                     fitness_inicial=instancia.evaluar(bloques.ensamblar_simple()),
                     generacion_del_mejor=gen_mejor, evaluaciones=evaluaciones, historial=historial)


def busqueda_aleatoria(instancia: Instancia, jerarquia: Jerarquia, evaluaciones: int,
                       rng: random.Random) -> tuple:
    """Línea base en el mismo espacio: bloques aleatorios pegados en orden aleatorio."""
    mejor, mejor_fit = None, None
    for _ in range(evaluaciones):
        series = list(Bloques.aleatorios(jerarquia, rng).ensamblar_simple())
        rng.shuffle(series)
        cal = Calendario(series)
        fit = instancia.evaluar(cal)
        if mejor_fit is None or (fit[0], -fit[1]) > (mejor_fit[0], -mejor_fit[1]):
            mejor, mejor_fit = cal, fit
    return mejor, mejor_fit
