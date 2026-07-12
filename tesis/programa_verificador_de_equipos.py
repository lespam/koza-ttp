import pandas as pd
from haversine import haversine, Unit
from datetime import datetime

from django.conf import settings
path = settings.BASE_DIR

# Paths to the CSV files
ruta_equipos = f'{path}/static/csv/teams.csv'
#ruta_calendario = 'media/csv/RES - output_ind_20241106151427063935.csv'
ruta_calendario = f'{path}media/csv/RES - output_ind_20241105065927181457.csv'


columnas = [
    'team_abbreviation', 'nickname', 'league', 'team_name', 'arena_name', 
    'arena_location', 'city', 'seating_capacity', 'opening_year', 'lat', 
    'lon', 'address', 'first_year_of_this_combination', 'last_year_of_this_combination'
]

# Load the CSV without a header 
equipos_df = pd.read_csv(ruta_equipos, header=0, names=columnas)
calendario_df = pd.read_csv(ruta_calendario, header=0, names=['i', 'fecha', 'team1', 'team2']) 

# Create dictionaries to store results for both CSVs
resultados_teams = {
    'equipo': [],
    'distancia_total': [],
    'juegos_casa': [],
    'juegos_fuera': [],
    'juegos_totales': []
}

resultados_calendar = {
    'fecha': [],
    'team1': [],
    'team2': [],
    'distancia': []
}

# Function to calculate the distance using Haversine
def calcular_distancia(coord1, coord2):
    return haversine(coord1, coord2, unit=Unit.KILOMETERS)

# Calculate home games distance and log calendar distances
coords_casa = []
coords_fuera = []
distancia_juego = []

# Loop through the calendar to calculate distances for each match
for juego in calendario_df.values:
    i, fecha, team1, team2 = juego
    
    # Get coordinates for home team
    coords_casa_df = equipos_df[equipos_df['team_abbreviation'] == team1][['lat', 'lon']]
    coords_casa = tuple(coords_casa_df.values[0])
    
    # Get coordinates for away team
    coords_fuera_df = equipos_df[equipos_df['team_abbreviation'] == team2][['lat', 'lon']]
    coords_fuera = tuple(coords_fuera_df.values[0])
    
    # Calculate distance between the two teams for this match
    distancia = haversine(coords_casa, coords_fuera, unit=Unit.KILOMETERS)
    
    # Append the results for the calendar CSV
    resultados_calendar['fecha'].append(fecha)
    resultados_calendar['team1'].append(team1)
    resultados_calendar['team2'].append(team2)
    resultados_calendar['distancia'].append(distancia)

    # Append the distance for each match to the list
    distancia_juego.append(distancia)

# Now calculate the distances and games for each team
for equipo in equipos_df['team_abbreviation'].unique():
    distancia_casa = 0
    distancia_fuera = 0
    juegos_casa = 0
    juegos_fuera = 0
    
    # Get the home team coordinates
    coords_casa_df = equipos_df[equipos_df['team_abbreviation'] == equipo][['lat', 'lon']]
    coords_casa = tuple(coords_casa_df.values[0])

    # Filter the games for this team (home and away)
    juegos_como_local = calendario_df[calendario_df['team1'] == equipo]
    juegos_como_visitante = calendario_df[calendario_df['team2'] == equipo]
    #print(f"juegos local para {equipo} - {juegos_como_local}")
    #print(f"juegos visitante para {equipo} - {juegos_como_visitante}")
    
    # Calculate away games distance
    for _, juego in juegos_como_visitante.iterrows():
        try:
            coords_fuera_df = equipos_df[equipos_df['team_abbreviation'] == juego['team1']][['lat', 'lon']]
            coords_fuera = tuple(coords_fuera_df.values[0])
            distancia_fuera += calcular_distancia(coords_casa, coords_fuera)
        except IndexError:
            print(f"Coordinates for opponent {juego['team1']} not found. Skipping game...")
            continue

    # Sum the distances for total
    distancia_total = distancia_fuera
    juegos_casa = juegos_como_local.shape[0]
    juegos_fuera = juegos_como_visitante.shape[0]
    juegos_totales = juegos_casa + juegos_fuera

    # Append results for the team statistics
    resultados_teams['equipo'].append(equipo)
    resultados_teams['distancia_total'].append(distancia_total)
    resultados_teams['juegos_casa'].append(juegos_casa)
    resultados_teams['juegos_fuera'].append(juegos_fuera)
    resultados_teams['juegos_totales'].append(juegos_totales)

# Create DataFrames from the results dictionaries
resultados_teams_df = pd.DataFrame(resultados_teams)
resultados_calendar_df = pd.DataFrame(resultados_calendar)

# Save the results to CSV files
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

ruta_resultados_teams = f'{path}/static/csv/analisis_equipos_{timestamp}.csv'
ruta_resultados_calendar = f'{path}/static/csv/calendario_distancias_{timestamp}.csv'

resultados_teams_df.to_csv(ruta_resultados_teams, index=False)
resultados_calendar_df.to_csv(ruta_resultados_calendar, index=False)

print(f"Resultados de equipos guardados en '{ruta_resultados_teams}'")
print(f"Resultados del calendario guardados en '{ruta_resultados_calendar}'")
