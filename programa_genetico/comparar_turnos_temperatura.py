"""Entrena la PG de temperatura y la compara contra el recocido hecho a mano.

Uso (desde la raíz del repo, sin Django):

    python -m programa_genetico.comparar_turnos_temperatura --generaciones 12 --poblacion 24
"""

from __future__ import annotations

import argparse
import multiprocessing
import time

from deap import gp

from programa_genetico.comparar_series import cargar_equipos
from programa_genetico.comparar_turnos import KM_OFICIAL_2023
from programa_genetico.motor_turnos import medir_juegos
from programa_genetico.motor_turnos_temperatura import (
    PSET, correr_con_regla, evolucionar, temperatura_a_mano,
)


def _prueba(args):
    texto, semilla, pasos = args
    coords = cargar_equipos(30)
    regla = temperatura_a_mano if texto is None else gp.compile(gp.PrimitiveTree.from_string(texto, PSET), PSET)
    pen, km, cal = correr_con_regla(coords, semilla, pasos, regla)
    m = medir_juegos(cal.juegos_por_fecha(), coords)
    return texto is None, semilla, pen, m


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--generaciones", type=int, default=12)
    p.add_argument("--poblacion", type=int, default=24)
    p.add_argument("--pasos-entrenamiento", type=int, default=30_000)
    p.add_argument("--pasos-prueba", type=int, default=400_000)
    p.add_argument("--semillas-prueba", type=int, default=4)
    p.add_argument("--semilla", type=int, default=0)
    args = p.parse_args()
    coords = cargar_equipos(30)
    t = time.time()
    r = evolucionar(coords, pasos_entrenamiento=args.pasos_entrenamiento, generaciones=args.generaciones,
                    tam_poblacion=args.poblacion, semilla=args.semilla,
                    on_generation=lambda g, f, a: print(f"gen {g}: {f:,.0f} | {a}", flush=True))
    print(f"Entrenamiento: {time.time() - t:.0f}s. Mejor árbol: {r.mejor}")
    trabajos = [(str(r.mejor), s, args.pasos_prueba) for s in range(1, args.semillas_prueba + 1)]
    trabajos += [(None, s, args.pasos_prueba) for s in range(1, args.semillas_prueba + 1)]
    with multiprocessing.get_context("fork").Pool(4) as pool:
        for a_mano, semilla, pen, m in sorted(pool.map(_prueba, trabajos), key=lambda x: (x[1], x[0])):
            nombre = "a mano" if a_mano else "PG    "
            print(f"semilla {semilla} {nombre}: {m['km']:,} km, {pen} reglas rotas, "
                  f"{100 * (m['km'] - KM_OFICIAL_2023) / KM_OFICIAL_2023:+.1f}% vs oficial | "
                  f"{m['temporada_dias']} días, visita máx {m['max_visita']}, casa máx {m['max_casa']}")


if __name__ == "__main__":
    main()
