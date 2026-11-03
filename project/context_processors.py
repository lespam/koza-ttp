from django.urls import translate_url

from project.languages import SITE_LANGUAGES


def languages(request):
    """Languages for the picker, each with this page's URL in that language."""
    path = request.get_full_path()
    return {
        "site_languages": [
            {"code": code, "name": english, "native": native,
             "url": translate_url(path, code)}
            for code, english, native in SITE_LANGUAGES
        ],
    }
