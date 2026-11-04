"""Motor de programación genética por series, con ADF.

Este módulo NO reemplaza al motor de la tesis (`programagenetico.py`).
Las dos versiones conviven para poder compararlas con la misma instancia.

Modelo
------
- Un **calendario** es una tupla de **series**. Una serie es un bloque de
  ``dias_por_serie`` fechas seguidas en el que se repiten las mismas parejas.
  Cada serie es un emparejamiento perfecto: cada equipo juega una vez por día.
- Por eso, si hay ``S`` series de ``L`` días, **cada equipo juega exactamente
  S * L juegos** (por ejemplo, 54 series de 3 días = 162 juegos).
- Un **individuo** es un programa (árbol) que transforma un calendario válido
  ``cal0``. Todas las primitivas que reciben un calendario devuelven otro
  calendario válido, así el número de juegos por equipo nunca cambia.
- El **ADF** ``ADF0(cal, serie)`` es una receta que actúa sobre una serie y que
  el árbol principal puede reutilizar en varias series.

Tipos: ``Calendario``, ``Serie`` (número de serie) y ``Posicion`` (número de
pareja dentro de la serie). Los números se toman módulo el tamaño real.

Fitness (igual que la tesis, para comparar):
- C1 = -suma(|juegos del equipo - juegos esperados|). Cero es lo mejor.
- C2 = suma de la distancia entre los rivales de cada juego (km).
Orden lexicográfico: primero C1, luego C2.

No depende de Django.
"""

from __future__ import annotations

import functools
import operator
import random
from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

from deap import base, creator, gp, tools


# ----------------------------------------------------------------------
# Tipos
# ----------------------------------------------------------------------
class Calendario(tuple):
    """Tupla de series; cada serie es una tupla de parejas (local, visitante)."""


class Serie(int):
    pass


class Posicion(int):
    pass


# ----------------------------------------------------------------------
# Instancia y generación 0
# ----------------------------------------------------------------------
@dataclass
class Instancia:
    equipos: Sequence[str]
    distancia: Callable[[str, str], float]
    num_series: int = 54
    dias_por_serie: int = 3

    def __post_init__(self):
        if len(self.equipos) % 2:
            raise ValueError("El número de equipos debe ser par.")
        self.equipos = list(self.equipos)
        self._dist = {}
        for a in self.equipos:
            for b in self.equipos:
                if a != b:
                    self._dist[(a, b)] = float(self.distancia(a, b))

    @property
    def juegos_por_equipo(self) -> int:
        return self.num_series * self.dias_por_serie

    @property
    def parejas_por_serie(self) -> int:
        return len(self.equipos) // 2

    def calendario_aleatorio(self, rng: random.Random) -> Calendario:
        """Generación 0: cada serie es un emparejamiento al azar."""
        series = []
        for _ in range(self.num_series):
            lista = list(self.equipos)
            rng.shuffle(lista)
            series.append(tuple((lista[i], lista[i + 1]) for i in range(0, len(lista), 2)))
        return Calendario(series)

    def evaluar(self, cal: Calendario) -> tuple:
        conteo = {e: 0 for e in self.equipos}
        total = 0.0
        L = self.dias_por_serie
        for serie in cal:
            for a, b in serie:
                conteo[a] += L
                conteo[b] += L
                total += L * self._dist[(a, b)]
        c1 = -sum(abs(n - self.juegos_por_equipo) for n in conteo.values())
        return c1, total

    def juegos_en_casa(self, cal: Calendario) -> dict:
        casa = {e: 0 for e in self.equipos}
        for serie in cal:
            for a, _ in serie:
                casa[a] += self.dias_por_serie
        return casa


# ----------------------------------------------------------------------
# Primitivas (todas conservan un calendario válido)
# ----------------------------------------------------------------------
def _cruzar(cal, s, p, q, modo):
    cal = list(cal)
    s %= len(cal)
    serie = list(cal[s])
    if len(serie) < 2:
        return Calendario(cal)
    p %= len(serie)
    q %= len(serie)
    if p == q:
        q = (q + 1) % len(serie)
    (a, b), (c, d) = serie[p], serie[q]
    if modo == 0:
        serie[p], serie[q] = (a, c), (b, d)
    else:
        serie[p], serie[q] = (a, d), (b, c)
    cal[s] = tuple(serie)
    return Calendario(cal)


