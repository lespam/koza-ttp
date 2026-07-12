import os
import sys
import io
import time
import re
import ast
import datetime
import itertools
import random
import json

from django.conf import settings

import pandas as pd
import numpy

# --- BLOQUE CRÍTICO DE MATPLOTLIB ---
# Debe ir obligatoriamente ANTES de importar pyplot u otras librerías visuales
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
# ------------------------------------

from deap import base, creator, tools, gp
import pygraphviz as pgv

from programa_genetico.calculadora import Calculadora

creator.create("DateType", datetime.datetime)
creator.create("StrType", str)
creator.create("TupleType", tuple)
creator.create("ListType", list)

# Function to capture print output
def capture_print_output(expr):
    buffer = io.StringIO()
    sys.stdout = buffer
    print(expr)
    sys.stdout = sys.__stdout__
    output = buffer.getvalue()
    buffer.close()
    return output

def obtener_calendario(lista1, lista2):
    """ Esta funcion devuelve una lista con los elementos de dos listas """
    resultado = []
    if isinstance(lista1, list):
        for each in lista1:
            resultado.append(each)
    if isinstance(lista2, list):
        for each in lista2:
            resultado.append(each)
    def arity():
        return 2
    return resultado

def getFecha(fecha):
    def arity():
        return 1
    return "'" + pd.to_datetime(fecha)+ "'"

def getEquipo(equipo):
    def arity():
        return 1
    return equipo

def agregar_juego(juego):
    def arity():
        return 1
    return juego

def juegos_a_arbol(games, pset):
    calendar_str = "[]"
    for game in reversed(games()):
        if game != ():
            cfecha, equipo1, equipo2 = game
            fecha, _, _ = game
            calendar_str = f'obtener_calendario(crear_juego({fecha}, {equipo1}, {equipo2}, {calendar_str}), [])'
        else:
            calendar_str = f'obtener_calendario([], [])'
    return calendar_str

def juegos_str_a_arbol(games, pset):
    calendar_str = "[]"
    for game in reversed(games()):
        if game != ():
            cfecha, equipo1, equipo2 = game
            fecha, _, _ = game
            calendar_str = f'obtener_calendario(crear_juego({fecha}, {equipo1}, {equipo2}, {calendar_str}), [])'
        else:
            calendar_str = f'obtener_calendario([], [])'
            
    arbol = gp.PrimitiveTree.from_string(calendar_str, pset)
    return arbol


