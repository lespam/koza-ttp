"""Corrige la longitud del estadio de Colorado (Coors Field).

static/csv/teams.csv tenía la latitud copiada como longitud (-39.75588), lo que ponía
a Denver en el océano Atlántico y alteraba toda distancia con Colorado. Solo cambia
filas que tienen exactamente el valor erróneo, así no toca equipos editados a mano.
"""
from django.db import migrations

ERRONEA = -39.75588
CORRECTA = -104.99420


def corregir(apps, schema_editor):
    Equipo = apps.get_model("tesis", "Equipo")
    Equipo.objects.filter(team_abbreviation="COL", lon=ERRONEA).update(lon=CORRECTA)


def revertir(apps, schema_editor):
    Equipo = apps.get_model("tesis", "Equipo")
    Equipo.objects.filter(team_abbreviation="COL", lon=CORRECTA).update(lon=ERRONEA)


class Migration(migrations.Migration):
    dependencies = [("tesis", "0002_rename_dias_de_juego_torneo_dias_seleccionados")]
    operations = [migrations.RunPython(corregir, revertir)]
