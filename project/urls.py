"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
#from django.contrib import admin
from django.urls import include, path, re_path
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    # Language picker posts here (sets the language cookie and redirects)
    path('i18n/', include('django.conf.urls.i18n')),
    # Mexican Spanish is the only Spanish: /es/... and /es-mx/... go to the unprefixed page
    re_path(r'^es(?:-mx)?/(?P<rest>.*)$', RedirectView.as_view(url='/%(rest)s', permanent=True,
                                                             query_string=True)),
]

# Mexican Spanish at /, every other language under its prefix (/en/, /fr/, ...)
urlpatterns += i18n_patterns(
    #path('admin/', admin.site.urls),
    path('myapp/', include('myapp.urls')),
    #path('', include('myapp.urls')),
    path('', include('tesis.urls')),
    path('pg/', include('programa_genetico.urls')),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)