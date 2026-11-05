from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import Resolver404, resolve
from django.utils import translation
from django.utils.cache import patch_vary_headers
from django.utils.translation import get_language_from_path, get_language_from_request


class IdiomaAutomaticoMiddleware:
    """Lleva a cada visitante al sitio en su idioma la primera vez que entra.

    Las páginas sin prefijo (/, /guia/) están en español de México. Si la persona
    eligió otro idioma antes (cookie) o su navegador pide otro idioma que el sitio
    tiene (Accept-Language), se le redirige a la misma página con prefijo (/en/guia/).

    Si eligió español con el selector, la cookie dice es-mx y ya no se redirige.
    Los navegadores y robots que no mandan idioma ven español, como antes.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        destino = self.destino(request)
        if destino:
            respuesta = HttpResponseRedirect(destino)
        else:
            respuesta = self.get_response(request)
        if get_language_from_path(request.path_info) is None:
            # La respuesta sin prefijo depende del idioma del navegador y de la cookie
            patch_vary_headers(respuesta, ("Accept-Language", "Cookie"))
        return respuesta

    @staticmethod
    def destino(request):
        if request.method not in ("GET", "HEAD"):
            return None
        if get_language_from_path(request.path_info) is not None:
            return None
        idioma = get_language_from_request(request, check_path=False)
        if idioma == settings.LANGUAGE_CODE:
            return None
        ruta = f"/{idioma}{request.path_info}"
        # Solo las páginas traducidas (i18n_patterns) tienen versión con prefijo
        anterior = translation.get_language()
        translation.activate(idioma)
        try:
            resolve(ruta)
        except Resolver404:
            return None
        finally:
            translation.activate(anterior) if anterior else translation.deactivate()
        consulta = request.META.get("QUERY_STRING")
        return f"{request.META.get('SCRIPT_NAME', '')}{ruta}" + (f"?{consulta}" if consulta else "")
