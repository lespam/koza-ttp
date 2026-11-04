from urllib.parse import urlsplit

from django.conf import settings
from django.utils import translation
from django.utils.translation import get_language_from_path
from django.views.i18n import set_language as django_set_language


def set_language(request):
    """Cambia de idioma desde cualquier página.

    Django traduce la dirección de regreso (`next`) solo si está en el idioma activo.
    El idioma activo sale de la cookie, que puede no coincidir con la página: por
    ejemplo, si se llegó a /yua/ con un enlace. Entonces regresaba a la misma página
    y no cambiaba el idioma. Aquí se activa primero el idioma de la página de origen.
    Una página sin prefijo (/documentacion/) está en español de México.
    """
    origen = request.POST.get("next") or request.GET.get("next") or ""
    idioma_origen = get_language_from_path(urlsplit(origen).path) or settings.LANGUAGE_CODE
    translation.activate(idioma_origen)
    return django_set_language(request)
