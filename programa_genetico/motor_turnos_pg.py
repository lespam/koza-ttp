"""Programación genética sobre el calendario por turnos (series de 2, 3 y 4 juegos).

Usa el modelo de ``motor_turnos`` y convierte sus movimientos en primitivas
de árboles de PG, al estilo de los otros motores: el árbol es un programa que
transforma un calendario válido.

Individuo (forma fija, como ``motor_bloques``)::

    para cada turno t:  cal = ADF_turno(cal, t)
    cal = AJUSTE(cal)

Primitivas (todas dejan un calendario sin choques y solo aceptan el cambio si
mejora: primero menos reglas rotas, luego menos km):

- ``kempe_si_mejora(cal, a, b, e)``: cadena de Kempe entre los turnos a y b
  que pasa por el equipo e.
- ``kempe_tolerante(cal, a, b, e)``: acepta la cadena aunque empeore un poco
  (hasta 5000 km, sin romper reglas), para salir de óptimos locales.
- ``mejor_kempe(cal, a, e)``: prueba la cadena de e con todos los turnos y
  aplica la mejor.
- ``turnos_si_mejora(cal, a, b)``: intercambia dos turnos completos.
- ``invertir_si_mejora(cal, a, e)``: cambia la localía de la serie de e en el
  turno a (sola o junto con otra serie de la misma pareja).
- Turnos: ``siguiente``, ``anterior``, ``mas(t, d)`` (``d`` es un desfase).
- Equipos: constante al azar, ``mas_viaja(cal)`` (el equipo que más viaja) y
  ``rival_en(cal, t, e)``.

Flujo evolutivo: torneo, elitismo, cruce y mutación de un punto por árbol.
Todos los individuos de una generación parten del mismo calendario. Al final
de cada generación, la mejor receta se aplica ``repeticiones`` veces más y ese
calendario es el punto de partida de la siguiente. Así la PG busca **recetas
de mejora** y el resultado se acumula. Se guarda el mejor calendario visto.

Línea base justa: ``busqueda_aleatoria`` aplica movimientos al azar (los
mismos tres tipos, solo si mejoran) con el mismo número de movimientos.

No depende de Django.
"""

from __future__ import annotations

import functools
import random
from dataclasses import dataclass, field
from typing import Callable, Optional

from deap import base, creator, gp, tools

from programa_genetico.motor_turnos import CalendarioTurnos


class Cal:
    """Calendario con su costo en caché. Las primitivas lo cambian en su lugar."""

    def __init__(self, cal: CalendarioTurnos, peso_regla: float = 20_000.0, peso_dia: float = 200_000.0):
        self.cal = cal
        self.peso_regla = peso_regla
        self.peso_dia = peso_dia
        self.movimientos = 0
        self.recalcular()

    def recalcular(self):
        self.dur = self.cal.duraciones()
        self.cache = [self.cal.costo_equipo(i, self.dur) for i in range(len(self.cal.equipos))]
        self.total = self._total(self.dur, self.cache)

    def _total(self, dur, cache):
        return (self.peso_dia * max(0, sum(dur) - self.cal.dias)
                + self.peso_regla * sum(p for p, _ in cache) + sum(k for _, k in cache))

    def probar(self, aplicar: Callable, deshacer: Callable, afectados: set, cambia_dur: bool) -> float:
        """Aplica un movimiento, devuelve la mejora (>0 si baja el costo) y lo deshace."""
        self.movimientos += 1
        aplicar()
        dur = self.cal.duraciones() if cambia_dur else self.dur
        if dur != self.dur:
            afectados = range(len(self.cal.equipos))
        cache = list(self.cache)
        for i in afectados:
            cache[i] = self.cal.costo_equipo(i, dur)
        nuevo = self._total(dur, cache)
        deshacer()
        return self.total - nuevo

    def aceptar(self, aplicar: Callable):
        aplicar()
        self.recalcular()

    def evaluar(self) -> tuple:
        return self.cal.evaluar()

    def estado(self):
        return self.cal.copia_estado()

    def copia(self) -> "Cal":
        otro = Cal.__new__(Cal)
        otro.__dict__.update(self.__dict__)
        otro.cal = CalendarioTurnos.__new__(CalendarioTurnos)
        otro.cal.__dict__.update(self.cal.__dict__)
        otro.cal.restaurar(self.cal.copia_estado())
        otro.dur, otro.cache = list(self.dur), list(self.cache)
        otro.movimientos = 0
        return otro


