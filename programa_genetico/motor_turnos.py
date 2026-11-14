"""Calendario por turnos con series de 2, 3 y 4 juegos y días libres.

Este módulo NO reemplaza a los otros motores. Quita la regla principal de
``motor_series`` y ``motor_bloques``: que los 30 equipos jueguen series de
3 días al mismo tiempo.

Modelo (como la temporada 2023 de MLB)
--------------------------------------
- Cada equipo juega **52 series**, 162 juegos, 81 en casa:
  - división: 13 juegos contra cada rival (series de 3, 3, 3 y 4);
  - resto de la liga: 6 o 7 juegos (3 + 3 o 3 + 4);
  - rival natural de interliga: 4 juegos (2 + 2);
  - los otros 14 de interliga: una serie de 3.
- La temporada se divide en ``turnos``. En cada turno, un equipo juega una
  serie o **descansa**. Todas las series de un turno empiezan el mismo día.
  Con ``semana=True`` (por defecto) los turnos alternan entre semana (4 días)
  y fin de semana (3 días), como MLB; las series de 4 juegos solo van entre
  semana. Quien juega una serie más corta que su turno tiene días libres.
  Con ``semana=False`` el turno dura lo que su serie más larga.
- Con 53 turnos y 52 series, cada equipo descansa un turno.

Reglas de realismo (las cumple el calendario oficial 2023)
----------------------------------------------------------
- Máximo 12 juegos seguidos en casa y 12 seguidos de visita.
- No jugar dos series seguidas contra el mismo rival.
- Máximo 20 días seguidos con juego (contrato colectivo de MLB).
- Temporada de 186 días como máximo (la oficial: 30 de marzo a 1 de octubre).
- Juegos en casa: 81 ± 3.

Las reglas rotas se cuentan en juegos (o días) y se restan primero; el viaje
solo decide entre calendarios que rompen lo mismo.

Viaje: igual que ``Instancia.viaje_total`` y que la medición del oficial.
Cada equipo sale de casa, va de estadio en estadio y regresa al final.

Búsqueda: recocido simulado con movimientos que siempre dejan un calendario
válido (ningún equipo juega dos series en el mismo turno):
- cadena de Kempe entre dos turnos,
- intercambiar dos turnos completos,
- invertir la localía de una serie o de dos series de la misma pareja.

No depende de Django.
"""

from __future__ import annotations

import datetime
import math
import random
from collections import defaultdict
from typing import Callable, Optional, Sequence

from programa_genetico.motor_series import MLB_DIVISIONES

# Rivales naturales de interliga en 2023 (AL -> NL).
RIVALES_2023 = {
    "BAL": "WAS", "BOS": "ATL", "NYA": "NYN", "TBA": "MIA", "TOR": "PHI",
    "CHA": "CHN", "CLE": "CIN", "DET": "PIT", "KCA": "SLN", "MIN": "MIL",
    "ANA": "LAN", "HOU": "COL", "OAK": "SFN", "SEA": "SDN", "TEX": "ARI",
}


def haversine_km(a: tuple, b: tuple) -> float:
    """Distancia en km entre dos (lat, lon). Radio 6371 km, como la medición del oficial."""
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