def cruzar_rivales_a(cal, s, p, q):
    """A-B y C-D pasan a A-C y B-D en toda la serie."""
    return _cruzar(cal, s, p, q, 0)


def cruzar_rivales_b(cal, s, p, q):
    """A-B y C-D pasan a A-D y B-C en toda la serie."""
    return _cruzar(cal, s, p, q, 1)


def invertir_localia(cal, s, p):
    """El visitante de la pareja p pasa a ser local en toda la serie."""
    cal = list(cal)
    s %= len(cal)
    serie = list(cal[s])
    p %= len(serie)
    a, b = serie[p]
    serie[p] = (b, a)
    cal[s] = tuple(serie)
    return Calendario(cal)


def siguiente(s):
    return Serie(s + 1)


def otra_pos(p):
    return Posicion(p + 1)


def _serie_al_azar(n):
    return Serie(random.randrange(n))


def _pos_al_azar(n):
    return Posicion(random.randrange(n))


# ----------------------------------------------------------------------
# Conjuntos de primitivas (árbol principal + ADF0)
# ----------------------------------------------------------------------
def crear_cruzar_si_mejora(instancia: Instancia):
    """Primitiva con conocimiento del dominio: de las tres formas de emparejar
    a los cuatro equipos de las parejas p y q, deja la de menor distancia."""
    dist = instancia._dist

    def cruzar_si_mejora(cal, s, p, q):
        opciones = [cal, _cruzar(cal, s, p, q, 0), _cruzar(cal, s, p, q, 1)]
        s %= len(cal)

        def costo(c):
            serie = c[s]
            n = len(serie)
            pp, qq = p % n, q % n
            if pp == qq:
                qq = (qq + 1) % n
            return dist[serie[pp]] + dist[serie[qq]]

        return min(opciones, key=costo)

    return cruzar_si_mejora


def crear_psets(instancia: Instancia):
    ns, np_ = instancia.num_series, instancia.parejas_por_serie
    cruzar_si_mejora = crear_cruzar_si_mejora(instancia)

    adf = gp.PrimitiveSetTyped("ADF0", [Calendario, Serie], Calendario)
    main = gp.PrimitiveSetTyped("MAIN", [Calendario], Calendario)
    for ps in (adf, main):
        ps.addPrimitive(cruzar_rivales_a, [Calendario, Serie, Posicion, Posicion], Calendario)
        ps.addPrimitive(cruzar_rivales_b, [Calendario, Serie, Posicion, Posicion], Calendario)
        ps.addPrimitive(invertir_localia, [Calendario, Serie, Posicion], Calendario)
        ps.addPrimitive(cruzar_si_mejora, [Calendario, Serie, Posicion, Posicion], Calendario,
                        name="cruzar_si_mejora")
        ps.addPrimitive(siguiente, [Serie], Serie)
        ps.addPrimitive(otra_pos, [Posicion], Posicion)
        ps.addEphemeralConstant(f"pos_{np_}", functools.partial(_pos_al_azar, np_), Posicion)
    main.addEphemeralConstant(f"serie_{ns}", functools.partial(_serie_al_azar, ns), Serie)
    adf.renameArguments(ARG0="cal", ARG1="serie")
    main.renameArguments(ARG0="cal0")
    main.addADF(adf)
    return main, adf


if not hasattr(creator, "FitnessSeries"):
    creator.create("FitnessSeries", base.Fitness, weights=(1.0, -1.0))
if not hasattr(creator, "IndividuoSeries"):
    creator.create("IndividuoSeries", list, fitness=creator.FitnessSeries)


# ----------------------------------------------------------------------
# Flujo evolutivo
# ----------------------------------------------------------------------
@dataclass
class Resultado:
    mejor_calendario: Calendario
    mejor_individuo: list
    fitness: tuple
    fitness_cal0: tuple
    generacion_del_mejor: int
    evaluaciones: int
    historial: list = field(default_factory=list)  # (gen, mejor_c1, mejor_c2)


