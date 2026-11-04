from django.urls import path
from django.views.generic import TemplateView

app_name = "documentacion"


def pagina(plantilla, seccion):
    return TemplateView.as_view(template_name=f"documentacion/{plantilla}.html",
                                extra_context={"seccion": seccion})


urlpatterns = [
    path("", pagina("index", "inicio"), name="index"),
    path("historico/", pagina("historico", "historico"), name="historico"),
    path("avances/", pagina("avances", "avances"), name="avances"),
]
