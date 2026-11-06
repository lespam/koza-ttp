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

Fitness:
- C1 = -suma(|juegos del equipo - juegos esperados|). Cero es lo mejor.
- C2 depende de ``Instancia.fitness``:
  - "viaje" (por defecto): kilómetros que viajan todos los equipos en la
    temporada, serie por serie, empezando y terminando en casa.
  - "rivales": la definición de la tesis, la suma de la distancia entre los
    rivales de cada juego. Sirve para comparar con la tesis.
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
    """Tupla de series; cada serie es una tupla de parejas (local, visitante).

    Guarda en ``_info`` los conteos de series en casa por equipo y de series
    por pareja, para no recorrer todo el calendario en cada primitiva.
    """


def _pareja(a, b):
    return (a, b) if a <= b else (b, a)


def _info(cal: Calendario) -> tuple:
    """(series en casa por equipo, series por pareja), calculado una vez."""
    info = getattr(cal, "_info", None)
    if info is None:
        casa, pares = {}, {}
        for serie in cal:
            for a, b in serie:
                casa[a] = casa.get(a, 0) + 1
                k = _pareja(a, b)
                pares[k] = pares.get(k, 0) + 1
        info = (casa, pares)
        cal._info = info
    return info


def _reemplazar_serie(cal: Calendario, s: int, nueva: tuple) -> Calendario:
    """Devuelve un calendario con la serie s cambiada y los conteos al día."""
    lista = list(cal)
    vieja = lista[s]
    lista[s] = nueva
    nuevo = Calendario(lista)
    casa, pares = _info(cal)
    casa, pares = casa.copy(), pares.copy()
    for a, b in vieja:
        casa[a] -= 1
        pares[_pareja(a, b)] -= 1
    for a, b in nueva:
        casa[a] = casa.get(a, 0) + 1
        k = _pareja(a, b)
        pares[k] = pares.get(k, 0) + 1
    nuevo._info = (casa, pares)
    return nuevo


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
    fitness: str = "viaje"  # "viaje" (viaje real) o "rivales" (definición de la tesis)
    tolerancia_casa: Optional[int] = 3  # juegos en casa: mitad ± tolerancia (None = sin regla)
    max_series_pareja: Optional[int] = 4  # series por pareja en la temporada (None = sin regla)

    def __post_init__(self):
        if len(self.equipos) % 2:
            raise ValueError("El número de equipos debe ser par.")
        self.equipos = list(self.equipos)
        if self.fitness not in ("viaje", "rivales"):
            raise ValueError("fitness debe ser 'viaje' o 'rivales'.")
        self._dist = {}
        for a in self.equipos:
            for b in self.equipos:
                self._dist[(a, b)] = 0.0 if a == b else float(self.distancia(a, b))

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
        L = self.dias_por_serie
        for serie in cal:
            for a, b in serie:
                conteo[a] += L
                conteo[b] += L
        c1 = -sum(abs(n - self.juegos_por_equipo) for n in conteo.values())
        c1 -= self.penalizacion(cal)
        if self.fitness == "viaje":
            return c1, self.viaje_total(cal)
        total = sum(L * self._dist[par] for serie in cal for par in serie)
        return c1, total

    def exceso_casa(self, series_en_casa: int) -> int:
        """Juegos en casa fuera del rango mitad ± tolerancia."""
        if self.tolerancia_casa is None:
            return 0
        desvio = abs(series_en_casa * self.dias_por_serie - self.juegos_por_equipo / 2)
        return int(max(0, desvio - self.tolerancia_casa))

    def exceso_pareja(self, series: int) -> int:
        """Juegos de una pareja por encima del máximo de series."""
        if self.max_series_pareja is None:
            return 0
        return max(0, series - self.max_series_pareja) * self.dias_por_serie

    def penalizacion(self, cal: Calendario) -> int:
        """Juegos que rompen las reglas de localía y de rivales repetidos.

        Se resta de C1, así que un calendario que rompe una regla nunca le gana
        a uno que las cumple todas.
        """
        casa, pares = _info(cal)
        return (sum(self.exceso_casa(casa.get(e, 0)) for e in self.equipos)
                + sum(self.exceso_pareja(n) for n in pares.values()))

    def viaje_total(self, cal: Calendario) -> float:
        """Kilómetros que viajan todos los equipos en la temporada.

        Cada equipo empieza en su casa. En cada serie está en el estadio del
        local; entre series viaja del estadio anterior al siguiente. Al final
        regresa a casa. Dentro de una serie no hay viaje.
        """
        dist = self._dist
        donde = {e: e for e in self.equipos}
        total = 0.0
        for serie in cal:
            for local, visita in serie:
                total += dist[(donde[local], local)] + dist[(donde[visita], local)]
                donde[local] = local
                donde[visita] = local
        total += sum(dist[(lugar, e)] for e, lugar in donde.items())
        return total

    def series_contra_mismo_rival(self, cal: Calendario) -> int:
        """Máximo de series que una misma pareja juega en la temporada."""
        return max(_info(cal)[1].values())

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
    s %= len(cal)
    serie = list(cal[s])
    if len(serie) < 2:
        return cal
    p %= len(serie)
    q %= len(serie)
    if p == q:
        q = (q + 1) % len(serie)
    (a, b), (c, d) = serie[p], serie[q]
    if modo == 0:
        serie[p], serie[q] = (a, c), (b, d)
    else:
        serie[p], serie[q] = (a, d), (b, c)
    return _reemplazar_serie(cal, s, tuple(serie))


