# tesis/services.py
import os
from django.conf import settings

def run_genetic_algorithm_logic(config):
    # ... tu lógica de DEAP ...
    
    # Asegúrate de crear el directorio si no existe
    ruta_svg = os.path.join(settings.BASE_DIR, 'media', 'svg', 'arbol.svg')
    os.makedirs(os.path.dirname(ruta_svg), exist_ok=True)
    
    # Dibuja el grafo
    # graph.draw(ruta_svg, prog='dot', format='svg') 
    # Asegúrate de que el objeto graph se cierre o destruya aquí
    
    # LEER EL CONTENIDO RECIÉN CREADO
    # Agregamos una pequeña validación para asegurar que el archivo tenga contenido
    if os.path.exists(ruta_svg):
        with open(ruta_svg, "r", encoding="utf-8") as f:
            svg_content = f.read()
    else:
        svg_content = "<svg><text>Error: No se generó el archivo SVG</text></svg>"

    return {
        'arbol': "...",
        'svg_content': svg_content, # Pasamos el contenido leído
        'distancia': 0.0,
        'diferencia': 0.0
    }