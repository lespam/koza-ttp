import os
import csv
import datetime
import pandas as pd
from django.conf import settings
from django.utils.safestring import mark_safe
from .models import Calendario, Juego, Serie, Equipo, Torneo

def run_genetic_algorithm_logic(config):
    """
    Servicio centralizado encargado de inicializar el entorno, leer los recursos físicos
    como el CSV de equipos, mandar a ejecutar el algoritmo genético sobre el modelo 
    de Calendario activo y retornar los resultados calculados.
    """
    # 1. DEFINICIÓN DE RUTAS DEL PROYECTO
    ruta_svg = os.path.join(settings.BASE_DIR, 'media', 'svg', 'arbol.svg')
    ruta_csv = os.path.join(settings.BASE_DIR, 'static', 'csv', 'teams.csv')
    os.makedirs(os.path.dirname(ruta_svg), exist_ok=True)
    
    # 2. EXTRACCIÓN Y VERIFICACIÓN DE DATOS DEL CSV (Sincronización inicial)
    equipos_desde_csv = []
    if os.path.exists(ruta_csv):
        with open(ruta_csv, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                equipos_desde_csv.append(row)
    else:
        print(f"Advertencia en Tesis: Archivo de referencia ausente en: {ruta_csv}")

    # 3. IDENTIFICAR EL CALENDARIO ASOCIADO A LA CONFIGURACIÓN ACTIVA
    calendario_actual = config.calendario
    
    if calendario_actual:
        # 3.1 Ejecutar el Algoritmo Genético Real (Modificado para persistir en BD)
        # Este método ahora limpia la BD, ejecuta DEAP e inserta los nuevos juegos.
        resultado_ejecucion = calendario_actual.ejecutar_programa_genetico()
        
        arbol_generado = resultado_ejecucion[0]
        diferencia_calculada = resultado_ejecucion[1]  # Violaciones de restricciones / Fitness
        
        # 3.2 Extraer el cálculo matemático real del Costo de Viaje total
        distancia_calculada = calendario_actual.calcular_distancia(arbol_generado)
        
    else:
        arbol_generado = "Vacio"
        distancia_calculada = 0
        diferencia_calculada = 0

    # 4. EXTRACCIÓN Y VALIDACIÓN DE RENDERIZADO DEL ÁRBOL SVG (Graphviz)
    if os.path.exists(ruta_svg):
        with open(ruta_svg, "r", encoding="utf-8") as f:
            svg_content = mark_safe(f.read())
    else:
        # Fallback de seguridad en la interfaz por si hay retraso en la escritura del stream
        svg_content = mark_safe(
            f"<svg width='100%' height='80'>"
            f"<text x='15' y='45' fill='#d35400' font-family='Segoe UI' font-size='13' font-weight='600'>"
            f"Árbol en proceso / Expresión en Consola: {str(arbol_generado)[:55]}..."
            f"</text></svg>"
        )

    # 5. RETORNO DE CONTEXTO INTEGRADO HACIA DASHBOARDVIEW
    return {
        'svg_content': svg_content,
        'distancia': distancia_calculada,
        'diferencia': diferencia_calculada,
        'calendario': calendario_actual
    }