def cruzar_rivales_a(cal, s, p, q):
    """A-B y C-D pasan a A-C y B-D en toda la serie."""
    return _cruzar(cal, s, p, q, 0)


def cruzar_rivales_b(cal, s, p, q):
    """A-B y C-D pasan a A-D y B-C en toda la serie."""
    return _cruzar(cal, s, p, q, 1)


def invertir_localia(cal, s, p):
    """El visitante de la pareja p pasa a ser local en toda la serie."""
    s %= len(cal)
    serie = list(cal[s])
    p %= len(serie)
    a, b = serie[p]
    serie[p] = (b, a)
    return _reemplazar_serie(cal, s, tuple(serie))


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
def _lugar(cal, s, equipo):
    """Estadio donde está ``equipo`` durante la serie s (o su casa fuera de rango)."""
    if s < 0 or s >= len(cal):
        return equipo
    for local, visita in cal[s]:
        if equipo in (local, visita):
            return local
    return equipo


def _costo_local(instancia: Instancia, cal, s, equipos) -> tuple:
    """Costo de la serie s para ``equipos``: (reglas rotas, distancia).

    Primero cuenta los juegos que rompen las reglas de localía y de rivales
    repetidos entre esos equipos. Luego la distancia, según el fitness:
    - "rivales": distancia entre los rivales de las parejas de esos equipos.
    - "viaje": viaje de esos equipos para llegar a la serie s y salir de ella.
    """
    casa, pares = _info(cal)
    lista = sorted(equipos)
    rotas = sum(instancia.exceso_casa(casa.get(e, 0)) for e in lista)
    rotas += sum(instancia.exceso_pareja(pares.get((a, b), 0))
                 for i, a in enumerate(lista) for b in lista[i + 1:])
    dist = instancia._dist
    if instancia.fitness == "rivales":
        return rotas, sum(dist[par] for par in cal[s] if par[0] in equipos or par[1] in equipos)
    total = 0.0
    for e in equipos:
        aqui = _lugar(cal, s, e)
        total += dist[(_lugar(cal, s - 1, e), aqui)] + dist[(aqui, _lugar(cal, s + 1, e))]
    return rotas, total


def crear_primitivas_si_mejora(instancia: Instancia):
    """Primitivas con conocimiento del dominio: prueban un cambio en una serie
    y lo conservan solo si baja el costo local de los equipos afectados."""

    def _equipos(cal, s, *ps):
        serie = cal[s % len(cal)]
        return {e for p in ps for e in serie[p % len(serie)]}

    def cruzar_si_mejora(cal, s, p, q):
        """De las tres formas de emparejar a los cuatro equipos de p y q, deja la mejor."""
        opciones = [cal, _cruzar(cal, s, p, q, 0), _cruzar(cal, s, p, q, 1)]
        n = len(cal[s % len(cal)])
        qq = q % n if q % n != p % n else (q + 1) % n
        equipos = _equipos(cal, s, p, qq)
        return min(opciones, key=lambda c: _costo_local(instancia, c, s % len(cal), equipos))

    def invertir_si_mejora(cal, s, p):
        """Invierte la localía de la pareja p solo si baja el costo local."""
        equipos = _equipos(cal, s, p)
        otro = invertir_localia(cal, s, p)
        ss = s % len(cal)
        if _costo_local(instancia, otro, ss, equipos) < _costo_local(instancia, cal, ss, equipos):
            return otro
        return cal

    return cruzar_si_mejora, invertir_si_mejora


def crear_psets(instancia: Instancia):
    ns, np_ = instancia.num_series, instancia.parejas_por_serie
    cruzar_si_mejora, invertir_si_mejora = crear_primitivas_si_mejora(instancia)

    adf = gp.PrimitiveSetTyped("ADF0", [Calendario, Serie], Calendario)
    main = gp.PrimitiveSetTyped("MAIN", [Calendario], Calendario)
    for ps in (adf, main):
        ps.addPrimitive(cruzar_rivales_a, [Calendario, Serie, Posicion, Posicion], Calendario)
        ps.addPrimitive(cruzar_rivales_b, [Calendario, Serie, Posicion, Posicion], Calendario)
        ps.addPrimitive(invertir_localia, [Calendario, Serie, Posicion], Calendario)
        ps.addPrimitive(cruzar_si_mejora, [Calendario, Serie, Posicion, Posicion], Calendario,
                        name="cruzar_si_mejora")
        ps.addPrimitive(invertir_si_mejora, [Calendario, Serie, Posicion], Calendario,
                        name="invertir_si_mejora")
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