# ----------------------------------------------------------------------
# Series de la temporada
# ----------------------------------------------------------------------
def series_mlb_2023(rng: random.Random, divisiones: Optional[dict] = None,
                    rivales: Optional[dict] = None) -> list:
    """Series (local, visita, juegos) con la estructura de MLB 2023.

    Cada equipo queda con 52 series, 162 juegos y 81 en casa. El azar decide
    qué parejas de la liga juegan 7 juegos y quién recibe la serie de 4.
    """
    divisiones = divisiones or MLB_DIVISIONES
    rivales = rivales or RIVALES_2023
    series = []
    for equipos in divisiones.values():
        eq = list(equipos)
        rng.shuffle(eq)
        # Cada equipo recibe la serie de 4 contra 2 de sus 4 rivales de división.
        for i in range(5):
            for k in (1, 2):
                a, b = eq[i], eq[(i + k) % 5]
                series += [(a, b, 4), (b, a, 3), (a, b, 3), (b, a, 3)]
    for liga in ("AL", "NL"):
        divs = [list(e) for d, e in sorted(divisiones.items()) if d.startswith(liga)]
        for d in divs:
            rng.shuffle(d)
        for i in range(3):
            for j in range(i + 1, 3):
                x, y = divs[i], divs[j]
                for s in range(5):
                    for p in range(5):
                        a, b = x[p], y[(p + s) % 5]
                        if s == 0:
                            series += [(a, b, 4), (b, a, 3)]
                        elif s == 1:
                            series += [(b, a, 4), (a, b, 3)]
                        else:
                            series += [(a, b, 3), (b, a, 3)]
    al = [e for d, eqs in sorted(divisiones.items()) if d.startswith("AL") for e in eqs]
    nl = [rivales[a] for a in al]
    for a, b in zip(al, nl):
        series += [(a, b, 2), (b, a, 2)]
    desplazamientos = list(range(1, 15))
    rng.shuffle(desplazamientos)
    for k, s in enumerate(desplazamientos):
        for i, a in enumerate(al):
            b = nl[(i + s) % 15]
            series.append((a, b, 3) if k < 7 else (b, a, 3))
    return series


