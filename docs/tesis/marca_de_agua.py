# Uso: python marca_de_agua.py original.pdf salida.pdf ["Asunto"] ["Etiqueta"]
#   Asunto: metadato /Subject del PDF (opcional).
#   Etiqueta: texto visible en la esquina superior de cada página, p. ej. "Versión pre-oficial" (opcional).
# Requiere: pip install pypdf reportlab (y la fuente DejaVu Sans)
import io, sys
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color

pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
src, dst = sys.argv[1], sys.argv[2]
asunto = sys.argv[3] if len(sys.argv) > 3 else "Presentación de defensa de tesis, ITAM, 23 de julio de 2026"
etiqueta = sys.argv[4] if len(sys.argv) > 4 else ""
r = PdfReader(src); w = PdfWriter()

def capa(ancho, alto):
    b = io.BytesIO(); c = canvas.Canvas(b, pagesize=(ancho, alto))
    # Marca diagonal central
    c.saveState()
    c.setFillColor(Color(0.5, 0.5, 0.5, alpha=0.16))
    c.translate(ancho/2, alto/2); c.rotate(28)
    # Tamaño según la altura, reducido si el texto no cabe en el ancho (páginas verticales)
    t1, t2 = "© Leslie Pamela Brenes Valencia", "Tesis ITAM 2026 · github.com/lespam/koza-ttp"
    f1 = min(alto*0.085, ancho*0.85 / (pdfmetrics.stringWidth(t1, "DVB", 1)))
    f2 = min(alto*0.04, ancho*0.8 / (pdfmetrics.stringWidth(t2, "DV", 1)))
    c.setFont("DVB", f1); c.drawCentredString(0, alto*0.02, t1)
    c.setFont("DV", f2);  c.drawCentredString(0, -alto*0.02 - f1*0.9, t2)
    c.restoreState()
    # Pie legible para citas
    c.setFillColor(Color(0.35, 0.35, 0.35, alpha=0.75)); c.setFont("DV", alto*0.016)
    # En páginas verticales el pie va más abajo para no tapar el número de página
    c.drawRightString(ancho - alto*0.02, alto*(0.045 if ancho > alto else 0.015),
        "Copia de preservación · Prohibida su reproducción sin citar la fuente")
    if etiqueta:
        c.setFillColor(Color(0.6, 0.1, 0.1, alpha=0.85)); c.setFont("DVB", alto*0.018)
        c.drawRightString(ancho - alto*0.02, alto - alto*0.035, etiqueta)
    c.save(); b.seek(0)
    return PdfReader(b).pages[0]

for p in r.pages:
    ancho, alto = float(p.mediabox.width), float(p.mediabox.height)
    p.merge_page(capa(ancho, alto))
    w.add_page(p)
w.add_metadata({"/Title": "Programación Genética en la planificación de temporadas de béisbol",
                "/Author": "Leslie Pamela Brenes Valencia",
                "/Subject": asunto})
w.compress_identical_objects()
with open(dst, "wb") as f: w.write(f)
