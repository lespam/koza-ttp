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

    def test_reglas_de_localia_y_rivales_entran_en_c1(self):
        from programa_genetico.motor_series import Calendario, Instancia

        pos = {"A": 0, "B": 1, "C": 5, "D": 6}
        inst = Instancia(list(pos), lambda a, b: abs(pos[a] - pos[b]), num_series=2,
                         dias_por_serie=1, tolerancia_casa=0, max_series_pareja=1)
        # A y C juegan las dos series en casa (2 en casa; lo justo es 1) y
        # las parejas A-B y C-D se repiten (máximo 1 serie).
        cal = Calendario([(("A", "B"), ("C", "D")), (("A", "B"), ("C", "D"))])
        # Localía: A +1, B -1, C +1, D -1 -> 4 juegos. Rivales: 2 parejas con 1 de más -> 2.
        self.assertEqual(inst.penalizacion(cal), 6)
        self.assertEqual(inst.evaluar(cal)[0], -6)

    def test_combinar_con_adf1_conserva_las_reglas_duras(self):
        import random

        from programa_genetico.motor_series import Instancia, evolucionar

        equipos = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]
        posiciones = {e: i for i, e in enumerate(equipos)}
        inst = Instancia(equipos, lambda a, b: abs(posiciones[a] - posiciones[b]),
                         num_series=6, dias_por_serie=3)
        r = evolucionar(inst, inst.calendario_aleatorio(random.Random(1)), generaciones=4,
                        tam_poblacion=20, semilla=1, combinar=True)
        self.assertEqual(len(r.mejor_individuo), 3)  # MAIN, ADF0, ADF1
        conteo = {e: 0 for e in equipos}
        for serie in r.mejor_calendario:
            for a, b in serie:
                conteo[a] += 3
                conteo[b] += 3
        self.assertEqual(set(conteo.values()), {18})

    def test_intercambiar_series_solo_cambia_el_orden(self):
        from programa_genetico.motor_series import Calendario, Instancia, intercambiar_series

        pos = {"A": 0, "B": 1, "C": 5, "D": 6}
        inst = Instancia(list(pos), lambda a, b: abs(pos[a] - pos[b]), num_series=3, dias_por_serie=1)
        cal = Calendario([(("A", "B"), ("C", "D")), (("C", "A"), ("D", "B")), (("A", "D"), ("B", "C"))])
        otro = intercambiar_series(cal, 0, 1)
        self.assertEqual(otro, Calendario([cal[1], cal[0], cal[2]]))
        self.assertEqual(inst.penalizacion(otro), inst.penalizacion(cal))
        self.assertEqual((inst.viaje_total(cal), inst.viaje_total(otro)), (44, 42))

    def test_reglas_por_division_liga_e_interliga(self):
        from programa_genetico.motor_series import Calendario, Instancia, ReglaNivel

        # 2 ligas x 1 división x 2 equipos: A-B y C-D son división, A-C liga no existe,
        # así que A-C, A-D, B-C, B-D son interliga.
        divisiones = {"X Div": ["A", "B"], "Y Div": ["C", "D"]}
        reglas = {
            "division": ReglaNivel(juegos=2, tolerancia=0, min_series=2, max_series=2),
            "liga": ReglaNivel(juegos=0, tolerancia=0, min_series=0, max_series=0),
            "interliga": ReglaNivel(juegos=2, tolerancia=0, min_series=1, max_series=1),
        }
        inst = Instancia(["A", "B", "C", "D"], lambda a, b: 1.0, num_series=4, dias_por_serie=1,
                         tolerancia_casa=None, divisiones=divisiones, reglas_nivel=reglas)
        bueno = Calendario([(("A", "B"), ("C", "D")), (("A", "C"), ("B", "D")),
                            (("A", "D"), ("B", "C")), (("B", "A"), ("D", "C"))])
        self.assertEqual(inst.penalizacion(bueno), 0)
        malo = Calendario([(("A", "B"), ("C", "D"))] * 4)
        self.assertGreater(inst.penalizacion(malo), 0)