# ----------------------------------------------------------------------
# Calendario
# ----------------------------------------------------------------------
class CalendarioTurnos:
    """Asignación de cada serie a un turno, sin choques.

    ``en[e][t]`` es la serie que juega el equipo ``e`` en el turno ``t``
    (o -1 si descansa).
    """

    def __init__(self, series: Sequence[tuple], equipos: Sequence[str],
                 distancia: Callable[[str, str], float], turnos: int = 53, dias: int = 186,
                 max_seguidos: int = 12, max_dias_seguidos: int = 20, casa: int = 81,
                 tolerancia_casa: int = 3, semana: bool = True):
        self.equipos = list(equipos)
        self.idx = {e: i for i, e in enumerate(self.equipos)}
        self.series = list(series)
        self.T = turnos
        self.dias = dias
        # Semana como MLB: turnos largos (entre semana, 4 días) y cortos (fin de
        # semana, 3 días), alternados. Las series de 4 juegos solo van en turnos
        # largos. Así la temporada dura siempre lo mismo (53 turnos = 186 días).
        self.largo = [t % 2 == 0 for t in range(turnos)] if semana else None
        self.max_seguidos = max_seguidos
        self.max_dias_seguidos = max_dias_seguidos
        self.casa = casa
        self.tolerancia_casa = tolerancia_casa
        n = len(self.equipos)
        self.D = [[0.0 if a == b else float(distancia(a, b)) for b in self.equipos] for a in self.equipos]
        self.local = [self.idx[s[0]] for s in self.series]
        self.visita = [self.idx[s[1]] for s in self.series]
        self.juegos = [s[2] for s in self.series]
        self.turno = [-1] * len(self.series)
        self.en = [[-1] * turnos for _ in range(n)]
        self.de_equipo = [[] for _ in range(n)]
        self.pareja = defaultdict(list)
        for k in range(len(self.series)):
            self.de_equipo[self.local[k]].append(k)
            self.de_equipo[self.visita[k]].append(k)
            self.pareja[frozenset((self.local[k], self.visita[k]))].append(k)

    # ---------- construcción ----------
    def construir(self, rng: random.Random, pasos: int = 400_000) -> bool:
        """Turno inicial sin choques (min-conflictos). Devuelve False si no lo logra."""
        n, T = len(self.equipos), self.T
        ocupado = [[0] * T for _ in range(n)]
        validos = [[t for t in range(T) if self.permitido(k, t)] for k in range(len(self.series))]
        turno = [rng.choice(validos[k]) for k in range(len(self.series))]
        for k, t in enumerate(turno):
            ocupado[self.local[k]][t] += 1
            ocupado[self.visita[k]][t] += 1

        def choca(k):
            t = turno[k]
            return ocupado[self.local[k]][t] > 1 or ocupado[self.visita[k]][t] > 1

        malas = {k for k in range(len(self.series)) if choca(k)}
        for _ in range(pasos):
            if not malas:
                break
            k = rng.choice(tuple(malas))
            u, v, t0 = self.local[k], self.visita[k], turno[k]
            ocupado[u][t0] -= 1
            ocupado[v][t0] -= 1
            if rng.random() < 0.1:
                t = rng.choice(validos[k])
            else:
                mejor = min(ocupado[u][x] + ocupado[v][x] for x in validos[k])
                opciones = [x for x in validos[k] if ocupado[u][x] + ocupado[v][x] == mejor and x != t0]
                t = rng.choice(opciones) if opciones else t0
            ocupado[u][t] += 1
            ocupado[v][t] += 1
            turno[k] = t
            malas.discard(k)
            for e in (u, v):
                for kk in self.de_equipo[e]:
                    if turno[kk] in (t0, t):
                        (malas.add if choca(kk) else malas.discard)(kk)
        if malas:
            return False
        for k, t in enumerate(turno):
            self._poner(k, t)
        return True

    def _poner(self, k, t):
        self.turno[k] = t
        self.en[self.local[k]][t] = k
        self.en[self.visita[k]][t] = k

    # ---------- movimientos (todos dejan un calendario sin choques) ----------
    def cadena(self, equipo: int, a: int, b: int) -> list:
        """Series de la cadena de Kempe de los turnos a/b que pasa por ``equipo``."""
        cad, vistas = [], set()
        for primero in (a, b):
            x, t = equipo, primero
            while True:
                k = self.en[x][t]
                if k < 0 or k in vistas:
                    break
                vistas.add(k)
                cad.append(k)
                x = self.visita[k] if self.local[k] == x else self.local[k]
                t = b if t == a else a
        return cad

    def permitido(self, k: int, t: int) -> bool:
        """Una serie de 4 juegos solo cabe en un turno largo."""
        return self.largo is None or self.juegos[k] < 4 or self.largo[t]

    def se_puede_cambiar(self, series: list, a: int, b: int) -> bool:
        return all(self.permitido(k, b if self.turno[k] == a else a) for k in series)

    def cambiar_turnos(self, series: list, a: int, b: int) -> None:
        """Pasa cada serie de la lista del turno a al b y viceversa."""
        for k in series:
            t = self.turno[k]
            for e in (self.local[k], self.visita[k]):
                if self.en[e][t] == k:
                    self.en[e][t] = -1
        for k in series:
            self._poner(k, b if self.turno[k] == a else a)

    def invertir(self, series: list) -> None:
        for k in series:
            self.local[k], self.visita[k] = self.visita[k], self.local[k]

    # ---------- costo ----------
    def duraciones(self) -> list:
        if self.largo is not None:
            return [4 if largo else 3 for largo in self.largo]
        dur = [0] * self.T
        for k, t in enumerate(self.turno):
            dur[t] = max(dur[t], self.juegos[k])
        return dur

    def costo_equipo(self, i: int, dur: list) -> tuple:
        """(reglas rotas en juegos o días, km) de un equipo."""
        D = self.D
        lugar, km, pen = i, 0.0, 0
        lado_prev, racha = None, 0
        rival_prev = -1
        dias_seguidos = 0
        en_casa = 0
        for t in range(self.T):
            k = self.en[i][t]
            if k < 0:
                pen += max(0, dias_seguidos - self.max_dias_seguidos)
                dias_seguidos = 0
                continue
            h, L = self.local[k], self.juegos[k]
            km += D[lugar][h]
            lugar = h
            lado = h == i
            if lado:
                en_casa += L
            if lado == lado_prev:
                racha += L
            else:
                pen += max(0, racha - self.max_seguidos)
                lado_prev, racha = lado, L
            rival = self.visita[k] if lado else h
            if rival == rival_prev:
                pen += L
            rival_prev = rival
            dias_seguidos += L
            if dur[t] > L:
                pen += max(0, dias_seguidos - self.max_dias_seguidos)
                dias_seguidos = 0
        pen += max(0, racha - self.max_seguidos)
        pen += max(0, dias_seguidos - self.max_dias_seguidos)
        km += D[lugar][i]
        pen += max(0, abs(en_casa - self.casa) - self.tolerancia_casa)
        return pen, km

    def evaluar(self) -> tuple:
        """(reglas rotas, km). Cero reglas rotas es lo mejor."""
        dur = self.duraciones()
        pen = max(0, sum(dur) - self.dias)
        km = 0.0
        for i in range(len(self.equipos)):
            p, k = self.costo_equipo(i, dur)
            pen += p
            km += k
        return pen, km

    def copia_estado(self) -> tuple:
        return list(self.turno), [list(f) for f in self.en], list(self.local), list(self.visita)

    def restaurar(self, estado: tuple) -> None:
        turno, en, local, visita = estado
        self.turno, self.en, self.local, self.visita = list(turno), [list(f) for f in en], list(local), list(visita)

    # ---------- salida ----------
    def juegos_por_fecha(self, inicio: datetime.date = datetime.date(2023, 3, 30)) -> list:
        """[(fecha, local, visita)] ordenado por fecha."""
        dur = self.duraciones()
        empieza = [0] * self.T
        for t in range(1, self.T):
            empieza[t] = empieza[t - 1] + dur[t - 1]
        juegos = []
        for k, t in enumerate(self.turno):
            for d in range(self.juegos[k]):
                juegos.append((inicio + datetime.timedelta(days=empieza[t] + d),
                               self.equipos[self.local[k]], self.equipos[self.visita[k]]))
        return sorted(juegos)


