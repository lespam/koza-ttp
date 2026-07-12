from abc import ABC, abstractmethod
import haversine as hav
from haversine import Unit
import pandas as pd
import math


# Unit values taken from http://www.unitconversion.org/unit_converter/length.html
# Estos valores son los que se usan para convertir de una unidad a otra
_CONVERSIONS = {
    Unit.KILOMETERS:       1.0,
    Unit.METERS:           1000.0,
    Unit.MILES:            0.621371192,
    Unit.NAUTICAL_MILES:   0.539956803,
    Unit.FEET:             3280.839895013,
    Unit.INCHES:           39370.078740158,
}

# Esta clase es la que se encarga de calcular la distancia entre dos puntos
class Calculadora():
    def __init__(self, coordenadas_equipos, metodo="haversine", unidad="km"):
        self.coordenadas_equipos = coordenadas_equipos
        #print(self.coordenadas_equipos)
        #self.coordenadas_equipos = self.coordenadas_equipos.drop_duplicates(subset=["equipo"], inplace=True)
        
        self.metodo_calculo= metodo
        self.unidad_distancia = unidad

    def inicializacion_de_calculadora(self) -> bool:
        # Implement the initialization logic here
        success = True
        return success
    # Esta funcion es la que se encarga de calcular la distancia entre dos puntos con el metodo de haversine
    @abstractmethod
    def haversine(self, punto_a, punto_b, unidad="km"):
        unit = Unit(unidad)
        return hav.haversine(punto_a, punto_b, unit=unit)
    # Esta funcion es la que se encarga de calcular la distancia entre dos puntos con el metodo euclidiano    
    def euclidiano(self, punto_a, punto_b, unidad="km"):
        distancia = math.dist(punto_a, punto_b)
        unit = Unit(unidad)
        magnitud = _CONVERSIONS[unit]
        return distancia * magnitud
    # Esta funcion es la que se encarga de calcular la distancia entre dos puntos con el metodo que se le indique
    def calcula_distancia(self, nombre_de_equipo_a, nombre_de_equipo_b):
        distancia = 0   
        #print(nombre_de_equipo_a)
        #print(nombre_de_equipo_b)
        #print(self.coordenadas_equipos)
        coordenadas_equipos = self.coordenadas_equipos
        #coordenadas_equipos['equipo'] = coordenadas_equipos['equipo']
        #coordenadas_equipos = coordenadas_equipos.drop_duplicates(subset=["equipo"], inplace=False)
        #print(type(coordenadas_equipos))
        #coordenadas_equipos = coordenadas_equipos.set_index("equipo")
        #print(coordenadas_equipos)
        #print("Equipo A: ",nombre_de_equipo_a)
        #print("Equipo B: ",nombre_de_equipo_b)
        #print("Lista de equipos con coordenadas BEFORE")
        #print(coordenadas_equipos)
        nombre_de_equipo_a = str(nombre_de_equipo_a)
        nombre_de_equipo_b = str(nombre_de_equipo_b)

        #equipo_b = coordenadas_equipos[coordenadas_equipos.index == nombre_de_equipo_b]
        
        # Check if the team name exists in the DataFrame
        if nombre_de_equipo_a in coordenadas_equipos['equipo'].unique():
            equipo_a = coordenadas_equipos[coordenadas_equipos["equipo"]==nombre_de_equipo_a]
            
            # Proceed with your calculations
        else:
            #pass
            #print(coordenadas_equipos['equipo'].unique())
            print(f"Team name '{nombre_de_equipo_b}' not found in the DataFrame.")
            
        # Check if the team name exists in the DataFrame
        if nombre_de_equipo_b in coordenadas_equipos['equipo'].unique():
            equipo_b = coordenadas_equipos[coordenadas_equipos["equipo"]==nombre_de_equipo_b]
            # Proceed with your calculations
        else:
            #pass
            #print(coordenadas_equipos['equipo'].unique())
            print(f"Team name '{nombre_de_equipo_b}' not found in the DataFrame.")
        #equipo_b = coordenadas_equipos[coordenadas_equipos["equipo"]==nombre_de_equipo_b]
        
        #print("Lista de equipos con coordenadas AFTER")
        #print(coordenadas_equipos)
        
        #print("Equipo A: ",equipo_a)
        #print("Equipo B: ",equipo_b)

        
        #equipo_a = float(equipo_a["lat"]), float(equipo_a["lon"])
        equipo_a = float(equipo_a["lat"].iloc[0]), float(equipo_a["lon"].iloc[0])
        equipo_b = float(equipo_b["lat"].iloc[0]), float(equipo_b["lon"].iloc[0])
        #print(type(equipo_a))
        #print(type(equipo_b))
        if self.metodo_calculo== "haversine":
            distancia = hav.haversine(equipo_a, equipo_b, unit=Unit(self.unidad_distancia))
        elif self.metodo_calculo== "euclidiano":
            distancia = self.euclidiano(equipo_a, equipo_b, unidad=Unit(self.unidad_distancia))
        #print("DIST ", distancia)
        #print(equipo_a)
        #print(equipo_b)
        return distancia
