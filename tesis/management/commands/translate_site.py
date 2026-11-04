"""Extrae, traduce automáticamente y compila los textos del sitio.

    python manage.py translate_site                  # extrae + traduce lo nuevo + compila
    python manage.py translate_site --compile-only   # solo compila los .po a .mo (servidor)
    python manage.py translate_site --languages en fr

Los textos se marcan en las plantillas con {% translate %} / {% blocktranslate trimmed %}.
Las traducciones quedan en locale/<idioma>/LC_MESSAGES/django.po; se pueden corregir a
mano y esta orden nunca sobrescribe una traducción que ya existe.

Motores de traducción (--backend):
    azure   Azure AI Translator. Capa gratuita (F0): 2 millones de caracteres al mes.
            Necesita AZURE_TRANSLATOR_KEY (+ AZURE_TRANSLATOR_REGION) en el .env.
    google  Google Translate vía el paquete deep-translator. Sin clave; útil para pruebas.

El náhuatl (nhe) y el zapoteco (zap) solo existen en Google Translate, así que siempre
se traducen con Google, aunque el motor elegido sea Azure.

No necesita gettext: usa polib para leer, escribir y compilar los catálogos.
"""
import ast
import os
import re
import time
import uuid
from pathlib import Path

import polib
import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import to_locale
from django.utils.translation.template import templatize

from project.languages import (
    GOOGLE_ONLY_LANGUAGES,
    LANGUAGE_MAP_AZURE,
    LANGUAGE_MAP_GOOGLE,
    MACHINE_SOURCE_LANGUAGE,
    TARGET_LANGUAGES,
)

SKIP_DIRS = {"env", "venv", ".venv", "staticfiles", "media", "node_modules", ".git", "locale"}
# templatize() convierte cada {% translate %} en  gettext(u'...')  con repr() de Python
GETTEXT_CALL = re.compile(r"""\bgettext\(u?('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")\)""")
PLACEHOLDER = re.compile(r"%\([a-zA-Z_][a-zA-Z0-9_]*\)[sd]")
# Un % que no es parte de %(x)s ni de %%
LONE_PERCENT = re.compile(r"(?<!%)%(?![%(])")
TAG = re.compile(r"</?[a-zA-Z][^>]*>")
AZURE_BATCH = 50
AZURE_RETRIES = 10


