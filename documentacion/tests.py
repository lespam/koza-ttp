from django.test import SimpleTestCase
from django.urls import reverse


class PaginasDeDocumentacion(SimpleTestCase):
    nombres = ["documentacion:index", "documentacion:historico", "documentacion:avances"]

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


class LenguasIndigenas(SimpleTestCase):
    """Maya y otomí: traducción automática con aviso de revisión."""

    def test_aviso_solo_en_lenguas_indigenas(self):
        for code in ("yua", "otq"):
            with self.subTest(idioma=code):
                r = self.client.get(f"/{code}/documentacion/")
                self.assertEqual(r.status_code, 200)
                self.assertContains(r, f'lang="{code}"')
                self.assertContains(r, 'class="aviso-traduccion"')
                self.assertContains(r, "Enviar una corrección")
        for url in ("/documentacion/", "/en/documentacion/"):
            with self.subTest(url=url):
                self.assertNotContains(self.client.get(url), 'class="aviso-traduccion"')

    def test_google_acepta_lenguas_que_no_conoce(self):
        # deep-translator no conoce el maya; el comando debe aceptarlo igual
        from tesis.management.commands.translate_site import Command
        self.assertEqual(Command.google_translator("yua")._target, "yua")

    def test_sin_lenguas_de_google(self):
        for code in ("nhe", "zap"):
            self.assertEqual(self.client.get(f"/{code}/documentacion/").status_code, 404)

    def test_numero_de_idiomas_al_dia(self):
        from django.conf import settings
        r = self.client.get(reverse("documentacion:avances"))
        self.assertContains(r, f"{len(settings.LANGUAGES)} idiomas")
