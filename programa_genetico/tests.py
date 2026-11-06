from unittest import mock

from django.test import SimpleTestCase

from programa_genetico.planificador import ModuloPlanificador
from programa_genetico.programagenetico import ProgramaGenetico


class _EquipoFalso:
    """Imita al modelo Equipo: la web pasa objetos, no cadenas."""

    def __init__(self, abreviatura):
        self.team_abbreviation = abreviatura

    def __str__(self):
        return self.team_abbreviation


class IniciarPlanificacionTests(SimpleTestCase):
    """Regresión del paso "Generar juegos" de la web.

    Antes fallaba con AttributeError (getProgramaGenetico no existe) y luego
    con TypeError en juegos_a_arbol (recibía una lista y la llamaba como función).
    """

    def test_iniciar_planificacion_genera_calendario_inicial(self):
        planificador = ModuloPlanificador()
        planificador.establecer_equipos([_EquipoFalso(a) for a in ("AAA", "BBB", "CCC", "DDD")])
        planificador.establecer_fechas(
            ["2026-04-06", "2026-04-07", "2026-04-08", "2026-04-09",
             "2026-04-11", "2026-04-13", "2026-04-14", "2026-04-15"])
        planificador.establecer_numero_de_juegos_por_equipo(2)
        planificador.setNumeroDeSeriesPorEquipo(2)

        # La gráfica del árbol necesita pygraphviz y escribe en media/; no es parte de esta prueba.
        with mock.patch.object(ProgramaGenetico, "genera_grafica"):
            resultado = planificador.iniciar_planificacion()

        juegos = planificador.obtener_calendario_inicial()
        self.assertEqual(len(juegos), 2 * 2 * 2)  # series * juegos * parejas por fecha
        self.assertIsInstance(resultado, str)


class MotorSeriesTests(SimpleTestCase):
    """El motor por series nunca rompe el número de juegos por equipo."""

    def test_juegos_por_equipo_se_conservan(self):
        import random

        from programa_genetico.motor_series import Instancia, evolucionar

        equipos = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]
        posiciones = {e: i for i, e in enumerate(equipos)}
        inst = Instancia(equipos, lambda a, b: abs(posiciones[a] - posiciones[b]),
                         num_series=6, dias_por_serie=3)
        cal0 = inst.calendario_aleatorio(random.Random(0))
        avance = []
        r = evolucionar(inst, cal0, generaciones=5, tam_poblacion=20, semilla=0,
                        on_generation=lambda g, c1, c2: avance.append(g))

        self.assertEqual(r.fitness[0], 0)  # C1 = 0: todos juegan 18
        self.assertEqual(inst.evaluar(r.mejor_calendario), r.fitness)
        self.assertLessEqual(r.fitness[1], r.historial[0][2])  # el elitismo nunca empeora
        self.assertEqual(avance, [0, 1, 2, 3, 4])

    def test_viaje_total_sigue_a_cada_equipo_serie_por_serie(self):
        from programa_genetico.motor_series import Calendario, Instancia

        pos = {"A": 0, "B": 1, "C": 5, "D": 6}
        inst = Instancia(list(pos), lambda a, b: abs(pos[a] - pos[b]), num_series=2, dias_por_serie=1)
        cal = Calendario([(("A", "B"), ("C", "D")), (("C", "A"), ("D", "B"))])
        # Serie 1: B va a A (1), D va a C (1).
        # Serie 2: A va de A a C (5), C se queda (0), D va de C a D (1), B va de A a D (6).
        # Regreso a casa: A de C (5), B de D (5), C y D ya están en casa.
        self.assertEqual(inst.viaje_total(cal), 24)
