from django.urls import translate_url
from django.utils.translation import get_language

from project.languages import SITE_LANGUAGES, SOURCE_LANGUAGE

SITIO_PRINCIPAL = "https://lesliedickinson.dev/"


def languages(request):
    """Languages for the picker, each with this page's URL in that language."""
    path = request.get_full_path()
    return {
        "site_languages": [
            {"code": code, "name": english, "native": native,
             "url": translate_url(path, code)}
            for code, english, native in SITE_LANGUAGES
        ],
        # Todo idioma que no es el original es traducción automática: se avisa y se pide revisión
        "traduccion_en_revision": get_language() != SOURCE_LANGUAGE,
        # lesliedickinson.dev solo existe en español e inglés
        "sitio_principal": SITIO_PRINCIPAL + ("es/" if (get_language() or "").startswith("es") else "en/"),
    }
