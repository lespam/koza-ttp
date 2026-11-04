"""Compara el motor por series contra la búsqueda aleatoria con el mismo presupuesto.

Uso (desde la raíz del repo, sin Django):

    python -m programa_genetico.comparar_series --semillas 5
"""

from __future__ import annotations

import argparse
import csv
import random
import statistics
import time
from pathlib import Path

from haversine import haversine

from programa_genetico.motor_series import Instancia, busqueda_aleatoria, evolucionar

RAIZ = Path(__file__).resolve().parent.parent


def cargar_equipos(n: int) -> dict:
    with open(RAIZ / "static" / "csv" / "teams.csv", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    return {fila["Team Abbreviation"]: (float(fila["Lat"]), float(fila["Lon"])) for fila in filas[:n]}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--equipos", type=int, default=30)
    p.add_argument("--series", type=int, default=54)
    p.add_argument("--dias", type=int, default=3)
    p.add_argument("--generaciones", type=int, default=50)
    p.add_argument("--poblacion", type=int, default=100)
    p.add_argument("--semillas", type=int, default=5)
    args = p.parse_args()

    coords = cargar_equipos(args.equipos)
    inst = Instancia(list(coords), lambda a, b: haversine(coords[a], coords[b]),
                     num_series=args.series, dias_por_serie=args.dias)
    print(f"{len(coords)} equipos, {inst.num_series} series de {inst.dias_por_serie} días "
          f"= {inst.juegos_por_equipo} juegos por equipo")

    mejoras = []
    for semilla in range(args.semillas):
        t = time.time()
        cal0 = inst.calendario_aleatorio(random.Random(semilla))
        r = evolucionar(inst, cal0, generaciones=args.generaciones,
                        tam_poblacion=args.poblacion, semilla=semilla)
        _, fit_b = busqueda_aleatoria(inst, r.evaluaciones, random.Random(10_000 + semilla))
        mejora = 100 * (fit_b[1] - r.fitness[1]) / fit_b[1]
        mejoras.append(mejora)
        print(f"semilla {semilla}: PG C1={r.fitness[0]} C2={r.fitness[1]:,.0f} km "
              f"(cal0 {r.fitness_cal0[1]:,.0f}, mejor en gen {r.generacion_del_mejor}) | "
              f"aleatoria C1={fit_b[0]} C2={fit_b[1]:,.0f} km | evals={r.evaluaciones} | "
              f"mejora {mejora:.1f}% | {time.time() - t:.0f}s")
    gana = sum(1 for m in mejoras if m > 0)
    print(f"\nPG gana en {gana} de {len(mejoras)} semillas. Mejora media {statistics.mean(mejoras):.1f}%")


if __name__ == "__main__":
    main()
