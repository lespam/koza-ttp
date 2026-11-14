from django.test import SimpleTestCase, TestCase
from django.urls import reverse


class PaginasDeDocumentacion(SimpleTestCase):
    nombres = ["documentacion:index", "documentacion:historico", "documentacion:avances",
               "documentacion:investigacion"]

    def test_cargan_en_espanol(self):
        for nombre in self.nombres:
            with self.subTest(nombre=nombre):
                r = self.client.get(reverse(nombre))
                self.assertEqual(r.status_code, 200)
                self.assertContains(r, '<main id="contenido"')
                self.assertContains(r, 'aria-current="page"')

    def test_cargan_en_otro_idioma(self):
        r = self.client.get("/en/documentacion/historico/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'lang="en"')

    def test_investigacion_tiene_datos_y_figuras(self):
        import json
        r = self.client.get(reverse("documentacion:investigacion"))
        self.assertContains(r, 'id="investigacion-datos"')
        for figura in ("fig-barras", "fig-turnos", "fig-kempe", "fig-valle", "fig-temp"):
            self.assertContains(r, f'id="{figura}"')
        import re
        bloque = re.search(r'id="investigacion-datos"[^>]*>(.*?)</script>', r.content.decode(), re.S).group(1)
        datos = json.loads(bloque)
        self.assertEqual(datos["oficial"], 1.74)
        self.assertEqual(sum(1 for b in datos["barras"] if b["oficial"]), 1)

    def test_resultado_negativo_visible(self):
        r = self.client.get(reverse("documentacion:historico"))
        self.assertContains(r, "3,182,738")
        self.assertContains(r, "2,663,470")


class PaginasEnTodosLosIdiomas(SimpleTestCase):
    """Una traducción con un % mal escapado tumba la página con un error 500.
    Necesita los .mo compilados (python manage.py translate_site --compile-only)."""

    def test_cargan_en_cada_idioma(self):
        from django.conf import settings
        for code, _ in settings.LANGUAGES:
            prefijo = "" if code == settings.LANGUAGE_CODE else f"/{code}"
            for pagina in ("", "historico/", "avances/"):
                with self.subTest(idioma=code, pagina=pagina):
                    r = self.client.get(f"{prefijo}/documentacion/{pagina}")
                    self.assertEqual(r.status_code, 200)


class EscaparPorcentaje(SimpleTestCase):
    def test_repara_porcentaje_suelto(self):
        from tesis.management.commands.translate_site import Command
        fuente = "Dio una distancia 19.5%% mayor y %(n)s veces más."
        self.assertEqual(Command.escape_percent(fuente, "A 19.5% greater, %(n)s times."),
                         "A 19.5%% greater, %(n)s times.")
        self.assertEqual(Command.escape_percent(fuente, "A 19.5%% greater."), "A 19.5%% greater.")
        self.assertFalse(Command.same_markup(fuente, "A 19.5% greater, %(n)s times."))


class VariableEnEnlace(SimpleTestCase):
    """Una variable dentro de un atributo, como <a href="%(guia)s">, no se envuelve en <span>."""

    def test_azure_no_rompe_el_enlace(self):
        import os
        from unittest import mock
        from tesis.management.commands.translate_site import Command
        fuente = 'Usa la <a href="%(guia)s">guía</a> en %(n)s pasos.'
        enviado = {}

        def eco(url, params, headers, json, timeout):
            enviado["texto"] = json[0]["text"]
            respuesta = mock.Mock(status_code=200)
            respuesta.json.return_value = [{"translations": [{"text": json[0]["text"]}]}]
            return respuesta

        with mock.patch.dict(os.environ, {"AZURE_TRANSLATOR_KEY": "x"}), \
                mock.patch("tesis.management.commands.translate_site.requests.post", eco):
            resultado = Command().azure_translate([fuente], "en")[0]
        self.assertIn('<a href="%(guia)s">', enviado["texto"])
        self.assertIn('<span class="notranslate">%(n)s</span>', enviado["texto"])
        self.assertEqual(resultado, fuente)
        self.assertTrue(Command.same_markup(fuente, resultado))


class LenguasIndigenas(SimpleTestCase):
    """Maya y otomí: traducción automática con aviso de revisión."""

    def test_aviso_en_todo_idioma_que_no_es_el_original(self):
        # T-2: todas las traducciones son automáticas, no solo maya y otomí
        for code in ("yua", "otq", "en", "pt", "ar"):
            with self.subTest(idioma=code):
                r = self.client.get(f"/{code}/documentacion/")
                self.assertEqual(r.status_code, 200)
                self.assertContains(r, f'lang="{code}"')
                self.assertContains(r, 'class="aviso-traduccion"')
                self.assertContains(r, "Enviar una corrección")
        self.assertNotContains(self.client.get("/documentacion/", HTTP_ACCEPT_LANGUAGE="es-MX"),
                               'class="aviso-traduccion"')

    def test_google_acepta_lenguas_que_no_conoce(self):
        # deep-translator no conoce el maya; el comando debe aceptarlo igual
        from tesis.management.commands.translate_site import Command
        self.assertEqual(Command.google_translator("yua")._target, "yua")

    def test_sin_lenguas_de_google(self):
        for code in ("nhe", "zap"):
            self.assertEqual(self.client.get(f"/{code}/documentacion/").status_code, 404)

    def test_numero_de_idiomas_al_dia(self):
        from django.conf import settings
        # URL fija: reverse() usaría el idioma que dejó activo la prueba anterior
        r = self.client.get("/documentacion/avances/")
        self.assertContains(r, f"{len(settings.LANGUAGES)} idiomas")


class CambioDeIdioma(SimpleTestCase):
    """El selector debe llevar a la misma página en el idioma elegido, sin importar
    la cookie de idioma que ya tenga el navegador."""

    casos = [
        # (cookie previa, página de origen, idioma elegido, destino esperado)
        (None, "/yua/documentacion/", "es-mx", "/documentacion/"),
        ("es-mx", "/otq/documentacion/historico/", "es-mx", "/documentacion/historico/"),
        ("en", "/yua/documentacion/", "es-mx", "/documentacion/"),
        ("yua", "/documentacion/avances/", "en", "/en/documentacion/avances/"),
        ("en", "/fr/documentacion/", "yua", "/yua/documentacion/"),
        (None, "/documentacion/", "otq", "/otq/documentacion/"),
    ]

    def test_selector_de_idioma(self):
        from django.conf import settings
        for cookie, origen, idioma, destino in self.casos:
            with self.subTest(cookie=cookie, origen=origen, idioma=idioma):
                self.client.cookies.clear()
                if cookie:
                    self.client.cookies[settings.LANGUAGE_COOKIE_NAME] = cookie
                r = self.client.post(reverse("set_language"), {"language": idioma, "next": origen})
                self.assertRedirects(r, destino, fetch_redirect_response=False)


class IdiomaAutomatico(SimpleTestCase):
    """La primera visita lleva al idioma del navegador; el selector manda."""

    pagina = "/documentacion/historico/"

    def test_navegador_en_ingles_va_a_ingles(self):
        r = self.client.get(self.pagina + "?x=1", HTTP_ACCEPT_LANGUAGE="en-US,en;q=0.9")
        self.assertRedirects(r, "/en/documentacion/historico/?x=1", fetch_redirect_response=False)

    def test_navegador_en_chino(self):
        r = self.client.get(self.pagina, HTTP_ACCEPT_LANGUAGE="zh-CN,zh;q=0.9")
        self.assertRedirects(r, "/zh-hans/documentacion/historico/", fetch_redirect_response=False)

    def test_navegador_en_espanol_se_queda(self):
        for idioma in ("es-MX", "es-ES,es;q=0.9", "es-AR"):
            with self.subTest(idioma=idioma):
                r = self.client.get(self.pagina, HTTP_ACCEPT_LANGUAGE=idioma)
                self.assertEqual(r.status_code, 200)

    def test_sin_idioma_se_queda_en_espanol(self):
        r = self.client.get(self.pagina)
        self.assertEqual(r.status_code, 200)
        self.assertIn("Accept-Language", r["Vary"])

    def test_idioma_no_disponible_se_queda_en_espanol(self):
        r = self.client.get(self.pagina, HTTP_ACCEPT_LANGUAGE="xx")
        self.assertEqual(r.status_code, 200)

    def test_elegir_espanol_gana_al_navegador(self):
        self.client.post(reverse("set_language"), {"language": "es-mx", "next": "/en" + self.pagina})
        r = self.client.get(self.pagina, HTTP_ACCEPT_LANGUAGE="en-US")
        self.assertEqual(r.status_code, 200)

    def test_pagina_con_prefijo_no_cambia(self):
        r = self.client.get("/fr" + self.pagina, HTTP_ACCEPT_LANGUAGE="en-US")
        self.assertEqual(r.status_code, 200)

    def test_formularios_post_no_se_redirigen(self):
        r = self.client.post(reverse("set_language"), {"language": "en", "next": "/"},
                             HTTP_ACCEPT_LANGUAGE="en-US")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], "/en/")


