"""El algoritmo más nuevo, listo para la demo (de 3 a 10 equipos).

Usa el modelo por turnos (``motor_turnos``) con la regla de temperatura que
aprendió la PG (``motor_turnos_temperatura``). Todo tiene valores ya elegidos:
la demo puede correr sin que la persona cambie nada.

Torneo genérico (no la estructura de MLB, que necesita 30 equipos):
- cada pareja juega ``series_por_pareja`` series de ``juegos_por_serie`` juegos,
  alternando quién es local;
- con número impar de equipos, en cada turno descansa al menos uno;
- hay turnos de sobra para que nadie juegue más de 20 días seguidos.

Reglas que se revisan: máximo 12 juegos seguidos en casa o de visita, no
repetir rival en series seguidas, máximo 20 días seguidos con juego y juegos
en casa cerca de la mitad.

De Django solo usa ``gettext_lazy`` para las etiquetas del formulario.

Uso::

    from programa_genetico.demo_turnos import ConfigDemo, correr_demo
    r = correr_demo({"NYA": (40.83, -73.93), ...}, ConfigDemo(pasos=20_000))
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable, Optional

from django.utils.translation import gettext_lazy as _
from deap import gp

from programa_genetico.motor_turnos import CalendarioTurnos, haversine_km, medir_juegos, recocido
from programa_genetico.motor_turnos_temperatura import PSET, REGLA_PG_APRENDIDA, temperatura_a_mano

MIN_EQUIPOS, MAX_EQUIPOS = 3, 10  # con 2 equipos siempre se repite rival


@dataclass
class ConfigDemo:
    juegos_por_serie: int = 3
    series_por_pareja: int = 2
    pasos: int = 20_000
    regla: str = "pg"  # "pg", "a_mano" o "solo_mejoras"
    semilla: int = 1


# Campos para armar el formulario. "grupo" separa el torneo del algoritmo.
CONFIG_CAMPOS = [
    {"clave": "juegos_por_serie", "grupo": "torneo", "tipo": "int", "valor_por_defecto": 3,
     "minimo": 2, "maximo": 4, "etiqueta": _("Juegos por serie"),
     "ayuda": _("Cuántos juegos seguidos se juegan en el mismo estadio.")},
    {"clave": "series_por_pareja", "grupo": "torneo", "tipo": "int", "valor_por_defecto": 2,
     "minimo": 1, "maximo": 4, "etiqueta": _("Series contra cada rival"),
     "ayuda": _("Con 2, cada equipo recibe una vez a cada rival y lo visita una vez.")},
    {"clave": "pasos", "grupo": "algoritmo", "tipo": "int", "valor_por_defecto": 20_000,
     "minimo": 1_000, "maximo": 100_000, "etiqueta": _("Pasos de búsqueda"),
     "ayuda": _("Cuántos cambios prueba el algoritmo. Más pasos tardan más y suelen dar menos viaje.")},
    {"clave": "regla", "grupo": "algoritmo", "tipo": "opciones", "valor_por_defecto": "pg",
     "opciones": [("pg", _("Regla aprendida por la programación genética")),
                  ("a_mano", _("Regla hecha a mano (recocido simulado)")),
                  ("solo_mejoras", _("Solo aceptar mejoras"))],
     "etiqueta": _("Cuándo aceptar un cambio peor"),
     "ayuda": _("Aceptar a veces un cambio peor ayuda a no quedarse atorado.")},
    {"clave": "semilla", "grupo": "algoritmo", "tipo": "int", "valor_por_defecto": 1,
     "minimo": 1, "maximo": 9_999, "etiqueta": _("Semilla"),
     "ayuda": _("Con la misma semilla, el resultado se repite igual.")},
]


@dataclass
class ResultadoDemo:
    juegos: list                 # [(fecha, local, visita)] ordenado por fecha
    km_azar: float               # calendario inicial al azar (sin optimizar)
    km_final: float
    reglas_rotas_azar: int
    reglas_rotas: int            # 0 = cumple todas
    revision: dict               # medición independiente (rachas, días, juegos en casa)
    historial: list = field(default_factory=list)  # [(paso, reglas rotas, km)]

    @property
    def km_inicial(self) -> float:
        return self.km_azar

    @property
    def mejora(self) -> float:
        """Fracción de viaje que se ahorró frente al calendario al azar."""
        return (self.km_azar - self.km_final) / self.km_azar if self.km_azar else 0.0


def config_desde_dict(datos: Optional[dict]) -> ConfigDemo:
    """Convierte lo que llega del formulario. Lo que falta o no es válido toma el valor por defecto."""
    datos = datos or {}
    valores = {}
    for campo in CONFIG_CAMPOS:
        clave, defecto = campo["clave"], campo["valor_por_defecto"]
        valor = datos.get(clave, defecto)
        if campo["tipo"] == "int":
            try:
                valor = int(valor)
            except (TypeError, ValueError):
                valor = defecto
            valor = min(max(valor, campo["minimo"]), campo["maximo"])
        elif valor not in {v for v, _etiqueta in campo["opciones"]}:
            valor = defecto
        valores[clave] = valor
    return ConfigDemo(**valores)


def series_demo(equipos: list, config: ConfigDemo) -> list:
    series = []
    for i, a in enumerate(equipos):
        for b in equipos[i + 1:]:
            for k in range(config.series_por_pareja):
                series.append((a, b, config.juegos_por_serie) if k % 2 == 0 else (b, a, config.juegos_por_serie))
    return series


def _turnos(n: int, config: ConfigDemo) -> int:
    por_equipo = (n - 1) * config.series_por_pareja
    minimos = math.ceil(n * por_equipo / (n - 1)) if n % 2 else por_equipo
    descansos = math.ceil(por_equipo * config.juegos_por_serie / 20) + 1
    return minimos + descansos


def _regla(nombre: str) -> Callable:
    if nombre == "a_mano":
        return temperatura_a_mano
    if nombre == "solo_mejoras":
        return lambda _avance, _aceptados: 0.0
    return gp.compile(gp.PrimitiveTree.from_string(REGLA_PG_APRENDIDA, PSET), PSET)


def correr_demo(coords: dict, config: Optional[ConfigDemo] = None,
                on_paso: Optional[Callable[[int, int, float], None]] = None) -> ResultadoDemo:
    """Arma y optimiza un calendario. ``coords`` = {equipo: (lat, lon)}, de 3 a 10 equipos."""
    config = config or ConfigDemo()
    equipos = list(coords)
    if not MIN_EQUIPOS <= len(equipos) <= MAX_EQUIPOS:
        raise ValueError(f"La demo usa de {MIN_EQUIPOS} a {MAX_EQUIPOS} equipos.")
    rng = random.Random(config.semilla)
    series = series_demo(equipos, config)
    juegos_equipo = (len(equipos) - 1) * config.series_por_pareja * config.juegos_por_serie
    T = _turnos(len(equipos), config)
    cal = CalendarioTurnos(series, equipos, lambda a, b: haversine_km(coords[a], coords[b]),
                           turnos=T, dias=T * config.juegos_por_serie, semana=False,
                           casa=juegos_equipo / 2, tolerancia_casa=config.juegos_por_serie)
    if not cal.construir(rng):
        raise RuntimeError("No se pudo armar un calendario inicial sin choques.")
    reglas_azar, km_azar = cal.evaluar()
    historial = [(0, reglas_azar, km_azar)]

    def aviso(paso, reglas, km):
        historial.append((paso, reglas, km))
        if on_paso is not None:
            on_paso(paso, reglas, km)

    reglas, km = recocido(cal, rng, pasos=config.pasos, temperatura=_regla(config.regla),
                          on_paso=aviso, cada=max(1, config.pasos // 50))
    historial.append((config.pasos, reglas, km))
    juegos = cal.juegos_por_fecha()
    revision = medir_juegos(juegos, coords)
    return ResultadoDemo(juegos=juegos, km_azar=km_azar, km_final=km, reglas_rotas_azar=int(round(reglas_azar)),
                         reglas_rotas=int(round(reglas)), revision=revision, historial=historial)


__all__ = ["CONFIG_CAMPOS", "ConfigDemo", "ResultadoDemo", "config_desde_dict", "correr_demo",
           "MIN_EQUIPOS", "MAX_EQUIPOS"]
