from django.urls import translate_url
from django.utils.translation import get_language

from project.languages import INDIGENOUS_LANGUAGES, SITE_LANGUAGES


def languages(request):
    """Languages for the picker, each with this page's URL in that language."""
    path = request.get_full_path()
    return {
        "site_languages": [
            {"code": code, "name": english, "native": native,
             "url": translate_url(path, code)}
            for code, english, native in SITE_LANGUAGES
        ],
        # Traducción automática a una lengua indígena: se avisa y se pide revisión
        "traduccion_en_revision": get_language() in INDIGENOUS_LANGUAGES,
    }