class UnaSolaCifraDelMotor(TestCase):
    """La portada, la demo y los avances dicen lo mismo sobre el motor mejorado."""

    def test_las_tres_paginas_usan_la_misma_cifra(self):
        from project.estado_motor import MOTOR
        cifra = str(MOTOR["mejorado"]["frente_al_azar"])
        for url in ("/", "/demo/", "/documentacion/avances/"):
            with self.subTest(url=url):
                html = self.client.get(url, HTTP_ACCEPT_LANGUAGE="es-MX").content.decode()
                self.assertNotIn("31 %", html)
                if url != "/demo/":  # sin configuración, la demo invita a la guía
                    self.assertIn(cifra, html)

    def test_avances_ya_no_dice_sin_resultados(self):
        html = self.client.get("/documentacion/avances/", HTTP_ACCEPT_LANGUAGE="es-MX").content.decode()
        self.assertNotIn("Sin resultados todavía", html)


class FraseLiteral(TestCase):
    """T-1: la frase principal es literal y está bien traducida a mano en inglés y portugués."""

    def test_portada_en_cada_idioma(self):
        casos = {
            "/": "el algoritmo no fue mejor que elegir calendarios al azar.",
            "/en/": "the algorithm was not better than choosing schedules at random.",
            "/pt/": "o algoritmo não foi melhor do que escolher calendários ao acaso.",
        }
        for url, frase in casos.items():
            with self.subTest(url=url):
                html = self.client.get(url, HTTP_ACCEPT_LANGUAGE="es-MX").content.decode()
                self.assertIn(frase, html)
                self.assertNotIn("le ganó al azar", html)


class TextosDePython(SimpleTestCase):
    """translate_site también encuentra los textos de formularios y datos en Python."""

    def test_extrae_gettext_de_python(self):
        from tesis.management.commands.translate_site import Command
        fuente = 'from django.utils.translation import gettext_lazy as _\nA = _("Nombre del equipo")\nB = len("x")\n'
        self.assertEqual(Command.python_msgids(fuente), ["Nombre del equipo"])

    def test_incluye_la_guia_y_el_estado_del_motor(self):
        from tesis.management.commands.translate_site import Command
        msgids = Command().extract_msgids()
        self.assertIn("Nombre del equipo", msgids)
        self.assertIn("Versión de la tesis (2026)", msgids)


class BotonDeModo(SimpleTestCase):
    def test_tiene_los_dos_textos(self):
        html = self.client.get("/documentacion/", HTTP_ACCEPT_LANGUAGE="es-MX").content.decode()
        self.assertIn('class="tema-a-oscuro"', html)
        self.assertIn('class="tema-a-claro" hidden', html)
        self.assertNotIn("aria-pressed", html)
