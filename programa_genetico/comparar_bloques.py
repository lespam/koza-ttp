"""Compara el motor por bloques (cada ADF es un calendario) contra la búsqueda aleatoria.

Uso (desde la raíz del repo, sin Django):

    python -m programa_genetico.comparar_bloques --semillas 3
"""

from __future__ import annotations

import argparse
import random
import statistics
import time

from haversine import haversine

from programa_genetico.comparar_series import cargar_equipos
from programa_genetico.motor_bloques import REGLAS_BLOQUES, Bloques, Jerarquia, busqueda_aleatoria, evolucionar
from programa_genetico.motor_series import MLB_DIVISIONES, Instancia


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--generaciones", type=int, default=50)
    p.add_argument("--poblacion", type=int, default=100)
    p.add_argument("--semillas", type=int, default=3)
    args = p.parse_args()

    coords = cargar_equipos(30)
    inst = Instancia(list(coords), lambda a, b: haversine(coords[a], coords[b]),
                     divisiones=MLB_DIVISIONES, reglas_nivel=REGLAS_BLOQUES)
    jer = Jerarquia(MLB_DIVISIONES)
    mejoras = []
    for semilla in range(args.semillas):
        t = time.time()
        bloques = Bloques.aleatorios(jer, random.Random(semilla))
        r = evolucionar(inst, bloques, generaciones=args.generaciones,
                        tam_poblacion=args.poblacion, semilla=semilla)
        cal_b, fit_b = busqueda_aleatoria(inst, jer, r.evaluaciones, random.Random(10_000 + semilla))
        mejora = 100 * (fit_b[1] - r.fitness[1]) / fit_b[1]
        mejoras.append(mejora)
        casa = inst.juegos_en_casa(r.mejor_calendario).values()
        casa_b = inst.juegos_en_casa(cal_b).values()
        print(f"semilla {semilla}: PG C1={r.fitness[0]} C2={r.fitness[1]:,.0f} km "
              f"(inicio C1={r.fitness_inicial[0]}, mejor en gen {r.generacion_del_mejor}) | "
              f"aleatoria C1={fit_b[0]} C2={fit_b[1]:,.0f} km | evals={r.evaluaciones} | "
              f"mejora {mejora:.1f}% | {time.time() - t:.0f}s")
        print(f"    PG: en casa {min(casa)}-{max(casa)} | aleatoria: en casa {min(casa_b)}-{max(casa_b)}")
    print(f"\nMejora media en viaje: {statistics.mean(mejoras):.1f}%")


if __name__ == "__main__":
    main()