class MotorBloquesTests(SimpleTestCase):
    """Cada ADF es un calendario: las reglas por nivel se cumplen por construcción."""

    def _instancia(self, **kw):
        from programa_genetico.motor_bloques import REGLAS_BLOQUES
        from programa_genetico.motor_series import MLB_DIVISIONES, Instancia

        equipos = [e for lista in MLB_DIVISIONES.values() for e in lista]
        pos = {e: (i % 6, i // 6) for i, e in enumerate(equipos)}
        return Instancia(equipos, lambda a, b: abs(pos[a][0] - pos[b][0]) + abs(pos[a][1] - pos[b][1]),
                         divisiones=MLB_DIVISIONES, reglas_nivel=REGLAS_BLOQUES, **kw)

    def test_bloques_aleatorios_cumplen_las_reglas_por_nivel(self):
        import random

        from programa_genetico.motor_bloques import Bloques, Jerarquia
        from programa_genetico.motor_series import MLB_DIVISIONES

        inst = self._instancia(tolerancia_casa=None)
        jer = Jerarquia(MLB_DIVISIONES)
        for semilla in range(5):
            cal = Bloques.aleatorios(jer, random.Random(semilla)).ensamblar_simple()
            self.assertEqual(len(cal), 54)
            self.assertEqual(inst.evaluar(cal)[0], 0)

    def test_evolucion_conserva_las_reglas(self):
        import random

        from programa_genetico.motor_bloques import Bloques, Jerarquia, evolucionar
        from programa_genetico.motor_series import MLB_DIVISIONES

        inst = self._instancia(tolerancia_casa=None)
        bloques = Bloques.aleatorios(Jerarquia(MLB_DIVISIONES), random.Random(0))
        r = evolucionar(inst, bloques, generaciones=3, tam_poblacion=10, semilla=0)
        self.assertEqual(r.fitness[0], 0)
        self.assertEqual(len(r.mejor_individuo), 5)  # ADF_liga, ADF_division, ADF_interliga, ADF_serie, AJUSTE


class MotorTurnosTests(SimpleTestCase):
    """Series de 2, 3 y 4 juegos con descansos: no todos juegan al mismo tiempo."""

    def _calendario(self, semilla=0):
        import random

        from programa_genetico.motor_series import MLB_DIVISIONES
        from programa_genetico.motor_turnos import CalendarioTurnos, series_mlb_2023

        equipos = [e for lista in MLB_DIVISIONES.values() for e in lista]
        pos = {e: (i % 6, i // 6) for i, e in enumerate(equipos)}
        rng = random.Random(semilla)
        cal = CalendarioTurnos(series_mlb_2023(rng), equipos,
                               lambda a, b: abs(pos[a][0] - pos[b][0]) + abs(pos[a][1] - pos[b][1]))
        self.assertTrue(cal.construir(rng))
        return cal, rng

    def _sin_choques(self, cal):
        for e in range(len(cal.equipos)):
            for t in range(cal.T):
                k = cal.en[e][t]
                if k >= 0:
                    self.assertEqual(cal.turno[k], t)
                    self.assertIn(e, (cal.local[k], cal.visita[k]))
        for k, t in enumerate(cal.turno):
            self.assertEqual(cal.en[cal.local[k]][t], k)
            self.assertEqual(cal.en[cal.visita[k]][t], k)

    def test_estructura_mlb_2023(self):
        import random
        from collections import Counter

        from programa_genetico.motor_turnos import series_mlb_2023

        series = series_mlb_2023(random.Random(3))
        juegos, casa, num = Counter(), Counter(), Counter()
        for h, a, n in series:
            juegos[h] += n
            juegos[a] += n
            casa[h] += n
            num[h] += 1
            num[a] += 1
        self.assertEqual(set(juegos.values()), {162})
        self.assertEqual(set(casa.values()), {81})
        self.assertEqual(set(num.values()), {52})
        self.assertEqual({n for _, _, n in series}, {2, 3, 4})

    def test_construccion_y_recocido_sin_choques(self):
        from programa_genetico.motor_turnos import recocido

        cal, rng = self._calendario()
        self._sin_choques(cal)
        antes = cal.evaluar()
        despues = recocido(cal, rng, pasos=3000)
        self._sin_choques(cal)
        self.assertEqual(despues, cal.evaluar())
        self.assertLessEqual(despues[0], antes[0])

    def test_pg_no_rompe_el_calendario(self):
        from programa_genetico.motor_turnos_pg import busqueda_aleatoria, evolucionar

        cal, _ = self._calendario(2)
        antes = cal.evaluar()
        r = evolucionar(cal, generaciones=2, tam_poblacion=4, repeticiones=1, semilla=0)
        self._sin_choques(r.mejor_calendario)
        self.assertEqual(r.fitness, r.mejor_calendario.evaluar())
        self.assertLessEqual((r.fitness[0], r.fitness[1]), (antes[0], antes[1] + 1e-6))
        self.assertEqual(len(r.mejor_individuo), 2)  # ADF_turno, AJUSTE
        otro, _ = self._calendario(2)
        c, fit = busqueda_aleatoria(otro, 500, __import__("random").Random(1))
        self._sin_choques(c)

    def test_medicion_de_juegos_por_fecha(self):
        from programa_genetico.motor_turnos import haversine_km, medir_juegos

        cal, _ = self._calendario(1)
        coords = {e: (30 + i % 6, -100 + i // 6) for i, e in enumerate(cal.equipos)}
        juegos = cal.juegos_por_fecha()
        self.assertEqual(len(juegos), 2430)
        m = medir_juegos(juegos, coords)
        self.assertEqual(m["juegos"], (162, 162))
        # La medición independiente coincide con el costo del modelo.
        cal.D = [[haversine_km(coords[a], coords[b]) for b in cal.equipos] for a in cal.equipos]
        self.assertAlmostEqual(m["km"], cal.evaluar()[1], delta=1)


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