# ----------------------------------------------------------------------
# Búsqueda
# ----------------------------------------------------------------------
def recocido(cal: CalendarioTurnos, rng: random.Random, pasos: int = 400_000,
             temp_inicial: float = 20_000.0, temp_final: float = 50.0,
             peso_regla: float = 20_000.0, peso_dia: float = 200_000.0,
             on_paso: Optional[Callable[[int, int, float], None]] = None, cada: int = 10_000,
             temperatura: Optional[Callable[[float, float], float]] = None) -> tuple:
    """Recocido simulado. Deja en ``cal`` el mejor calendario y devuelve (reglas rotas, km).

    ``temperatura(avance, aceptados)`` reemplaza el enfriamiento geométrico.
    ``avance`` va de 0 a 1 en la corrida y ``aceptados`` es la fracción
    reciente de movimientos aceptados. Así la PG puede diseñar la regla.
    """
    n, T = len(cal.equipos), cal.T
    dur = cal.duraciones()
    cache = [cal.costo_equipo(i, dur) for i in range(n)]

    def total(dur, cache):
        return (peso_dia * max(0, sum(dur) - cal.dias) + peso_regla * sum(p for p, _ in cache)
                + sum(k for _, k in cache))

    actual = total(dur, cache)
    mejor, mejor_estado = actual, cal.copia_estado()
    aceptados = 0.5
    for paso in range(pasos):
        if temperatura is None:
            temp = temp_inicial * (temp_final / temp_inicial) ** (paso / pasos)
        else:
            try:
                temp = float(temperatura(paso / pasos, aceptados))
            except (OverflowError, ValueError, ZeroDivisionError):
                temp = 0.0
            if not temp == temp:  # NaN
                temp = 0.0
        r = rng.random()
        if r < 0.75:
            a, b = rng.randrange(T), rng.randrange(T)
            if a == b:
                continue
            if r < 0.6:  # cadena de Kempe
                series = cal.cadena(rng.randrange(n), a, b)
                if not series or not cal.se_puede_cambiar(series, a, b):
                    continue
                afectados = {e for k in series for e in (cal.local[k], cal.visita[k])}
            else:  # dos turnos completos
                series = [k for k, t in enumerate(cal.turno) if t in (a, b)]
                if not cal.se_puede_cambiar(series, a, b):
                    continue
                afectados = set(range(n))
            cal.cambiar_turnos(series, a, b)
            deshacer = lambda s=series, a=a, b=b: cal.cambiar_turnos(s, a, b)
            nueva_dur = cal.duraciones()
        else:  # invertir localía (sola o con otra serie de la misma pareja)
            k = rng.randrange(len(cal.series))
            u, v = cal.local[k], cal.visita[k]
            otras = [x for x in cal.pareja[frozenset((u, v))] if cal.local[x] == v]
            series = [k] + ([rng.choice(otras)] if otras and rng.random() < 0.8 else [])
            cal.invertir(series)
            deshacer = lambda s=series: cal.invertir(s)
            afectados = {u, v}
            nueva_dur = dur
        if nueva_dur != dur:
            afectados = set(range(n))
        viejos = {i: cache[i] for i in afectados}
        for i in afectados:
            cache[i] = cal.costo_equipo(i, nueva_dur)
        nuevo = total(nueva_dur, cache)
        d = nuevo - actual
        acepta = d <= 0 or (temp > 0 and rng.random() < math.exp(-d / temp))
        aceptados = 0.99 * aceptados + 0.01 * acepta
        if acepta:
            actual, dur = nuevo, nueva_dur
            if actual < mejor:
                mejor, mejor_estado = actual, cal.copia_estado()
        else:
            deshacer()
            for i, c in viejos.items():
                cache[i] = c
        if on_paso is not None and paso % cada == 0:
            pen = max(0, sum(dur) - cal.dias) + sum(p for p, _ in cache)
            on_paso(paso, pen, sum(k for _, k in cache))
    cal.restaurar(mejor_estado)
    return cal.evaluar()


