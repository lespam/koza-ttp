import random
from typing import List, Any, Dict, Tuple
from datetime import datetime, time
import pandas as pd
from django.utils.timezone import get_default_timezone


#import programa_genetico
#import sys
#sys.path.append('/home/ubuntu/django-gunicorn-nginx')
from programa_genetico.programagenetico import ProgramaGenetico


class ModuloPlanificador():
    def __init__(self) -> None:
        """Inicializa el módulo planificador con parámetros por defecto."""
        self.programa_genetico = ProgramaGenetico()
        self.equipos = []
        self.fechas = []
        self.fecha_de_inicio = pd.to_datetime("")
        self.fecha_de_fin = pd.to_datetime("")
        self.numero_de_juegos = 1
        self.numero_de_series = 1
        self.numero_de_juegos_torneo = 1
        self.dias_seleccionados = ""
        self.coordenadas_equipos = pd.DataFrame()
        self.metodo_calculo= "haversine"
        self.unidad_distancia = "km"
        self.calendario_inicial = []
    
    def inicializar_planificador(self) -> bool:
        """
        Inicializa el planificador. Actualmente, siempre devuelve True.
        
        Returns:
            bool: True si la operación fue exitosa, False de lo contrario.
        """
        success = True
        return success
    
    def set_programa_genetico(self, programa_genetico: ProgramaGenetico) -> bool:
        """
        Establece el programa genético para el planificador.
        
        Args:
            programa_genetico (ProgramaGenetico): El programa genético a establecer.
        
        Returns:
            bool: True si la operación fue exitosa, False de lo contrario.
        """
        self.programa_genetico = programa_genetico
        return True
    
    def get_programa_genetico(self) -> ProgramaGenetico:
        """
        Obtiene el programa genético configurado.
        
        Returns:
            ProgramaGenetico: Una instancia de la clase ProgramaGenetico.
        """
        return self.programa_genetico
    
    def establecer_numero_de_juegos_por_equipo(self, numero_de_juegos: int) -> bool:
        """
        Establece el número de juegos por equipo.
        
        Args: numero_de_juegos (int): el número de juegos por equipo.
        
        Returns:
            bool: True si la operación fue exitosa, False de lo contrario.
        """
        self.numero_de_juegos = numero_de_juegos
        return True
    
    def obtener_numero_de_series_por_equipo(self) -> int:
        """
        Obtiene el número de series por equipo configurado.
        
        Return:
            int: El número de series que cada equipo juega.
        """
        return self.numero_de_series
    
    def obtener_numero_de_juegos_por_equipo(self) -> int:
        """
        Obtiene el número de juegos por equipo en el torneo.

        Returns:
            int: El número de juegos por equipo en el torneo.
        """
        return self.numero_de_juegos
    
    def setNumeroDeJuegosPorEquipoTorneo(self, numero):
        self.numero_de_juegos_por_equipo_torneo = numero
    
    def getNumeroDeSeriesPorEquipo(self) -> int:
        return self.numero_de_series
    
    def setNumeroDeSeriesPorEquipo(self, numero_de_series: int) -> bool:
        self.numero_de_series = numero_de_series
        return True
    
    def establecer_dias_seleccionados(self, dias_seleccionados: str) -> bool:
        """
        Establece los días de juego para el torneo.

        Args:
            dias_seleccionados (str): Un string que representa los días de juego.

        Returns:
            bool: True si la operación fue exitosa.
        """
        self.dias_seleccionados = dias_seleccionados
        return True
    
    def obtener_dias_seleccionados(self) -> str:
        """
        Obtiene los días de juego para el torneo.

        Returns:
            str: Los días de juego en formato string.
        """
        return self.dias_seleccionados
    
    
    def establecer_equipos(self, equipos: list) -> bool:
        """
        Establece la lista de equipos y actualiza el programa genético con ellos.

        Args:
            equipos (list): Una lista de equipos.

        Returns:
            bool: True si la operación fue exitosa.
        """
        self.equipos = equipos
        self.programa_genetico.setEquipos(equipos)
        return True
    
    def obtener_equipos(self) -> list:
        """
        Obtiene la lista de equipos.

        Returns:
            list: La lista de equipos.
        """
        return self.equipos
    
    def establecer_fecha_de_inicio(self, fecha_de_inicio: str) -> bool:
        """
        Establece la fecha de inicio del torneo.

        Args:
            fecha_de_inicio (str): La fecha de inicio en formato string.

        Returns:
            bool: True si la operación fue exitosa.
        """
        self.fecha_de_inicio = pd.to_datetime(fecha_de_inicio)
        return True
    
    def obtener_fecha_de_inicio(self) -> pd.Timestamp:
        """
        Obtiene la fecha de inicio del torneo.

        Returns:
            pd.Timestamp: La fecha de inicio del torneo.
        """
        return self.fecha_de_inicio
    
    def establecer_fecha_de_fin(self, fecha_de_fin: str) -> bool:
        """
        Establece la fecha de fin del torneo.

        Args:
            fecha_de_fin (str): La fecha de fin en formato string.

        Returns:
            bool: True si la operación fue exitosa.
        """
        self.fecha_de_fin = pd.to_datetime(fecha_de_fin)
        return True
    
    def obtener_fecha_de_fin(self) -> pd.Timestamp:
        """
        Obtiene la fecha de fin del torneo.

        Returns:
            pd.Timestamp: La fecha de fin del torneo.
        """
        return self.fecha_de_fin
    
    def establecer_fechas(self, fechas: list) -> bool:
        """
        Establece la lista de fechas y actualiza el programa genético con ellas.

        Args:
            fechas (list): Una lista de fechas.

        Returns:
            bool: True si la operación fue exitosa.
        """
        self.fechas = fechas
        #self.programa_genetico.setFechas(fechas)
        return True
    
    def obtener_fechas(self) -> list:
        """
        Obtiene la lista de fechas.

        Returns:
            list: La lista de fechas.
        """
        return self.fechas
    
    #def getEquiposDeProgramaGenetico(self) -> list:
    #    return self.programa_genetico.getEquipos()
    
    def establecer_coordenadas_equipos(self, coordenadas_equipos) -> bool:
        """
        Establece la lista de equipos con coordenadas.

        Args:
            coordenadas_equipos: Una lista de equipos con coordenadas.

        Returns:
            bool: True si la operación fue exitosa.
        """
        self.coordenadas_equipos = coordenadas_equipos
        return True
    
    def obtener_coordenadas_equipos(self):
        """
        Obtiene la lista de equipos con coordenadas.

        Returns:
            La lista de equipos con coordenadas.
        """
        return self.coordenadas_equipos
    
    def establecer_calendario_inicial(self, calendario_inicial):
        """
        Establece el calendario inicial.

        Args:
            calendario_inicial: El calendario inicial para el planificador.
        """
        self.calendario_inicial = calendario_inicial
        
    def obtener_calendario_inicial(self):
        """
        Obtiene el calendario inicial.

        Returns:
            El calendario inicial.
        """
        return self.calendario_inicial
    
    def crear_calendario_inicial(self):
        """
        Genera el calendario inicial para el planificador.
        
        Returns:
            list: Una lista de juegos generados.
        """
        dias_de_semana = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
        dias_seleccionados = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Sabado']
        lista_dia_de_semana = pd.DataFrame(dias_de_semana, index=range(7), columns=['Dia'])
        dias_seleccionados = lista_dia_de_semana[lista_dia_de_semana['Dia'].isin(dias_seleccionados)].index.to_list()
        num_dias_seleccionados = len(dias_seleccionados)
        #calendario_inicial = []
        #lista_de_series = []
        lista_de_fechas_disponibles = self.obtener_fechas()
        lista_de_fechas_disponibles = [fecha for fecha in lista_de_fechas_disponibles if pd.to_datetime(fecha).dayofweek in dias_seleccionados]
        
        tz = get_default_timezone()
        start_time = time(9, 0)  # 9:00 AM
        end_time = time(12, 0)  # 12:00 PM
        
        numero_de_juegos = self.obtener_numero_de_juegos_por_equipo()
        numero_de_series = self.obtener_numero_de_series_por_equipo()
        numero_de_juegos_esperado = numero_de_juegos * numero_de_series
        #numero_de_juegos_torneo = self.obtener_numero_de_juegos_por_equipo_por_torneoTorneo()
        
        lista_de_fechas = lista_de_fechas_disponibles[:numero_de_juegos_esperado]
        #print(f'lista de fechas {lista_de_fechas}')
        self.establecer_fechas(lista_de_fechas)
        
        juegos = []
        fecha_iter = 0
        equipos = self.obtener_equipos()
        lista_de_equipos = [equipo for equipo in equipos]
        
        print(f"El numero de series es {numero_de_series}")
        print(f"El numero de juegos es {numero_de_juegos}")
        
        for k in range(numero_de_series):
            random.shuffle(lista_de_equipos)
            if len(lista_de_equipos) % 2 != 0:
                # Si es impar eliminamos el ultimo equipo
                lista_de_equipos = lista_de_equipos[:-1]
            else:
                pass
            pares = [(lista_de_equipos[j], lista_de_equipos[j+1]) for j in range(0, len(lista_de_equipos), 2)]
            for i in range(numero_de_juegos):
                #print(f'Numero de juego: {i+1}')
                # Creamos una fecha datetime con la
                # fecha de inicio y la hora de inicio
                # del juego para los juegos de esta serie
                # print(f'fechas {i}: {lista_de_fechas[i]}')
                if fecha_iter >= len(lista_de_fechas):
                    break
                if fecha_iter % num_dias_seleccionados == 0:
                    random.shuffle(lista_de_equipos)
                    pares = [(lista_de_equipos[j], lista_de_equipos[j+1]) for j in range(0, len(lista_de_equipos), 2)]
                fecha_i = datetime.strptime(lista_de_fechas[fecha_iter], "%Y-%m-%d").date()  # This is a datetime.date 
                fecha_de_inicio = datetime.combine(fecha_i, start_time).replace(tzinfo=tz)
                fecha_de_fin = datetime.combine(fecha_i, end_time).replace(tzinfo=tz)
                n_serie = k + 1
                for par in pares:
                    juego_dict = {
                        'numero_de_serie': n_serie,
                        'fecha_de_inicio': fecha_de_inicio,
                        'fecha_de_fin': fecha_de_fin,
                        'equipo1': par[0],
                        'equipo2': par[1]}
                    # Agregamos el juego a la lista de juegos
                    juegos.append(juego_dict)
                fecha_iter = fecha_iter + 1
        return juegos

    def iniciar_planificacion(self):
        """
        Inicia el planificador generando el calendario inicial y configurando el programa genético.
        
        Returns:
            El resultado de inicializar el programa genético.
        """
        calendario_inicial = self.crear_calendario_inicial()
        self.establecer_calendario_inicial(calendario_inicial)
        pg = self.getProgramaGenetico()
        
        pg.establecer_calendario_inicial(calendario_inicial)
        pg.setCalculadora(self.obtener_coordenadas_equipos(), self.metodo_calculo, self.unidad_distancia)
        pg.setEquipos(self.obtener_equipos())
        pg.setFechas(self.obtener_fechas())
        pg.establecer_numero_de_juegos_por_equipo(self.obtener_numero_de_juegos_por_equipo())
        pg.establecer_numero_de_series_por_equipo(self.getNumeroDeSeriesPorEquipo())   
        
        pg.set_genera_calendario(self.crear_calendario_inicial)
        
        result = pg.inicializar_programa_genetico()
        
        return result
    
    def obtener_expresion(self):
        """
        Crea un árbol de expresiones para el programa genético y lo devuelve.
        
        Returns:
            El árbol de expresiones generado.
        """
        pg = self.getProgramaGenetico()
        result = pg.crear_arbol()
        return result
    
    def calcular_distancia_en_casa(self, juegos, equipo):
        """
        Calcula la distancia total que un equipo tiene que recorrer en casa.
        
        Args:
            juegos (list): La lista de juegos.
            equipo (str): El equipo para el que se calcula la distancia.
            
        Returns:
            float: La distancia total que el equipo tiene que recorrer en casa.
        """
        calendario = pd.DataFrame(juegos)
        pg = self.getProgramaGenetico()
        pg.setCalculadora(self.obtener_coordenadas_equipos(), self.metodo_calculo, self.unidad_distancia)        
        calculadora = pg.getCalculadora()
        distancia_en_casa = 0.0
        for tupla in calendario:
            fecha = tupla[0]
            equipo1 = tupla[1]
            equipo2 = tupla[2]
            distancia_juego = calculadora.calcula_distancia(equipo1, equipo2)
            if equipo1 == equipo:
                distancia_en_casa += distancia_juego
        return distancia_en_casa
    
    def calcular_distancia(self, expresion: str) -> float:
        """
        Calcula la distancia total para una expresión dada.
        
        Args:
            expresion (str): La expresión para la que se calcula la distancia.
            
        Returns:
            float: La distancia total calculada.
        """
        pg = self.get_programa_genetico()
        pg.setCalculadora(self.obtener_coordenadas_equipos(), self.metodo_calculo, self.unidad_distancia)        
        calculadora = pg.getCalculadora()
        calendario = eval(expresion)
        total_distance = 0.0
        for tupla in calendario:
            if tupla != ():
                fecha = tupla[0]
                equipo1 = tupla[1]
                equipo2 = tupla[2]
                distance = calculadora.calcula_distancia(equipo1, equipo2)
            else:
                distance = 0
            total_distance += distance    
        return total_distance

    def ejecutar_programa_genetico(self):
        """
        Ejecuta el programa genético y devuelve el resultado.
        
        Returns:
            str: El resultado de ejecutar el programa genético.
        """
        calendario_inicial = self.crear_calendario_inicial()
        self.establecer_calendario_inicial(calendario_inicial)
        
        pg = self.get_programa_genetico()
        
        pg.establecer_calendario_inicial(calendario_inicial)
        pg.setCalculadora(self.obtener_coordenadas_equipos(), self.metodo_calculo, self.unidad_distancia)
        pg.setEquipos(self.obtener_equipos())
        pg.setFechas(self.obtener_fechas())
        
        pg.establecer_numero_de_juegos_por_equipo(self.obtener_numero_de_juegos_por_equipo())
        pg.establecer_numero_de_series_por_equipo(self.getNumeroDeSeriesPorEquipo())        
        
        pg.set_genera_calendario(self.crear_calendario_inicial)
        print("SE SOLICITO RESULTADOOOOOO")
        
        result = pg.run()
        print("SE RECIBVIO RESULTADOOOOOO")
        resulta = result[0]
        resultb = result[1]
        
        return [resulta, resultb]
    
    def ejecutar_programa_genetico_alt(self):
        """
        Ejecuta una versión alternativa del programa genético y devuelve el resultado.
        
        Returns:
            str: El resultado de ejecutar la versión alternativa del programa genético.
        """
        calendario_inicial = self.crear_calendario_inicial()
        self.establecer_calendario_inicial(calendario_inicial)
        pg = self.get_programa_genetico()
        
        pg.establecer_calendario_inicial(calendario_inicial)
        pg.setCalculadora(self.obtener_coordenadas_equipos(), self.metodo_calculo, self.unidad_distancia)
        pg.setEquipos(self.obtener_equipos())
        pg.setFechas(self.obtener_fechas())
        pg.establecer_numero_de_juegos_por_equipo(self.obtener_numero_de_juegos_por_equipo())
        pg.establecer_numero_de_series_por_equipo(self.getNumeroDeSeriesPorEquipo())        
        result = pg.run_alt()
        result = str(result)
        return result