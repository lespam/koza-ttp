# Uso: python marca_de_agua.py original.pdf salida.pdf
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
r = PdfReader(src); w = PdfWriter()

def capa(ancho, alto):
    b = io.BytesIO(); c = canvas.Canvas(b, pagesize=(ancho, alto))
    # Marca diagonal central
    c.saveState()
    c.setFillColor(Color(0.5, 0.5, 0.5, alpha=0.16))
    c.translate(ancho/2, alto/2); c.rotate(28)
    c.setFont("DVB", alto*0.085); c.drawCentredString(0, alto*0.02, "© Leslie Pamela Brenes Valencia")
    c.setFont("DV", alto*0.04);  c.drawCentredString(0, -alto*0.06, "Tesis ITAM 2026 · github.com/lespam/koza-ttp")
    c.restoreState()
    # Pie legible para citas
    c.setFillColor(Color(0.35, 0.35, 0.35, alpha=0.75)); c.setFont("DV", alto*0.016)
    c.drawRightString(ancho - alto*0.02, alto*0.045,
        "Copia de preservación · Prohibida su reproducción sin citar la fuente")
    c.save(); b.seek(0)
    return PdfReader(b).pages[0]

for p in r.pages:
    ancho, alto = float(p.mediabox.width), float(p.mediabox.height)
    p.merge_page(capa(ancho, alto))
    w.add_page(p)
w.add_metadata({"/Title": "Programación Genética en la planificación de temporadas de béisbol",
                "/Author": "Leslie Pamela Brenes Valencia",
                "/Subject": "Presentación de defensa de tesis, ITAM, 23 de julio de 2026"})
w.compress_identical_objects()
with open(dst, "wb") as f: w.write(f)
