"""Resultados de la demo ya calculados (para el sitio estático).

Cada torneo ya configurado (tesis/torneos.py) se corre una vez en una
computadora con ``python manage.py precalcular_demo`` y se guarda en
static/data/demo/<torneo>.json. La página /demo/torneo/<torneo>/ solo lee ese
archivo: no calcula nada en cada visita.
"""
import datetime
import json
from dataclasses import asdict
from pathlib import Path

from django.conf import settings

from programa_genetico.demo_turnos import ConfigDemo, ResultadoDemo

CARPETA = Path(settings.BASE_DIR) / "static" / "data" / "demo"


def archivo(clave):
    return CARPETA / f"{clave}.json"


def guardar(clave, equipos, config: ConfigDemo, resultado: ResultadoDemo):
    CARPETA.mkdir(parents=True, exist_ok=True)
    datos = {
        "torneo": clave, "equipos": list(equipos), "config": asdict(config),
        "resultado": {
            "juegos": [[f.isoformat(), h, v] for f, h, v in resultado.juegos],
            "km_azar": resultado.km_azar, "km_final": resultado.km_final,
            "reglas_rotas_azar": resultado.reglas_rotas_azar, "reglas_rotas": resultado.reglas_rotas,
            "revision": resultado.revision, "historial": [list(h) for h in resultado.historial],
        },
    }
    archivo(clave).write_text(json.dumps(datos, ensure_ascii=False, separators=(",", ":"), default=str),
                              encoding="utf-8")


def cargar(clave):
    """(equipos, ConfigDemo, ResultadoDemo) o None si ese torneo no se ha calculado."""
    ruta = archivo(clave)
    if not ruta.exists():
        return None
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    r = datos["resultado"]
    resultado = ResultadoDemo(
        juegos=[(datetime.date.fromisoformat(f), h, v) for f, h, v in r["juegos"]],
        km_azar=r["km_azar"], km_final=r["km_final"],
        reglas_rotas_azar=r["reglas_rotas_azar"], reglas_rotas=r["reglas_rotas"],
        revision=r["revision"], historial=[tuple(h) for h in r["historial"]])
    return datos["equipos"], ConfigDemo(**datos["config"]), resultado
