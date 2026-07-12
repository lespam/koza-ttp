import os
import django
import pandas as pd
from pathlib import Path
import sys

# Correct the project name and settings path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# Assuming this script is in the root of your Django project directory
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

django.setup()

# Now your Django models are available
from tesis.models import Equipo

path = '/static/csv/teams.csv'
data = pd.read_csv(path)
i = 1
for x in data.values:
    equipo = Equipo.objects.create(
        
        team_abbreviation=x[0],
        nickname=x[1],
        league=x[2],
        team_name=x[3],
        arena_name=x[4],
        arena_location=x[5],
        city=x[6],
        seating_capacity=x[7],
        opening_year=x[8],
        lat=x[9],
        lon=x[10],
        address=x[11],
        first_year_of_this_combination=x[12],
        last_year_of_this_combination=x[13]
    )
    
    equipo.save()
    print("next item")