class Turno(int):
    pass


class Equipo(int):
    pass


class Desfase(int):
    pass


# ----------------------------------------------------------------------
# Movimientos (aplicar / deshacer) sobre CalendarioTurnos
# ----------------------------------------------------------------------
def _mov_kempe(c: CalendarioTurnos, a: int, b: int, e: int):
    if a == b:
        return None
    series = c.cadena(e, a, b)
    if not series or not c.se_puede_cambiar(series, a, b):
        return None
    hacer = lambda: c.cambiar_turnos(series, a, b)
    afectados = {x for k in series for x in (c.local[k], c.visita[k])}
    return hacer, hacer, afectados, True


def _mov_turnos(c: CalendarioTurnos, a: int, b: int):
    if a == b:
        return None
    series = [k for k, t in enumerate(c.turno) if t in (a, b)]
    if not c.se_puede_cambiar(series, a, b):
        return None
    hacer = lambda: c.cambiar_turnos(series, a, b)
    return hacer, hacer, set(range(len(c.equipos))), False


def _movs_invertir(c: CalendarioTurnos, a: int, e: int):
    k = c.en[e][a]
    if k < 0:
        return []
    u, v = c.local[k], c.visita[k]
    grupos = [[k]] + [[k, x] for x in c.pareja[frozenset((u, v))] if c.local[x] == v]
    return [((lambda g=g: c.invertir(g)), (lambda g=g: c.invertir(g)), {u, v}, False) for g in grupos]


def _probar_y_aceptar(cal: Cal, movs) -> Cal:
    mejor, mejora = None, 0.0
    for m in movs:
        if m is None:
            continue
        aplicar, deshacer, afectados, cambia = m
        d = cal.probar(aplicar, deshacer, afectados, cambia)
        if d > mejora:
            mejor, mejora = aplicar, d
    if mejor is not None:
        cal.aceptar(mejor)
    return cal


# ----------------------------------------------------------------------
# Primitivas
# ----------------------------------------------------------------------
def kempe_si_mejora(cal, a, b, e):
    c = cal.cal
    return _probar_y_aceptar(cal, [_mov_kempe(c, a % c.T, b % c.T, e % len(c.equipos))])


TOLERANCIA_KM = 5_000.0


def kempe_tolerante(cal, a, b, e):
    """Acepta la cadena aunque empeore hasta TOLERANCIA_KM, sin romper más reglas.

    Sirve para salir de un óptimo local, como el recocido simulado.
    """
    c = cal.cal
    m = _mov_kempe(c, a % c.T, b % c.T, e % len(c.equipos))
    if m is None:
        return cal
    aplicar, deshacer, afectados, cambia = m
    if cal.probar(aplicar, deshacer, afectados, cambia) > -TOLERANCIA_KM:
        cal.aceptar(aplicar)
    return cal


def mejor_kempe(cal, a, e):
    c = cal.cal
    a, e = a % c.T, e % len(c.equipos)
    return _probar_y_aceptar(cal, [_mov_kempe(c, a, b, e) for b in range(c.T)])


def turnos_si_mejora(cal, a, b):
    c = cal.cal
    return _probar_y_aceptar(cal, [_mov_turnos(c, a % c.T, b % c.T)])


def invertir_si_mejora(cal, a, e):
    c = cal.cal
    return _probar_y_aceptar(cal, _movs_invertir(c, a % c.T, e % len(c.equipos)))


def siguiente(t):
    return Turno(t + 1)


def anterior(t):
    return Turno(t - 1)