# ==========================================
# Clase ProgramaGenetico
# ==========================================
class ProgramaGenetico():
    def __init__(self):
        self.calculadora = Calculadora([], metodo="haversine", unidad="km")
        self.calendario_inicial = []
        self.equipos = []
        self.lista_de_fechas = []
        self.numero_de_juegos_por_equipo = 0
        self.numero_de_series_por_equipo = 0
        
        self.main_cal = gp.PrimitiveSet("MAIN_CAL", 0)
        self.pset_cal = gp.PrimitiveSetTyped("PSET_CAL", in_types=[creator.ListType], ret_type=creator.ListType)
        
        self.pset_inicial = gp.PrimitiveSetTyped("PSET_IN", in_types=[creator.ListType], ret_type=creator.ListType)
        self.pset = gp.PrimitiveSetTyped("MAIN", in_types=[], ret_type=creator.ListType)
        self.toolbox = base.Toolbox()
        
        self.generador_de_calendarios = None
        
    def crear_juego(self, fecha, equipo1, equipo2, lista):
        def arity():
            return 4
        fecha_bool = isinstance(fecha, str) and re.search(r'(\d+-\d+-\d+)', fecha)
        equipo1_bool = isinstance(equipo1, str) and re.search(r'[A-Z]{3}', equipo1)
        equipo2_bool = isinstance(equipo2, str) and re.search(r'[A-Z]{3}', equipo2)
        lista_bool = isinstance(lista, list)
        
        if fecha_bool and equipo1_bool and equipo2_bool and lista_bool:
            if equipo1 == equipo2:
                equipos_disponibles = [equipo for equipo in self.getEquipos() if equipo != equipo1]
                equipo2 = random.choice(equipos_disponibles) if equipos_disponibles else None
            fecha = "'" + str(datetime.datetime.strptime(fecha, "%Y-%m-%d").date().isoformat() )+ "'"
            juego = (fecha, equipo1, equipo2)
            respuesta = [juego] + lista
        else:
            juego = self.escoge_uno_de_cada_uno()
            respuesta = [juego] + lista if lista_bool else [juego]
        return respuesta
    
    def crear_juego2(self, fecha, equipo1, equipo2, lista):
        def arity():
            return 4
        fecha_bool = isinstance(fecha, str) and re.search(r'(\d+-\d+-\d+)', fecha)
        equipo1_bool = isinstance(equipo1, str) and re.search(r'[A-Z]{3}', equipo1)
        equipo2_bool = isinstance(equipo2, str) and re.search(r'[A-Z]{3}', equipo2)
        lista_bool = isinstance(lista, list)      
            
        if fecha_bool and equipo1_bool and equipo2_bool and lista_bool:
            if equipo1 == equipo2:
                juego = ()
            else:
                fecha = "'" + str(datetime.datetime.strptime(fecha, "%Y-%m-%d").date().isoformat() )+ "'"
                juego = (fecha, equipo1, equipo2)
            respuesta = [juego] + lista
        else:
            juego = ()
            respuesta = [juego] + lista if lista_bool else [juego]
        return respuesta

    # Getters y Setters
    def setCalculadora(self, coordenadas_equipos, metodo, unidad):
        self.calculadora = Calculadora(coordenadas_equipos, metodo, unidad)
    def getCalculadora(self):
        return self.calculadora
    def establecer_calendario_inicial(self, calendario_inicial):
        self.calendario_inicial = calendario_inicial
    def obtener_calendario_inicial(self):
        return self.calendario_inicial
    
    def formatear_calendario_inicial(self, calendario_inicial):
        calendario_inicial = pd.DataFrame(calendario_inicial, columns=["fecha_de_inicio", "equipo1", "equipo2"])
        nuevo_calendario = pd.DataFrame()
        nuevo_calendario["fecha"] =  "'" + pd.to_datetime(calendario_inicial["fecha_de_inicio"]).dt.strftime("%Y-%m-%d")+ "'"
        nuevo_calendario["equipo1"] = calendario_inicial["equipo1"]
        nuevo_calendario["equipo2"] = calendario_inicial["equipo2"]
        return nuevo_calendario
    
    def formatear_calendario(self, calendario):
        calendario = pd.DataFrame(calendario, columns=["fecha_de_inicio", "equipo1", "equipo2"])
        nuevo_calendario = pd.DataFrame()
        nuevo_calendario["fecha"] =  "'" + pd.to_datetime(calendario["fecha_de_inicio"]).dt.strftime("%Y-%m-%d")+ "'"
        nuevo_calendario["equipo1"] = calendario["equipo1"]
        nuevo_calendario["equipo2"] = calendario["equipo2"]
        return list(nuevo_calendario.itertuples(index=False, name=None))
    
    def set_genera_calendario(self, funcion):
        self.generador_de_calendarios = funcion
        
    def generador_de_calendarios_formateados(self):
        calendario = list(self.generador_de_calendarios())
        calendario = pd.DataFrame(calendario, columns=["fecha_de_inicio", "equipo1", "equipo2"])
        nuevo_calendario = pd.DataFrame()
        nuevo_calendario["fecha"] =  "'" + pd.to_datetime(calendario["fecha_de_inicio"]).dt.strftime("%Y-%m-%d")+ "'"
        nuevo_calendario["equipo1"] = calendario["equipo1"]
        nuevo_calendario["equipo2"] = calendario["equipo2"]
        return list(nuevo_calendario.itertuples(index=False, name=None))    
        
    def setEquipos(self, equipos):
        self.equipos = equipos
    def getEquipos(self):
        return self.equipos
    def setFechas(self, lista_de_fechas):
        self.lista_de_fechas = lista_de_fechas
    def getFechas(self):
        return self.lista_de_fechas
    def establecer_numero_de_juegos_por_equipo(self, numero):
        self.numero_de_juegos_por_equipo = numero
    def obtener_numero_de_juegos_por_equipo(self):
        return self.numero_de_juegos_por_equipo
    def establecer_numero_de_series_por_equipo(self, numero):
        self.numero_de_series_por_equipo = numero
    def obtener_numero_de_series_por_equipo(self):
        return self.numero_de_series_por_equipo
    def setPesetInicial(self, pset_inicial):
        self.pset_inicial = pset_inicial
    def getPsetInicial(self):
        return self.pset_inicial
    def setPset(self, pset):
        self.pset = pset
    def getPset(self):
        return self.pset
    def getPset_cal(self):
        return self.pset_cal
    def setToolbox(self, toolbox):
        self.toolbox = toolbox
    def getToolbox(self):
        return self.toolbox
    def getPsetMainCal(self):
        return self.main_cal
    def setPsetMainCal(self, main_cal):
        self.main_cal = main_cal
    
    # Evaluación
    def evalList(self, individual):
        toolbox = self.getToolbox()
        func = toolbox.compile(individual)
        result = type(func)
        return result,    
        
    def eval_calendario(self, individual):
        calendario = self.toolbox.compile(expr=individual)
        total_distance = 0.0
        for tupla in calendario:
            if tupla != ():
                fecha = tupla[0]
                equipo1 = tupla[1]
                equipo2 = tupla[2]
                distance = self.calculadora.calcula_distancia(equipo1, equipo2)
            else:
                distance = 0
            total_distance += distance

        num_juegos_semana = self.obtener_numero_de_juegos_por_equipo()
        num_juegos_esperado = num_juegos_semana
        
        juegos_por_equipo = {str(equipo): 0 for equipo in self.getEquipos()}
        for fecha in calendario:
            if fecha != ():
                juegos_por_equipo[str(fecha[1])] += 1
                juegos_por_equipo[str(fecha[2])] += 1

        total_diferencia = - sum(abs(juegos - num_juegos_esperado) for juegos in juegos_por_equipo.values())
        return total_diferencia, total_distance
    
    def parse_games(self, expr, pset):
        nexpr = capture_print_output(expr)
        input_string = nexpr
        pattern = r"crear_juego\('(\d{4}-\d{2}-\d{2})', '(\w+)', '(\w+)'"
        matches = re.findall(pattern, input_string)
        
        games = []
        for match in matches:
            fecha, equipo1, equipo2 = match
            games.append((fecha, equipo1, equipo2))
        return games        

    # Efímeras
    def fecha_aleatoria(self):
        respuesta = random.choice(self.lista_de_fechas)
        def arity():
            return 0
        return "'" + pd.to_datetime(respuesta).isoformat()+ "'"
        
    def equipo_aleatorio(self):
        equipo = random.choice(self.equipos)
        def arity():
            return 0
        return equipo
        
    def escoge_uno_de_cada_uno(self):
        fecha = self.fecha_aleatoria()
        equipo1 = self.equipo_aleatorio()
        equipo2 = self.equipo_aleatorio()
        if equipo1==equipo2:
            equipos_disponibles = [equipo for equipo in self.getEquipos() if equipo != equipo1]
            equipo2 = random.choice(equipos_disponibles) if equipos_disponibles else None
        def arity():
            return 0
        return [(fecha, equipo1, equipo2)]
    
    # Inicialización del Programa Genético
    def inicializar_programa_genetico(self):
        toolbox = self.getToolbox()
        toolbox.register("crear_juego", self.crear_juego)
        toolbox.register("obtener_calendario", obtener_calendario)
        toolbox.register("fecha", getFecha)
        toolbox.register("equipo", getEquipo)
        toolbox.register("juego", agregar_juego)
        
        pset_inicial = self.getPsetInicial()                
        pset_inicial.addPrimitive(toolbox.crear_juego, [creator.DateType, creator.StrType, creator.StrType, creator.ListType],  creator.ListType, name="crear_juego")
        pset_inicial.addPrimitive(toolbox.obtener_calendario, [creator.ListType, creator.ListType],  creator.ListType, name="obtener_calendario")
        pset_inicial.addPrimitive(toolbox.fecha, [creator.DateType], creator.DateType, name="Fecha")
        pset_inicial.addPrimitive(toolbox.equipo, [creator.StrType], creator.StrType, name="Equipo")
        pset_inicial.addPrimitive(toolbox.juego, [creator.ListType], creator.ListType, name="agregar_juego") 
        
        pset = self.getPset()
        pset.addPrimitive(toolbox.crear_juego, [creator.DateType, creator.StrType, creator.StrType, creator.ListType],  creator.ListType, name="crear_juego")
        pset.addPrimitive(toolbox.obtener_calendario, [creator.ListType, creator.ListType],  creator.ListType, name="obtener_calendario")
        pset.addPrimitive(toolbox.fecha, [creator.DateType], creator.DateType, name="Fecha")
        pset.addPrimitive(toolbox.equipo, [creator.StrType], creator.StrType, name="Equipo")
        pset.addPrimitive(toolbox.juego, [creator.ListType], creator.ListType, name="agregar_juego")
        pset.addTerminal([], ret_type=creator.ListType, name="[]")
        
        for each in self.getEquipos():
            pset_inicial.addTerminal(each, creator.StrType)
            pset.addTerminal(each, creator.StrType)
        for each in self.getFechas():
            pset_inicial.addTerminal(each, creator.DateType)
            pset.addTerminal(each, creator.DateType)
            
        calendario_inicial = self.obtener_calendario_inicial()
        calendario = self.formatear_calendario_inicial(calendario_inicial)
        calendario = list(calendario.itertuples(index=False, name=None))
        for each in calendario:
            pset_inicial.addTerminal([each], creator.ListType)
            pset.addTerminal([each], creator.ListType)
             
        toolbox.register("equipo_aleatorio", self.equipo_aleatorio)
        toolbox.register("fecha_aleatoria", self.fecha_aleatoria)
        
        pset.addEphemeralConstant("EquipoRandom", toolbox.equipo_aleatorio, creator.StrType)
        pset.addEphemeralConstant("FechaRandom", toolbox.fecha_aleatoria, creator.DateType)
        pset.addADF(pset_inicial)
        
        creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
        creator.create("Tree", gp.PrimitiveTree)
        creator.create("Individual", list, fitness=creator.FitnessMin)
        
        toolbox.register('pset_expr0', gp.genGrow, pset=pset_inicial, min_=2, max_=5)
        toolbox.register('main_expr', gp.genGrow, pset=pset, min_=2, max_=5)
        toolbox.register('NODE', tools.initIterate, creator.Tree, toolbox.pset_expr0)
        toolbox.register('ROOT', tools.initIterate, creator.Tree, toolbox.main_expr)
        
        func_cycle = [toolbox.ROOT, toolbox.NODE]
        psets = (pset, pset_inicial)
        
        toolbox.register('individual', tools.initCycle, creator.Individual, func_cycle, n=1)
        toolbox.register('population', tools.initRepeat, list, toolbox.individual)
        toolbox.register('compile', gp.compileADF, psets=psets)
        toolbox.register('evaluate', self.evalList)
        toolbox.register('select', tools.selTournament, tournsize=3)
        toolbox.register('mate', gp.cxOnePoint)
        toolbox.register('expr', gp.genGrow, min_=2, max_=5)
        toolbox.register('mutate', gp.mutUniform, expr=toolbox.expr)
        
        nuevo_texto = juegos_a_arbol(calendario, pset)
        nuevo_texto = gp.PrimitiveTree.from_string(nuevo_texto, pset)
        composed = toolbox.compile([nuevo_texto,None])
        respuesta = f'{composed}'
        grafica = gp.graph(nuevo_texto)
        self.genera_grafica(grafica)
        
        return respuesta
        
    def genera_grafica(self, grafica):
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        nodes, edges, labels = grafica
        
        g = pgv.AGraph()
        g.add_nodes_from(nodes)
        g.add_edges_from(edges)
        g.layout(prog="dot")
        
        # Guardar archivo dot
        dot_path = os.path.join(settings.BASE_DIR, 'file.dot')
        g.write(dot_path)
        
        # Directorios de Media QA
        media_path = os.path.join(settings.BASE_DIR, 'media')
        pdf_dir = os.path.join(media_path, 'pdf')
        wbmp_dir = os.path.join(media_path, 'wbmp')
        svg_dir = os.path.join(media_path, 'svg')
        
        os.makedirs(pdf_dir, exist_ok=True)
        os.makedirs(wbmp_dir, exist_ok=True)
        os.makedirs(svg_dir, exist_ok=True)
        
        for i in nodes:
            n = g.get_node(i)
            n.attr["label"] = labels[i]
            
        pdf_path = os.path.join(pdf_dir, f"ptree-{timestamp}.pdf")
        wbmp_path = os.path.join(wbmp_dir, "arbol.wbmp")
        svg_path = os.path.join(svg_dir, "arbol.svg")
        
        g.draw(str(pdf_path))
        g.draw(path=str(wbmp_path), format="cmapx")
        g.draw(str(svg_path), format="svg")
    
    # RUN
    def run(self):
        start = time.time()
        toolbox = self.getToolbox()
        toolbox.register("crear_juego", self.crear_juego2)
        toolbox.register("obtener_calendario", obtener_calendario)
        toolbox.register("fecha", getFecha)
        toolbox.register("equipo", getEquipo)
        
        calendario = self.formatear_calendario(self.generador_de_calendarios())
        self.establecer_calendario_inicial(calendario)
        
        self.main_cal = gp.PrimitiveSet("MAIN", 0)
        main_cal = self.getPsetMainCal()
        
        main_cal.addPrimitive(toolbox.crear_juego, 4)
        main_cal.addPrimitive(toolbox.obtener_calendario, 2)
        main_cal.addPrimitive(toolbox.fecha, 1)
        main_cal.addPrimitive(toolbox.equipo, 1)
        
        for each in self.getEquipos():
            main_cal.addTerminal(each)
        for each in self.getFechas():
            main_cal.addTerminal(each)
            
        toolbox.register("escoge_uno_de_cada_uno", self.escoge_uno_de_cada_uno)
        toolbox.register("equipo_aleatorio", self.equipo_aleatorio)
        main_cal.addEphemeralConstant("EquipoRandom", toolbox.equipo_aleatorio)

        creator.create("FitnessMin", base.Fitness, weights=(1.0, -1.0))
        creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMin)
        
        toolbox.register('genera_calendario', self.generador_de_calendarios_formateados)
        toolbox.register("juegos_str_a_arbol", juegos_str_a_arbol, games=toolbox.genera_calendario, pset = main_cal)
        toolbox.register('individual', tools.initIterate, creator.Individual, toolbox.juegos_str_a_arbol)
        toolbox.register('population', tools.initRepeat, list, toolbox.individual)
        toolbox.register('compile', self.parse_games, pset=main_cal)
        toolbox.register('evaluate', self.eval_calendario)
        toolbox.register('select', tools.selTournament, tournsize=15, fit_attr = 'fitness')
        toolbox.register('mate', gp.cxOnePointLeafBiased, termpb = 0)
        toolbox.register('expr', gp.genGrow, min_=10, max_=1000)
        toolbox.register('mutate', gp.mutNodeReplacement, pset=main_cal)
        
        CXPB, MUTPB, NGEN = 0.2, 0.1, 10
        POP_N = 100
        pop = toolbox.population(n=POP_N)
        hof = tools.HallOfFame(1)
        
        stats_equipos_con_juegos_incompletos = tools.Statistics(lambda ind: ind.fitness.values[0])
        stats_fitness = tools.Statistics(lambda ind: ind.fitness.values[1])
        mstats = tools.MultiStatistics(equipos_con_juegos_incompletos=stats_equipos_con_juegos_incompletos, fitness=stats_fitness)
        mstats.register("avg", numpy.mean)
        mstats.register("std", numpy.std)
        mstats.register("min", numpy.min)
        mstats.register("max", numpy.max)
        
        logbook = tools.Logbook()
        logbook.header = "gen", "evals", "equipos_con_juegos_incompletos", "fitness"
        logbook.chapters["equipos_con_juegos_incompletos"].header = "std", "min", "avg", "max"
        logbook.chapters["fitness"].header = "std", "min", "avg", "max"
        
        for ind in pop:
            ind.fitness.values = toolbox.evaluate(ind)
            
        hof.update(pop)
        record = mstats.compile(pop)
        logbook.record(gen=0, evals=len(pop), **record)
        print(logbook.stream)
        
        for g in range(1, NGEN):
            offspring = toolbox.select(pop, len(pop))
            offspring = [toolbox.clone(ind) for ind in offspring]
            
            for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:
                    toolbox.mate(ind1, ind2)
                    del ind1.fitness.values
                    del ind2.fitness.values
                    
            for ind in offspring:
                if random.random() < MUTPB:
                    toolbox.mutate(individual=ind, pset=main_cal)
                    del ind.fitness.values
                    
            invalids = [ind for ind in offspring if not ind.fitness.valid]
            for ind in invalids:
                ind.fitness.values = toolbox.evaluate(ind)
                
            pop = offspring
            hof.update(pop)
            record = mstats.compile(pop)
            logbook.record(gen=g, evals=len(invalids), **record)
            print(logbook.stream)

        # -----------------------------------------------------
        # SECCION DE GUARDADO (Archivos estructurados vía MEDIA)
        # -----------------------------------------------------
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        
        # 1. Guardar LOG (txt)
        txt_dir = os.path.join(settings.BASE_DIR, 'media', 'txt')
        os.makedirs(txt_dir, exist_ok=True)
        archivo_salida = os.path.join(txt_dir, f'output_{timestamp}.txt')
        with open(archivo_salida, 'w', encoding='utf-8') as f:
            f.write(str(logbook))
            
        textoa = hof[0]
        toolbox.register('t_expr', gp.PrimitiveTree.from_string, textoa, main_cal)
        texto = toolbox.compile(hof[0])
        
        # 2. Guardar CSV (Pandas)
        csv_dir = os.path.join(settings.BASE_DIR, 'media', 'csv')
        os.makedirs(csv_dir, exist_ok=True)
        archivo_csv = os.path.join(csv_dir, f'output_ind_{timestamp}.csv')
        pd.DataFrame(texto).to_csv(archivo_csv, index=False)

        # 3. Generar y guardar gráficas del Árbol (SVG, PDF, WBMP)
        grafica = gp.graph(hof[0])
        inicio_grafica = time.time()
        self.genera_grafica(grafica)
        fin_grafica = time.time()

        # 4. Generar y guardar Gráfica de Progreso (Matplotlib - JPG)
        gen = logbook.select("gen")
        size_avgs = logbook.chapters["equipos_con_juegos_incompletos"].select("avg")
        fit_mins = logbook.chapters["fitness"].select("avg")

        fig, ax1 = plt.subplots()
        line1 = ax1.plot(gen, size_avgs, "r-", label="Equipos con Juegos Incompletos por calendario")
        ax1.set_xlabel("Generation")
        ax1.set_ylabel("Fitness", color="b")
        for tl in ax1.get_yticklabels():
            tl.set_color("b")

        ax2 = ax1.twinx()
        line2 = ax2.plot(gen, fit_mins, "b-", label="Distancia promedio (Fitness)")
        ax2.set_ylabel("Equipos", color="r")
        for tl in ax2.get_yticklabels():
            tl.set_color("r")

        lns = line1 + line2
        labs = [l.get_label() for l in lns]
        ax1.legend(lns, labs, loc="center right")

        jpg_dir = os.path.join(settings.BASE_DIR, 'media', 'jpg')
        os.makedirs(jpg_dir, exist_ok=True)
        archivo_jpg = os.path.join(jpg_dir, f'my_plot_{timestamp}.jpg')
        plt.savefig(archivo_jpg, dpi=300, bbox_inches='tight')
        plt.close('all')

        end = time.time()
        total_time = (end - start)
        print(f"====TIEMPO==== {total_time}") 

        # 5. Guardar Información técnica (txt)
        archivo_info = os.path.join(txt_dir, f'output_info_{timestamp}.txt')
        with open(archivo_info, 'w', encoding='utf-8') as f:
            f.write(f"CXPB: {CXPB}, MUTPB: {MUTPB}, NGEN: {NGEN}, POP: {POP_N} \n")
            f.write(f"Diferencial de juegos: {hof[0].fitness.values[0]:,}\n")
            f.write(f"Distancia: {hof[0].fitness.values[1]:,} km\n")
            f.write(f"Tiempo (s): {total_time}")

        return (f'{texto}', hof[0].fitness.values[0])