def evolucionar(instancia: Instancia,
                cal0: Calendario,
                generaciones: int = 50,
                tam_poblacion: int = 100,
                prob_cruce: float = 0.8,
                prob_mutacion: float = 0.2,
                tam_torneo: int = 3,
                elite: int = 1,
                altura_max: int = 10,
                iterar_adf: bool = True,
                semilla: Optional[int] = None,
                on_generation: Optional[Callable[[int, float, float], None]] = None,
                ) -> Resultado:
    """Evoluciona programas que transforman ``cal0`` y devuelve el mejor calendario.

    ``on_generation(gen, mejor_c1, mejor_c2)`` se llama al final de cada
    generación, para mostrar el avance en la web.
    """
    random.seed(semilla)  # DEAP usa el módulo random global
    main, adf = crear_psets(instancia)
    psets = (main, adf)

    tb = base.Toolbox()
    tb.register("expr_main", gp.genHalfAndHalf, pset=main, min_=1, max_=4)
    tb.register("expr_adf", gp.genHalfAndHalf, pset=adf, min_=1, max_=3)
    tb.register("MAIN", tools.initIterate, gp.PrimitiveTree, tb.expr_main)
    tb.register("ADF", tools.initIterate, gp.PrimitiveTree, tb.expr_adf)
    tb.register("individual", tools.initCycle, creator.IndividuoSeries, [tb.MAIN, tb.ADF], n=1)

    evaluaciones = 0

    def ejecutar(ind):
        """Aplica el individuo a cal0.

        Con ``iterar_adf``, primero se aplica la receta ADF0 a cada serie
        (una rama de iteración fija, al estilo de Koza) y luego el árbol principal.
        """
        cal = cal0
        if iterar_adf:
            receta = gp.compile(ind[1], adf)
            for s in range(len(cal)):
                cal = receta(cal, Serie(s))
        return gp.compileADF(ind, psets)(cal)

    def evaluar(ind):
        nonlocal evaluaciones
        evaluaciones += 1
        return instancia.evaluar(ejecutar(ind))

    def ajustar(ind, nuevo):
        """Rechaza árboles más altos que altura_max (control de crecimiento)."""
        return nuevo if all(t.height <= altura_max for t in nuevo) else ind

    pop = [tb.individual() for _ in range(tam_poblacion)]
    for ind in pop:
        ind.fitness.values = evaluar(ind)

    fitness_cal0 = instancia.evaluar(cal0)
    clave = lambda fit: (fit[0], -fit[1])
    mejor = tb.clone(max(pop, key=lambda i: clave(i.fitness.values)))
    gen_mejor = 0
    historial = []

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
                for t in range(len(a)):  # cruce árbol por árbol (MAIN con MAIN, ADF con ADF)
                    a[t], b[t] = gp.cxOnePoint(a[t], b[t])
                hijos[i - 1] = ajustar(hijos[i - 1], a)
                hijos[i] = ajustar(hijos[i], b)
                del hijos[i - 1].fitness.values, hijos[i].fitness.values

        for i, ind in enumerate(hijos):
            if random.random() < prob_mutacion:
                nuevo = tb.clone(ind)
                t = random.randrange(len(nuevo))
                pset = psets[t]
                expr = tb.expr_main if t == 0 else tb.expr_adf
                nuevo[t], = gp.mutUniform(nuevo[t], expr=lambda pset, type_: expr(type_=type_), pset=pset)
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

    cal = ejecutar(mejor)
    return Resultado(mejor_calendario=cal, mejor_individuo=mejor, fitness=tuple(mejor.fitness.values),
                     fitness_cal0=fitness_cal0, generacion_del_mejor=gen_mejor,
                     evaluaciones=evaluaciones, historial=historial)


def busqueda_aleatoria(instancia: Instancia, evaluaciones: int, rng: random.Random) -> tuple:
    """Línea base: el mejor de ``evaluaciones`` calendarios al azar."""
    mejor, mejor_fit = None, None
    for _ in range(evaluaciones):
        cal = instancia.calendario_aleatorio(rng)
        fit = instancia.evaluar(cal)
        if mejor_fit is None or (fit[0], -fit[1]) > (mejor_fit[0], -mejor_fit[1]):
            mejor, mejor_fit = cal, fit
    return mejor, mejor_fit