def mas(t, d):
    return Turno(t + d)


def otro_desfase(d):
    return Desfase(d + 1)


def mas_viaja(cal):
    return Equipo(max(range(len(cal.cache)), key=lambda i: cal.cache[i][1] + 20_000 * cal.cache[i][0]))


def rival_en(cal, t, e):
    c = cal.cal
    k = c.en[e % len(c.equipos)][t % c.T]
    if k < 0:
        return Equipo(e)
    return Equipo(c.visita[k] if c.local[k] == e % len(c.equipos) else c.local[k])


def _equipo_al_azar(n):
    return Equipo(random.randrange(n))


def _turno_al_azar(n):
    return Turno(random.randrange(n))


def _desfase_al_azar(n):
    return Desfase(random.randrange(1, n))


def crear_psets(turnos: int, equipos: int):
    """(ADF_turno, AJUSTE)."""
    adf = gp.PrimitiveSetTyped("ADF_turno", [Cal, Turno], Cal)
    ajuste = gp.PrimitiveSetTyped("AJUSTE", [Cal], Cal)
    for ps in (adf, ajuste):
        ps.addPrimitive(kempe_si_mejora, [Cal, Turno, Turno, Equipo], Cal)
        ps.addPrimitive(mejor_kempe, [Cal, Turno, Equipo], Cal)
        ps.addPrimitive(kempe_tolerante, [Cal, Turno, Turno, Equipo], Cal)
        ps.addPrimitive(turnos_si_mejora, [Cal, Turno, Turno], Cal)
        ps.addPrimitive(invertir_si_mejora, [Cal, Turno, Equipo], Cal)
        ps.addPrimitive(siguiente, [Turno], Turno)
        ps.addPrimitive(anterior, [Turno], Turno)
        ps.addPrimitive(mas, [Turno, Desfase], Turno)
        ps.addPrimitive(otro_desfase, [Desfase], Desfase)
        ps.addPrimitive(mas_viaja, [Cal], Equipo)
        ps.addPrimitive(rival_en, [Cal, Turno, Equipo], Equipo)
        ps.addEphemeralConstant(f"equipo_{equipos}", functools.partial(_equipo_al_azar, equipos), Equipo)
        ps.addEphemeralConstant(f"desfase_{turnos}", functools.partial(_desfase_al_azar, turnos), Desfase)
    ajuste.addEphemeralConstant(f"turno_{turnos}", functools.partial(_turno_al_azar, turnos), Turno)
    adf.renameArguments(ARG0="cal", ARG1="turno")
    ajuste.renameArguments(ARG0="cal")
    return adf, ajuste


if not hasattr(creator, "FitnessTurnos"):
    creator.create("FitnessTurnos", base.Fitness, weights=(-1.0, -1.0))
if not hasattr(creator, "IndividuoTurnos"):
    creator.create("IndividuoTurnos", list, fitness=creator.FitnessTurnos)


@dataclass
class Resultado:
    mejor_calendario: CalendarioTurnos
    mejor_individuo: list
    fitness: tuple
    fitness_inicial: tuple
    movimientos: int
    historial: list = field(default_factory=list)