class Command(BaseCommand):
    help = "Extrae, traduce automáticamente y compila los textos del sitio a todos los idiomas."

    def add_arguments(self, parser):
        parser.add_argument("--languages", nargs="+", default=TARGET_LANGUAGES,
                            help="Idiomas a procesar (por defecto, todos).")
        parser.add_argument("--backend", choices=["azure", "google"], default="azure")
        parser.add_argument("--compile-only", action="store_true",
                            help="Solo compila los .po existentes a .mo.")
        parser.add_argument("--no-translate", action="store_true",
                            help="Actualiza los .po con los textos nuevos pero no los traduce.")

    def handle(self, *args, **options):
        unknown = set(options["languages"]) - set(TARGET_LANGUAGES)
        if unknown:
            raise CommandError(f"Idiomas desconocidos: {', '.join(sorted(unknown))}")

        locale_dir = Path(settings.LOCALE_PATHS[0])
        if options["compile_only"]:
            for code in options["languages"]:
                po_path = self.po_path(locale_dir, code)
                if po_path.exists():
                    polib.pofile(str(po_path)).save_as_mofile(str(po_path.with_suffix(".mo")))
            self.stdout.write(self.style.SUCCESS("Catálogos compilados."))
            return

        msgids = self.extract_msgids()
        self.stdout.write(f"{len(msgids)} textos encontrados en las plantillas.")

        for code in options["languages"]:
            translate = None
            if not options["no_translate"]:
                use_google = options["backend"] == "google" or code in GOOGLE_ONLY_LANGUAGES
                translate = self.google_translate if use_google else self.azure_translate

            po_path = self.po_path(locale_dir, code)
            po = self.update_catalog(po_path, code, msgids)

            # Repara traducciones viejas que perdieron el %% de un porcentaje
            for entry in po:
                if entry.msgstr:
                    entry.msgstr = self.escape_percent(entry.msgid, entry.msgstr)

            pending = [entry for entry in po if not entry.msgstr and not entry.obsolete]
            done = 0
            if translate and pending:
                sources = [entry.msgid for entry in pending]
                results = translate(sources, code)
                for entry, result in zip(pending, results):
                    result = self.escape_percent(entry.msgid, result) if result else result
                    if result and self.same_markup(entry.msgid, result):
                        entry.msgstr = result
                        done += 1

            po.save(str(po_path))
            po.save_as_mofile(str(po_path.with_suffix(".mo")))
            self.stdout.write(
                f"{code}: {po.percent_translated()}% traducido "
                f"({done} nuevos, {len(pending) - done} pendientes)"
            )

    @staticmethod
    def po_path(locale_dir, code):
        return locale_dir / to_locale(code) / "LC_MESSAGES" / "django.po"

    def extract_msgids(self):
        """Todos los textos marcados en las plantillas, en orden de aparición."""
        msgids = {}
        for path in self.template_paths(Path(settings.BASE_DIR)):
            source = path.read_text(encoding="utf-8")
            if "translate" not in source and "trans " not in source:
                continue
            for match in GETTEXT_CALL.finditer(templatize(source, origin=str(path))):
                msgid = ast.literal_eval(match.group(1))
                location = str(path.relative_to(settings.BASE_DIR)).replace(os.sep, "/")
                msgids.setdefault(msgid, location)
        return msgids

    @staticmethod
    def template_paths(base):
        """Las plantillas .html del proyecto, sin entrar a SKIP_DIRS.

        Las carpetas se descartan antes de recorrerlas: un entorno virtual copiado
        de Linux a Windows tiene enlaces (como env/lib64) que Windows no puede abrir.
        """
        paths = []
        for root, dirs, files in os.walk(base):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
            paths.extend(Path(root) / f for f in files if f.endswith(".html"))
        return sorted(paths)

    @staticmethod
    def update_catalog(po_path, code, msgids):
        """Abre (o crea) el .po, añade los textos nuevos y retira los que ya no se usan."""
        po_path.parent.mkdir(parents=True, exist_ok=True)
        po = polib.pofile(str(po_path)) if po_path.exists() else polib.POFile()
        po.metadata = {
            "Project-Id-Version": "koza-ttp",
            "Language": code,
            "MIME-Version": "1.0",
            "Content-Type": "text/plain; charset=UTF-8",
            "Content-Transfer-Encoding": "8bit",
            **{k: v for k, v in po.metadata.items() if k == "PO-Revision-Date"},
        }
        existing = {entry.msgid: entry for entry in po}
        for msgid, location in msgids.items():
            if msgid not in existing:
                po.append(polib.POEntry(msgid=msgid, msgstr="", occurrences=[(location, "")]))
        for entry in list(po):
            if entry.msgid not in msgids:
                po.remove(entry)
        return po

    @staticmethod
    def escape_percent(source, translation):
        """En {% blocktranslate %} un % literal se escribe %%. Los traductores lo
        devuelven como un solo %, y Django falla al mostrar la página (ValueError).
        Si el original tiene %%, todo % suelto de la traducción vuelve a ser %%."""
        if "%%" not in source:
            return translation
        return LONE_PERCENT.sub("%%", translation)

    @staticmethod
    def same_markup(source, translation):
        """Rechaza traducciones que perdieron variables %(x)s o etiquetas HTML,
        o que Django no podría formatear."""
        if "%%" in source or "%(" in source:
            try:
                translation % {name: "" for name in re.findall(r"%\(([a-zA-Z_][a-zA-Z0-9_]*)\)", source)}
            except (ValueError, TypeError, KeyError):
                return False
        return (sorted(PLACEHOLDER.findall(source)) == sorted(PLACEHOLDER.findall(translation))
                and len(TAG.findall(source)) == len(TAG.findall(translation)))

    # --- Motores de traducción -------------------------------------------------------

    def azure_translate(self, texts, code):
        key = os.environ.get("AZURE_TRANSLATOR_KEY")
        if not key:
            raise CommandError("Falta AZURE_TRANSLATOR_KEY en el .env (o usa --backend google).")
        headers = {
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/json",
            "X-ClientTraceId": str(uuid.uuid4()),
        }
        region = os.environ.get("AZURE_TRANSLATOR_REGION")
        if region:
            headers["Ocp-Apim-Subscription-Region"] = region

        # Las variables %(x)s viajan dentro de <span class="notranslate"> para que no se toquen
        protect = lambda text: PLACEHOLDER.sub(lambda m: f'<span class="notranslate">{m.group(0)}</span>', text)
        unprotect = lambda text: re.sub(r'<span class="notranslate">\s*(.*?)\s*</span>', r"\1", text)

        results = []
        for start in range(0, len(texts), AZURE_BATCH):
            batch = texts[start:start + AZURE_BATCH]
            # La capa gratuita (F0) limita los caracteres por minuto: si responde 429, se espera
            for attempt in range(AZURE_RETRIES):
                response = requests.post(
                    "https://api.cognitive.microsofttranslator.com/translate",
                    params={"api-version": "3.0", "from": MACHINE_SOURCE_LANGUAGE,
                            "to": LANGUAGE_MAP_AZURE[code], "textType": "html"},
                    headers=headers,
                    json=[{"text": protect(text)} for text in batch],
                    timeout=60,
                )
                if response.status_code != 429:
                    break
                wait = int(response.headers.get("Retry-After", 60))
                self.stdout.write(f"{code}: límite de Azure alcanzado, esperando {wait} s...")
                time.sleep(wait)
            if response.status_code != 200:
                raise CommandError(f"Azure Translator respondió {response.status_code}: {response.text}")
            results += [unprotect(item["translations"][0]["text"]) for item in response.json()]
        return results

    def google_translate(self, texts, code):
        translator = self.google_translator(LANGUAGE_MAP_GOOGLE[code])
        results = []
        for text in texts:
            # Las variables %(x)s se cambian por {0}, {1}... que Google respeta
            names = PLACEHOLDER.findall(text)
            masked = text
            for i, name in enumerate(names):
                masked = masked.replace(name, "{%d}" % i, 1)
            try:
                translated = translator.translate(masked) or ""
            except Exception as error:  # una frase fallida no detiene el resto
                self.stderr.write(f"{code}: no se pudo traducir {text[:40]!r}: {error}")
                translated = ""
            for i, name in enumerate(names):
                translated = translated.replace("{%d}" % i, name, 1)
            results.append(translated)
        return results

    @staticmethod
    def google_translator(target):
        """deep-translator solo acepta los idiomas de su lista fija, que es anterior a
        las lenguas que Google agregó en 2024 (náhuatl, zapoteco, maya...). Se le pasa la
        lista ampliada con el código que falte."""
        from deep_translator import GoogleTranslator
        from deep_translator.constants import GOOGLE_LANGUAGES_TO_CODES

        languages = dict(GOOGLE_LANGUAGES_TO_CODES)
        if target not in languages.values():
            languages[target] = target
        return GoogleTranslator(source=MACHINE_SOURCE_LANGUAGE, target=target, languages=languages)
