"""Genera el sitio estático: cada página en HTML, en todos los idiomas.

    python manage.py generar_estatico            # escribe sitio_estatico/
    python manage.py generar_estatico --idiomas es-mx en

Recorre el sitio con el cliente de pruebas de Django, empezando en la portada
de cada idioma y siguiendo los enlaces internos. Guarda cada página como
<ruta>/index.html y copia static/. Las páginas que necesitan servidor (registro
de equipos, ligas, calendarios, la guía y el tablero de la tesis) no se generan.
"""
import re
import shutil
from html import unescape
from pathlib import Path
from urllib.parse import urldefrag, urlsplit

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.test import Client
from django.test.utils import override_settings

# Rutas (sin prefijo de idioma) que necesitan servidor o base de datos
EXCLUIR = re.compile(
    r"^/(guia|equipo|liga|torneo|configuracion|juego|calendario|serie|condicion|programa_facade|"
    r"obtener_|myapp|pg|i18n|admin|media|demo/configuracion|demo/resultado|demo/tesis)"
)
ENLACE = re.compile(r'href="([^"]+)"')


class Command(BaseCommand):
    help = "Genera el sitio estático en sitio_estatico/."

    def add_arguments(self, parser):
        parser.add_argument("--salida", default=str(Path(settings.BASE_DIR) / "sitio_estatico"))
        parser.add_argument("--idiomas", nargs="*", help="Códigos de idioma (por omisión, todos).")
        parser.add_argument("--dominio", help="Dominio propio para GitHub Pages (escribe el archivo CNAME).")

    def handle(self, *args, **opciones):
        salida = Path(opciones["salida"])
        if salida.exists():
            shutil.rmtree(salida)
        salida.mkdir(parents=True)
        codigos = opciones["idiomas"] or [c for c, _n in settings.LANGUAGES]
        prefijos = {c: ("" if c == settings.LANGUAGE_CODE else f"/{c}") for c in codigos}
        host = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS and settings.ALLOWED_HOSTS[0] != "*" else "localhost"
        cliente = Client(HTTP_HOST=host)
        pendientes = [p + "/" for p in prefijos.values()]
        vistos, guardadas, fallas = set(pendientes), 0, []
        todos_los_prefijos = sorted({f"/{c}" for c, _n in settings.LANGUAGES if c != settings.LANGUAGE_CODE},
                                    key=len, reverse=True)

        def sin_prefijo(ruta):
            for p in todos_los_prefijos:
                if ruta == p or ruta.startswith(p + "/"):
                    return p, ruta[len(p):] or "/"
            return "", ruta

        with override_settings(ESTATICO=True):
            while pendientes:
                ruta = pendientes.pop()
                r = cliente.get(ruta)
                if r.status_code != 200 or "text/html" not in r.get("Content-Type", ""):
                    fallas.append((ruta, r.status_code))
                    continue
                html = r.content.decode("utf-8")
                destino = salida / ruta.lstrip("/") / "index.html"
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.write_text(html, encoding="utf-8")
                guardadas += 1
                for enlace in ENLACE.findall(html):
                    enlace = urldefrag(unescape(enlace))[0]
                    partes = urlsplit(enlace)
                    if partes.scheme or partes.netloc or not partes.path.startswith("/") or partes.query:
                        continue
                    prefijo, resto = sin_prefijo(partes.path)
                    if prefijo not in prefijos.values() or resto.startswith("/static/") or EXCLUIR.match(resto):
                        continue
                    if not partes.path.endswith("/"):
                        continue
                    if partes.path not in vistos:
                        vistos.add(partes.path)
                        pendientes.append(partes.path)

        # Página para direcciones que no existen (GitHub Pages usa 404.html)
        with override_settings(ESTATICO=True, DEBUG=False):
            r = cliente.get("/no-existe-esta-pagina/")
        (salida / "404.html").write_bytes(r.content)
        call_command("collectstatic", interactive=False, verbosity=0)
        shutil.copytree(settings.STATIC_ROOT, salida / "static")
        (salida / ".nojekyll").write_text("")
        if opciones["dominio"]:
            (salida / "CNAME").write_text(opciones["dominio"] + "\n")
        self.stdout.write(f"{guardadas} páginas en {salida}")
        for ruta, estado in sorted(fallas):
            self.stdout.write(f"  sin generar: {ruta} ({estado})")
