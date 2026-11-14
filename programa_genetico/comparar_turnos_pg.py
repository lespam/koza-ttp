"""Compara la PG por turnos contra movimientos al azar con el mismo número de movimientos.

Uso (desde la raíz del repo, sin Django):

    python -m programa_genetico.comparar_turnos_pg --semillas 4 --generaciones 20 --poblacion 16
"""

from __future__ import annotations

import argparse
import random
import time

from programa_genetico.comparar_series import cargar_equipos
from programa_genetico.comparar_turnos import KM_OFICIAL_2023
from programa_genetico.motor_turnos import CalendarioTurnos, haversine_km, medir_juegos, series_mlb_2023
from programa_genetico.motor_turnos_pg import busqueda_aleatoria, evolucionar


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--semillas", type=int, default=1)
    p.add_argument("--primera", type=int, default=1)
    p.add_argument("--generaciones", type=int, default=20)
    p.add_argument("--poblacion", type=int, default=16)
    args = p.parse_args()
    coords = cargar_equipos(30)
    for semilla in range(args.primera, args.primera + args.semillas):
        rng = random.Random(semilla)
        cal = CalendarioTurnos(series_mlb_2023(rng), sorted(coords),
                               lambda a, b: haversine_km(coords[a], coords[b]))
        if not cal.construir(rng):
            raise RuntimeError("No se pudo construir un calendario inicial sin choques.")
        base = CalendarioTurnos.__new__(CalendarioTurnos)
        base.__dict__.update(cal.__dict__)
        base.restaurar(cal.copia_estado())
        t = time.time()
        r = evolucionar(cal, generaciones=args.generaciones, tam_poblacion=args.poblacion,
                        repeticiones=args.poblacion, semilla=semilla)
        t_pg = time.time() - t
        _, fit_azar = busqueda_aleatoria(base, r.movimientos, random.Random(10_000 + semilla))
        m = medir_juegos(r.mejor_calendario.juegos_por_fecha(), coords)
        print(f"semilla {semilla}: PG {m['km']:,} km ({r.fitness[0]} reglas rotas, "
              f"{100 * (m['km'] - KM_OFICIAL_2023) / KM_OFICIAL_2023:+.1f}% vs oficial) | "
              f"azar {fit_azar[1]:,.0f} km ({fit_azar[0]} reglas rotas) | "
              f"{r.movimientos:,} movimientos | {t_pg:.0f}s")
        print(f"    {m}")
        print(f"    ADF_turno: {r.mejor_individuo[0]}")
        print(f"    AJUSTE: {r.mejor_individuo[1]}")


if __name__ == "__main__":
    main()