def evolucionar(cal0: CalendarioTurnos, generaciones: int = 60, tam_poblacion: int = 40,
                prob_cruce: float = 0.8, prob_mutacion: float = 0.3, tam_torneo: int = 3,
                elite: int = 2, altura_max: int = 6, repeticiones: int = 20, semilla: Optional[int] = None,
                on_generation: Optional[Callable[[int, int, float], None]] = None) -> Resultado:
    random.seed(semilla)
    psets = crear_psets(cal0.T, len(cal0.equipos))
    exprs = [functools.partial(gp.genHalfAndHalf, pset=ps, min_=1, max_=3) for ps in psets]
    arboles = [functools.partial(tools.initIterate, gp.PrimitiveTree, e) for e in exprs]
    tb = base.Toolbox()
    tb.register("individual", tools.initCycle, creator.IndividuoTurnos, arboles, n=1)

    actual = Cal(cal0)
    mejor_visto = actual
    inicial = actual.evaluar()
    movimientos = 0

    def ejecutar(ind, punto: Cal) -> Cal:
        f_turno, f_ajuste = (gp.compile(t, ps) for t, ps in zip(ind, psets))
        cal = punto.copia()
        for t in range(cal.cal.T):
            cal = f_turno(cal, Turno(t))
        return f_ajuste(cal)

    def evaluar(ind, punto: Cal):
        nonlocal movimientos
        res = ejecutar(ind, punto)
        movimientos += res.movimientos
        ind.resultado = res
        return res.total, 0.0

    def ajustar(ind, nuevo):
        return nuevo if all(t.height <= altura_max for t in nuevo) else ind

    pop = [tb.individual() for _ in range(tam_poblacion)]
    historial = []
    for gen in range(generaciones):
        for ind in pop:
            ind.fitness.values = evaluar(ind, actual)
        mejor = min(pop, key=lambda i: i.fitness.values[0])
        # Explotación: la mejor receta se aplica varias veces seguidas.
        candidato = mejor.resultado
        for _ in range(repeticiones):
            siguiente_cal = ejecutar(mejor, candidato)
            movimientos += siguiente_cal.movimientos
            candidato = siguiente_cal
            if candidato.total < mejor_visto.total:
                mejor_visto = candidato
        if mejor.resultado.total < mejor_visto.total:
            mejor_visto = mejor.resultado
        actual = candidato if candidato.total < actual.total + TOLERANCIA_KM * 4 else mejor_visto
        pen, km = mejor_visto.evaluar()
        historial.append((gen, pen, km))
        if on_generation is not None:
            on_generation(gen, pen, km)
        if gen == generaciones - 1:
            break
        elites = [tb.clone(i) for i in sorted(pop, key=lambda i: i.fitness.values[0])[:elite]]
        hijos = [tb.clone(i) for i in tools.selTournament(pop, tam_poblacion - elite, tournsize=tam_torneo)]
        for i in range(1, len(hijos), 2):
            if random.random() < prob_cruce:
                a, b = tb.clone(hijos[i - 1]), tb.clone(hijos[i])
                for t in range(len(a)):
                    a[t], b[t] = gp.cxOnePoint(a[t], b[t])
                hijos[i - 1], hijos[i] = ajustar(hijos[i - 1], a), ajustar(hijos[i], b)
        for i, ind in enumerate(hijos):
            if random.random() < prob_mutacion:
                nuevo = tb.clone(ind)
                t = random.randrange(len(nuevo))
                expr = exprs[t]
                nuevo[t], = gp.mutUniform(nuevo[t], expr=lambda pset, type_: expr(type_=type_), pset=psets[t])
                hijos[i] = ajustar(ind, nuevo)
        pop = elites + hijos

    return Resultado(mejor_calendario=mejor_visto.cal, mejor_individuo=mejor, fitness=mejor_visto.evaluar(),
                     fitness_inicial=inicial, movimientos=movimientos, historial=historial)


def busqueda_aleatoria(cal0: CalendarioTurnos, movimientos: int, rng: random.Random) -> tuple:
    """Movimientos al azar (Kempe, turnos, localía) que solo se aceptan si mejoran."""
    cal = Cal(cal0)
    c = cal.cal
    n, T = len(c.equipos), c.T
    while cal.movimientos < movimientos:
        r = rng.random()
        a, b, e = rng.randrange(T), rng.randrange(T), rng.randrange(n)
        if r < 0.6:
            movs = [_mov_kempe(c, a, b, e)]
        elif r < 0.75:
            movs = [_mov_turnos(c, a, b)]
        else:
            movs = _movs_invertir(c, a, e)
            movs = [rng.choice(movs)] if movs else []
        if not movs or movs[0] is None:
            cal.movimientos += 1
            continue
        _probar_y_aceptar(cal, movs)
    return c, cal.evaluar()