# ----------------------------------------------------------------------
# Medición independiente (la misma para el oficial y para el motor)
# ----------------------------------------------------------------------
def medir_juegos(juegos: list, coords: dict) -> dict:
    """Mide un calendario dado como [(fecha, local, visita)] ordenado por fecha.

    No usa nada del modelo por turnos, así sirve para comparar con el oficial.
    """
    ultimo, total = {}, 0.0
    por_equipo = defaultdict(list)
    for f, h, a in juegos:
        for e in (h, a):
            total += haversine_km(coords[ultimo.get(e, e)], coords[h])
            ultimo[e] = h
        por_equipo[h].append((f, a, True))
        por_equipo[a].append((f, h, False))
    for e, lugar in ultimo.items():
        total += haversine_km(coords[lugar], coords[e])
    fechas = sorted({f for f, _, _ in juegos})
    temporada = (fechas[-1] - fechas[0]).days + 1
    r = {"km": round(total), "temporada_dias": temporada, "juegos": set(), "en_casa": set(),
         "max_visita": 0, "max_casa": 0, "max_series_seguidas_mismo_rival": 0,
         "max_dias_seguidos": 0, "dias_libres": set()}
    for e, s in por_equipo.items():
        r["juegos"].add(len(s))
        r["en_casa"].add(sum(1 for x in s if x[2]))
        n, lado = 0, None
        for x in s:
            n = n + 1 if x[2] == lado else 1
            lado = x[2]
            clave = "max_casa" if lado else "max_visita"
            r[clave] = max(r[clave], n)
        series = []
        for x in s:
            if series and series[-1][0] == x[1] and series[-1][1] == x[2] and (x[0] - series[-1][2]).days <= 1:
                series[-1][2] = x[0]
            else:
                series.append([x[1], x[2], x[0]])
        m = 1
        for i in range(1, len(series)):
            m = m + 1 if series[i][0] == series[i - 1][0] else 1
            r["max_series_seguidas_mismo_rival"] = max(r["max_series_seguidas_mismo_rival"], m)
        dias = sorted({x[0] for x in s})
        n = 1
        for i in range(1, len(dias)):
            n = n + 1 if (dias[i] - dias[i - 1]).days == 1 else 1
            r["max_dias_seguidos"] = max(r["max_dias_seguidos"], n)
        r["dias_libres"].add(temporada - len(dias))
    for clave in ("juegos", "en_casa", "dias_libres"):
        r[clave] = (min(r[clave]), max(r[clave]))
    return r
