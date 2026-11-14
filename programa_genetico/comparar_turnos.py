"""Corre el motor por turnos (series de 2, 3 y 4 juegos, con descansos) con la estructura de MLB 2023.

Uso (desde la raíz del repo, sin Django):

    python -m programa_genetico.comparar_turnos --semillas 4 --pasos 400000

Referencia: el calendario oficial 2023 viaja 1.74 millones de km con la
misma medición (``medir_juegos``). Ese calendario no se guarda en el repo
(términos de uso de MLB); solo la cifra calculada.
"""

from __future__ import annotations

import argparse
import json
import random
import time

from programa_genetico.comparar_series import cargar_equipos
from programa_genetico.motor_turnos import (
    CalendarioTurnos, haversine_km, medir_juegos, recocido, series_mlb_2023,
)

KM_OFICIAL_2023 = 1_740_337


def correr(semilla: int, pasos: int, turnos: int = 53, dias: int = 186, avance: bool = False):
    coords = cargar_equipos(30)
    rng = random.Random(semilla)
    cal = CalendarioTurnos(series_mlb_2023(rng), sorted(coords),
                           lambda a, b: haversine_km(coords[a], coords[b]), turnos=turnos, dias=dias)
    if not cal.construir(rng):
        raise RuntimeError("No se pudo construir un calendario inicial sin choques.")
    inicial = cal.evaluar()
    aviso = (lambda p, pen, km: print(f"  paso {p}: reglas rotas {pen}, {km:,.0f} km", flush=True)) if avance else None
    final = recocido(cal, rng, pasos=pasos, on_paso=aviso, cada=max(1, pasos // 10))
    return cal, inicial, final, medir_juegos(cal.juegos_por_fecha(), coords)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--semillas", type=int, default=1)
    p.add_argument("--primera", type=int, default=1)
    p.add_argument("--pasos", type=int, default=400_000)
    p.add_argument("--turnos", type=int, default=53)
    p.add_argument("--guardar", help="carpeta para guardar cada calendario como JSON")
    p.add_argument("--avance", action="store_true")
    args = p.parse_args()
    for semilla in range(args.primera, args.primera + args.semillas):
        t = time.time()
        cal, inicial, final, m = correr(semilla, args.pasos, args.turnos, avance=args.avance)
        dif = 100 * (m["km"] - KM_OFICIAL_2023) / KM_OFICIAL_2023
        print(f"semilla {semilla}: inicio {inicial[1]:,.0f} km ({inicial[0]} reglas rotas) -> "
              f"{m['km']:,} km ({final[0]} reglas rotas), {dif:+.1f}% vs oficial | {time.time() - t:.0f}s")
        print(f"    {m}")
        if args.guardar:
            with open(f"{args.guardar}/turnos_{semilla}.json", "w", encoding="utf-8") as f:
                json.dump({"semilla": semilla, "pasos": args.pasos, "medicion": {k: list(v) if isinstance(v, tuple) else v for k, v in m.items()},
                           "juegos": [(d.isoformat(), h, a) for d, h, a in cal.juegos_por_fecha()]}, f)


if __name__ == "__main__":
    main()
