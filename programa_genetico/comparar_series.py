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

from programa_genetico.motor_series import MLB_DIVISIONES, Instancia, busqueda_aleatoria, evolucionar

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
    p.add_argument("--fitness", choices=["viaje", "rivales"], default="viaje")
    p.add_argument("--combinar", action="store_true", help="agrega mezclar_serie y ADF1")
    p.add_argument("--divisiones", action="store_true", help="reglas de MLB 2023 por división, liga e interliga")
    p.add_argument("--iniciales", type=int, default=1, help="calendarios de inicio (cal0, cal1, ...)")
    args = p.parse_args()

    coords = cargar_equipos(args.equipos)
    inst = Instancia(list(coords), lambda a, b: haversine(coords[a], coords[b]),
                     num_series=args.series, dias_por_serie=args.dias, fitness=args.fitness,
                     divisiones=MLB_DIVISIONES if args.divisiones else None)
    print(f"{len(coords)} equipos, {inst.num_series} series de {inst.dias_por_serie} días "
          f"= {inst.juegos_por_equipo} juegos por equipo, fitness={inst.fitness}")

    mejoras = []
    for semilla in range(args.semillas):
        t = time.time()
        rng_ini = random.Random(semilla)
        cal0 = inst.calendario_aleatorio(rng_ini)
        extra = [inst.calendario_aleatorio(rng_ini) for _ in range(args.iniciales - 1)]
        r = evolucionar(inst, cal0, generaciones=args.generaciones,
                        tam_poblacion=args.poblacion, semilla=semilla,
                        combinar=args.combinar, iniciales_extra=extra)
        cal_b, fit_b = busqueda_aleatoria(inst, r.evaluaciones, random.Random(10_000 + semilla))
        mejora = 100 * (fit_b[1] - r.fitness[1]) / fit_b[1]
        mejoras.append(mejora)
        print(f"semilla {semilla}: PG C1={r.fitness[0]} C2={r.fitness[1]:,.0f} km "
              f"(cal0 {r.fitness_cal0[1]:,.0f}, mejor en gen {r.generacion_del_mejor}) | "
              f"aleatoria C1={fit_b[0]} C2={fit_b[1]:,.0f} km | evals={r.evaluaciones} | "
              f"mejora {mejora:.1f}% | {time.time() - t:.0f}s")
        for nombre, cal in (("PG", r.mejor_calendario), ("aleatoria", cal_b)):
            casa = inst.juegos_en_casa(cal).values()
            print(f"    {nombre}: juegos en casa {min(casa)}-{max(casa)}, "
                  f"máx. series contra el mismo rival {inst.series_contra_mismo_rival(cal)}")
    gana = sum(1 for m in mejoras if m > 0)
    print(f"\nPG gana en {gana} de {len(mejoras)} semillas. Mejora media {statistics.mean(mejoras):.1f}%")


if __name__ == "__main__":
    main()
