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
