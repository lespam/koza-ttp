from unittest import mock

from django.test import SimpleTestCase

from programa_genetico.planificador import ModuloPlanificador
from programa_genetico.programagenetico import ProgramaGenetico, cruce_un_punto_sesgado


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


class CruceTests(SimpleTestCase):
    """deap.gp.cxOnePointLeafBiased falla en Python 3.11+ (random.sample con un set)."""

    def test_cruce_intercambia_subarboles_del_mismo_tipo(self):
        import operator
        from deap import gp
        pset = gp.PrimitiveSet("MAIN", 0)
        pset.addPrimitive(operator.add, 2)
        pset.addTerminal(1)
        pset.addTerminal(2)
        a = gp.PrimitiveTree.from_string("add(add(1, 1), 1)", pset)
        b = gp.PrimitiveTree.from_string("add(2, add(2, 2))", pset)
        nodos = len(a) + len(b)
        a, b = cruce_un_punto_sesgado(a, b, termpb=0)
        self.assertEqual(len(a) + len(b), nodos)
        self.assertEqual(str(a).count("1") + str(b).count("1"), 3)


class GraficaArbolTests(SimpleTestCase):
    """Regresión: los nodos del árbol se encimaban en la gráfica.

    Las etiquetas se ponían después de calcular el acomodo de Graphviz.
    """

    def test_nodos_del_mismo_nivel_no_se_enciman(self):
        try:
            from programa_genetico.programagenetico import construir_grafica_arbol
            construir_grafica_arbol([0], [], {0: "x"})
        except ImportError:
            self.skipTest("pygraphviz no está instalado")

        etiquetas = {0: "crear_juego", 1: "New York Yankees", 2: "Boston Red Sox",
                     3: "2026-04-01", 4: "EquipoRandom"}
        aristas = [(0, 1), (0, 2), (0, 3), (0, 4)]
        g = construir_grafica_arbol(list(etiquetas), aristas, etiquetas)

        cajas = []
        for nodo in g.nodes():
            x, y = map(float, nodo.attr["pos"].split(","))
            cajas.append((x, y, float(nodo.attr["width"]) * 72))
        for i, a in enumerate(cajas):
            for b in cajas[i + 1:]:
                if abs(a[1] - b[1]) < 1:  # mismo nivel
                    self.assertGreaterEqual(abs(a[0] - b[0]), (a[2] + b[2]) / 2)
        self.assertEqual(g.get_node(1).attr["label"], "New York Yankees")


class CalendarioGrandeTests(SimpleTestCase):
    """Regresión: con más de unos 100 juegos, gp.compile (eval) lanzaba
    SyntaxError "too many nested parentheses" en "Generar juegos"."""

    def test_iniciar_planificacion_con_muchos_juegos(self):
        planificador = ModuloPlanificador()
        equipos = [_EquipoFalso(letra * 3) for letra in "ABCDEFGHIJ"]
        planificador.establecer_equipos(equipos)
        planificador.establecer_fechas([f"2026-05-{dia:02d}" for dia in range(1, 31)])
        planificador.establecer_numero_de_juegos_por_equipo(3)
        planificador.setNumeroDeSeriesPorEquipo(10)

        with mock.patch.object(ProgramaGenetico, "genera_grafica"):
            resultado = planificador.iniciar_planificacion()

        self.assertGreater(len(planificador.obtener_calendario_inicial()), 100)
        self.assertIsInstance(resultado, str)
