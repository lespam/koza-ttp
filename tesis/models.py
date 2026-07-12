import datetime
import re
import pandas as pd
from django import forms
from django.db import models
from django.db import models
from django.forms import CheckboxSelectMultiple, ModelForm
from django.urls import reverse

#import sys
from programa_genetico.planificador import ModuloPlanificador

class User(models.Model):
    """User Model:
    This model represents the User class.
    args:
        name: CharField for the user's name.
        email: EmailField for the user's email address.
        password: CharField for the user's password.
        created_at: DateTimeField for the date and time the user was created.
        updated_at: DateTimeField for the date and time the user was last updated.
    """
    name = models.CharField(max_length=100)
    email = models.EmailField()
    password = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Equipo(models.Model):
    """ Equipo Model:
    This model represents the Equipo class.
    args:
        Team Abbreviation: CharField for the team's abbreviation.
        Nickname: CharField for the team's nickname.
        League (National or American): CharField for the team's league.
        Team Name: CharField for the team's name.
        Arena Name: CharField for the team's arena name.
        Arena Location: CharField for the team's arena location.
        City: CharField for the team's city.
        Seating Capacity: IntegerField for the team's seating capacity.
        Opening Year: IntegerField for the team's opening year.
        Lat: FloatField for the team's latitude.
        Lon: FloatField for the team's longitude.
        Address: CharField for the team's address.
        First year of this combination: IntegerField for the team's first year of this combination.
        Last year of this combination: IntegerField for the team's last year of this combination.
    """
    team_abbreviation = models.CharField(max_length=100, blank=True, null=True, unique=True)
    nickname = models.CharField(max_length=100, blank=True, null=True)
    league = models.CharField(max_length=100,  blank=True, null=True)
    team_name = models.CharField(max_length=100,  blank=True, null=True)
    arena_name = models.CharField(max_length=100,  blank=True, null=True)
    arena_location = models.CharField(max_length=100,  blank=True, null=True)
    city = models.CharField(max_length=100,  blank=True, null=True)
    seating_capacity = models.IntegerField(blank=True, null=True)
    opening_year = models.IntegerField(blank=True, null=True)
    lat = models.FloatField()
    lon = models.FloatField()
    address = models.CharField(max_length=100,  blank=True, null=True)
    first_year_of_this_combination = models.IntegerField(blank=True, null=True)
    last_year_of_this_combination = models.IntegerField(blank=True, null=True)
    def __str__(self):
        return self.team_abbreviation
    def get_absolute_url(self):
        return reverse("tesis:equipo_detail", kwargs={"pk": self.pk})
    def test_communication_equipo(self):
        result = ModuloPlanificador.iniciar_planificacion(self)
        return "The result of the communication test is: " + str(result) + " and the timestamp is: " + str(datetime.datetime.now())
    def __repr__(self):
        return f"'{self.team_abbreviation}'"
    @classmethod
    def from_string(cls, equipo_string):
        # Assume the string is the abbreviation of the team 'WAS'
        equipo = cls.objects.get(team_abbreviation=equipo_string)
        if equipo:
            return equipo
        else:
            raise ValueError(f"Invalid string format: {equipo_string}")

        
class Liga(models.Model):
    """ Liga Model:
    This model represents the Liga class.
    args:
        liga: CharField for the league's name.
        equipos: ManyToManyField for the league's teams.
    """
    nombre = models.CharField(max_length=100)
    equipos = models.ManyToManyField(Equipo, related_name='ligas')
    def __str__(self):
        return self.nombre
    def get_absolute_url(self):
        return reverse("tesis:liga_detail", kwargs={"pk": self.pk})
    def test_communication_liga(self):
        return "test_communication_liga called"

class Calendario(models.Model):
    """ Calendario Model:
    This model represents the Calendario class.
    args
        id_calendario: CharField for the calendar's id.
        torneo: ForeignKey to the tournament.
        lista_de_juegos: ManyToManyField for the calendar's games.
    """
    torneo = models.ForeignKey('Torneo', on_delete=models.CASCADE)
    def __str__(self):
        return "Calendario " + str(self.id)
    def get_absolute_url(self):
        return reverse("tesis:calendario_detail", kwargs={"pk": self.pk})
    def get_torneo(self):
        return self.torneo
    def set_torneo(self, torneo):
        self.torneo = torneo
    def obtener_equipos_participantes(self):
        return self.torneo.obtener_equipos_del_torneo()
    def get_juegos(self):
        return Juego.objects.filter(serie__calendario__pk=self.pk)
    def test_communication_calendario(self):
        return "test_communication_calendario called"
    def __repr__(self):
        return f"Calendario('{self.id}')"
    def get_numero_de_juegos(self):
        resultado = self.torneo.get_numero_de_juegos()
        return resultado
    def get_numero_de_series(self):
        resultado = self.torneo.get_numero_de_series()
        return resultado
    
    def get_numero_de_juegos_torneo(self):
        resultado = self.torneo.get_numero_de_juegos_torneo()
        return resultado
    
    def obtener_expresion(self):
        planificador = ModuloPlanificador()
        planificador.establecer_equipos(self.obtener_equipos_participantes())
        lista_fechas = []
        fecha = self.torneo.fecha_inicio
        while fecha <= self.torneo.fecha_fin:
            lista_fechas.append(fecha.isoformat())
            fecha = fecha + datetime.timedelta(days=1)
        planificador.establecer_fechas(lista_fechas)
        
        planificador.establecer_numero_de_juegos_por_equipo(self.get_numero_de_juegos())
        planificador.establecer_numero_de_juegos_por_equipo(self.get_numero_de_series())
        # Fetch the QuerySet
        queryset = Equipo.objects.filter(ligas__torneo__pk=self.torneo.pk).values_list('team_abbreviation', 'lat', 'lon')

        # Check if the QuerySet is not empty
        if queryset:
            # Create the DataFrame
            coordenadas_equipos = pd.DataFrame(list(queryset), columns=['equipo', 'lat', 'lon'])
        else:
            print("The QuerySet is empty. Please check your filter criteria.")
        #coordenadas_equipos = pd.DataFrame(Equipo.objects.filter(ligas__torneo__pk=self.torneo.pk).values_list('team_abbreviation', 'lat', 'lon'), columns=['equipo', 'lat', 'lon'])
        planificador.establecer_coordenadas_equipos(coordenadas_equipos)
        result = planificador.inicializar_planificador()
        return result
    def calcular_distancia(self, expresion):
        planificador = ModuloPlanificador()
        planificador.establecer_equipos(self.obtener_equipos_participantes())
        lista_fechas = []
        fecha = self.torneo.fecha_inicio
        while fecha <= self.torneo.fecha_fin:
            lista_fechas.append(fecha.isoformat())
            fecha = fecha + datetime.timedelta(days=1)
        planificador.establecer_fechas(lista_fechas)
        planificador.establecer_numero_de_juegos_por_equipo(self.get_numero_de_juegos())
        planificador.setNumeroDeSeriesPorEquipo(self.get_numero_de_series())
        # Fetch the QuerySet
        queryset = Equipo.objects.filter(ligas__torneo__pk=self.torneo.pk).values_list('team_abbreviation', 'lat', 'lon')

        # Check if the QuerySet is not empty
        if queryset:
            # Create the DataFrame
            coordenadas_equipos = pd.DataFrame(list(queryset), columns=['equipo', 'lat', 'lon'])
        else:
            print("The QuerySet is empty. Please check your filter criteria.")
        #coordenadas_equipos = pd.DataFrame(Equipo.objects.filter(ligas__torneo__pk=self.torneo.pk).values_list('team_abbreviation', 'lat', 'lon'), columns=['equipo', 'lat', 'lon'])
        planificador.establecer_coordenadas_equipos(coordenadas_equipos)
        result = planificador.calcular_distancia(expresion)
        #result = planificador.calcular_distancia(expresion)
        return result
    def ejecutar_programa_genetico(self):
        planificador = ModuloPlanificador()
        planificador.establecer_equipos(self.obtener_equipos_participantes())
        lista_fechas = []
        fecha = self.torneo.fecha_inicio
        while fecha <= self.torneo.fecha_fin:
            lista_fechas.append(fecha.isoformat())
            fecha = fecha + datetime.timedelta(days=1)
        planificador.establecer_fechas(lista_fechas)
        planificador.setNumeroDeJuegosPorEquipoTorneo(self.get_numero_de_juegos_torneo())
        planificador.establecer_numero_de_juegos_por_equipo(self.get_numero_de_juegos())
        planificador.setNumeroDeSeriesPorEquipo(self.get_numero_de_series())
        
        # Fetch the QuerySet
        queryset = Equipo.objects.filter(ligas__torneo__pk=self.torneo.pk).values_list('team_abbreviation', 'lat', 'lon')

        # Check if the QuerySet is not empty
        if queryset:
            # Create the DataFrame
            coordenadas_equipos = pd.DataFrame(list(queryset), columns=['equipo', 'lat', 'lon'])
        else:
            print("The QuerySet is empty. Please check your filter criteria.")
        #coordenadas_equipos = pd.DataFrame(Equipo.objects.filter(ligas__torneo__pk=self.torneo.pk).values_list('team_abbreviation', 'lat', 'lon'), columns=['equipo', 'lat', 'lon'])
        planificador.establecer_coordenadas_equipos(coordenadas_equipos)
        result = planificador.ejecutar_programa_genetico()
        resulta = result[0]
        resultb = result[1]
        
        return [resulta, resultb]
        #return result
    def ejecutar_programa_genetico_alt(self):
        planificador = ModuloPlanificador()
        planificador.establecer_equipos(self.obtener_equipos_participantes())
        lista_fechas = []
        fecha = self.torneo.fecha_inicio
        while fecha <= self.torneo.fecha_fin:
            lista_fechas.append(fecha.isoformat())
            fecha = fecha + datetime.timedelta(days=1)
        planificador.establecer_fechas(lista_fechas)
        planificador.establecer_numero_de_juegos_por_equipo(self.get_numero_de_juegos())
        planificador.setNumeroDeSeriesPorEquipo(self.get_numero_de_series())
        # Fetch the QuerySet
        queryset = Equipo.objects.filter(ligas__torneo__pk=self.torneo.pk).values_list('team_abbreviation', 'lat', 'lon')

        # Check if the QuerySet is not empty
        if queryset:
            # Create the DataFrame
            coordenadas_equipos = pd.DataFrame(list(queryset), columns=['equipo', 'lat', 'lon'])
        else:
            print("The QuerySet is empty. Please check your filter criteria.")
        #coordenadas_equipos = pd.DataFrame(Equipo.objects.filter(ligas__torneo__pk=self.torneo.pk).values_list('team_abbreviation', 'lat', 'lon'), columns=['equipo', 'lat', 'lon'])
        planificador.establecer_coordenadas_equipos(coordenadas_equipos)
        result = planificador.ejecutar_programa_genetico_alt()
        return result

            
            
class Juego(models.Model):
    """ Juego Model:
    This model represents the Juego class.
    args
        torneo: ForeignKey to the tournament.
        calendario: ForeignKey to the calendar.
        fecha: DateField for the game's date.
        equipo_en_casa: ForeignKey to the home team.
        equipo_visita: ForeignKey to the visiting team.
    """
    serie = models.ForeignKey('Serie', on_delete=models.CASCADE, related_name='juegos', default=-1)
    fecha_de_inicio = models.DateTimeField() # fecha_de_inicio DateField for the game's start date. Example: 2021-01-01 at 9 am would be "2021-01-01"
    fecha_de_fin = models.DateTimeField() # fecha_de_fin DateTimeField for the game's end date. Example: 2021-01-01 at 9 am would be "2021-01-01 09:00:00"
    equipo_en_casa = models.ForeignKey('Equipo', on_delete=models.CASCADE, related_name='equipo_en_casa')
    equipo_visita = models.ForeignKey('Equipo', on_delete=models.CASCADE, related_name='equipo_de_visita')
    def get_absolute_url(self):
        return reverse("tesis:juego_detail", kwargs={"pk": self.pk})
    def test_communication_juego(self):
        return "test_communication_juego called"
    def __str__(self) -> str:
        respuesta = ""
        if self.equipo_en_casa.team_name == None:
            equipo_en_casa = "EQA" 
        else: 
            equipo_en_casa = self.equipo_en_casa.team_abbreviation
        if self.equipo_visita.team_name == None:
            equipo_visita = "EQB"
        else:
            equipo_visita = self.equipo_visita.team_abbreviation
        if self.fecha_de_inicio == None:
            fecha_de_inicio = "fecha de inicio vacía"
        else:
            fecha_de_inicio = self.fecha_de_inicio.strftime('%Y-%m-%d')
        respuesta = f"Juego('{fecha_de_inicio}', '{equipo_en_casa}', '{equipo_visita}')"
        return respuesta
    def __repr__(self):
        respuesta = ""
        if self.equipo_en_casa.team_name == None:
            equipo_en_casa = "EQA" 
        else: 
            equipo_en_casa = self.equipo_en_casa.team_abbreviation
        if self.equipo_visita.team_name == None:
            equipo_visita = "EQB"
        else:
            equipo_visita = self.equipo_visita.team_abbreviation
        if self.fecha_de_inicio == None:
            fecha_de_inicio = "fecha de inicio vacía"
        else:
            fecha_de_inicio = self.fecha_de_inicio.strftime('%Y-%m-%d')
        respuesta = f"Juego('{fecha_de_inicio}', '{equipo_en_casa}', '{equipo_visita}')"
        return respuesta
    @classmethod
    def from_string(cls, juego_string):
        # Assume the string is in the format "Juego('{fecha_de_inicio}', '{fecha_de_fin}', '{equipo_en_casa}', '{equipo_visita}')"
        match = re.match(r"Juego\('(.+)', '(.+)', '(.+)', '(.+)'\)", juego_string)
        if match:
            juego, created = cls.objects.get_or_create(fecha_de_inicio=match.group(1), fecha_de_fin=match.group(2), equipo_en_casa=match.group(3), equipo_visita=match.group(4))
            return juego
        else:
            raise ValueError(f"Invalid string format: {juego_string}")
        
class Serie(models.Model):
    """
    Serie Model:
    This model represents the Serie class.
    args
        numero_de_serie: IntegerField for the series number.
        torneo: ForeignKey to the tournament.
    """
    calendario = models.ForeignKey('Calendario', on_delete=models.CASCADE, related_name='series', default=-1)
    numero_de_serie = models.IntegerField()
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['calendario', 'numero_de_serie'], name='unique_serie_per_calendario')
        ]
    # Add many juegos to each serie
    def __repr__(self):
        respuesta = f"Serie({self.numero_de_serie})"
        return respuesta
    def __str__(self):
        respuesta = f"{self.__repr__()} del Torneo {self.calendario.torneo.nombre} "
        return respuesta
    def get_absolute_url(self):
        return reverse("tesis:serie_detail", kwargs={"pk": self.pk})
    def get_juegos(self):
        juegos = Juego.objects.filter(serie__pk=self.pk)
        return juegos
    def test_communication_serie(self):
        return "test_communication_serie called"

class Torneo(models.Model):
    """ Torneo Model:
    This model represents the Torneo class.
    args
        nombre: CharField for the tournament's name.
        liga: ForeignKey to the league.
        fecha_inicio: DateField for the tournament's start date.
        dias_seleccionados: CharField for the tournament's game days.
        numero_de_juegos: IntegerField for the number of games.
        metodo: CharField for the method used to calculate the distance, haversine by default or euclidean.
        unidad: CharField for the unit of distance, km by default.
        calendario: ForeignKey to the calendar.
    """
    calendario_principal = models.OneToOneField('Calendario', on_delete=models.SET_NULL, null=True, blank=True, default=None, related_name='torneo_principal')
    nombre = models.CharField(max_length=100)
    liga = models.ManyToManyField(Liga)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    dias_seleccionados = models.CharField(max_length=100, blank=True, null=True, default="Lunes, Martes, Miercoles, Jueves, Viernes, Sabado, Domingo")
    numero_de_juegos = models.IntegerField()
    numero_de_series = models.IntegerField()
    metodo = models.CharField(max_length=100)
    unidad = models.CharField(max_length=100)
    def __str__(self):
        return self.nombre
    def get_absolute_url(self):
        return reverse("tesis:torneo_detail", kwargs={"pk": self.pk})
    def establecer_equipos_en_planificador(self, equipos):
        planificador = ModuloPlanificador()
        planificador.establecer_equipos(equipos)
        return planificador.getEquipos()
    def obtener_equipos_del_torneo(self):
        equipos = Equipo.objects.filter(ligas__torneo__pk=self.pk)
        return equipos
    def obtener_fechas_del_torneo(self):
        lista_fechas = []
        fecha = self.fecha_inicio
        while fecha <= self.fecha_fin:
            lista_fechas.append(fecha.isoformat())
            fecha = fecha + datetime.timedelta(days=1)
        return lista_fechas
    def obtener_equipos_con_coordenadas(self):
        equipos = Equipo.objects.filter(ligas__torneos__pk=self.pk).values_list('team_abbreviation', 'lat', 'lon')
        return equipos
    def get_numero_de_series(self):
        return self.numero_de_series
    def set_numero_de_series(self, numero_de_series):
        self.numero_de_series = numero_de_series
    def set_numero_de_juegos(self, numero_de_juegos):
        self.numero_de_juegos = numero_de_juegos
    def get_numero_de_juegos(self):
        return self.numero_de_juegos
    def get_numero_de_juegos_torneo(self):    
        return self.numero_de_juegos * self.numero_de_series
    
    def obtener_expresion(self):
        planificador = ModuloPlanificador()
        planificador.establecer_equipos(Equipo.objects.filter(ligas__torneos__pk=self.pk).values_list('team_abbreviation', flat=True))
        #planificador.setFechas(self.mandar_fechas_al_programa_genetico())
        lista_fechas = []
        fecha = self.fecha_inicio
        while fecha <= self.fecha_fin:
            lista_fechas.append(fecha.isoformat())
            fecha = fecha + datetime.timedelta(days=1)
        planificador.establecer_fechas(lista_fechas)
        planificador.establecer_numero_de_juegos_por_equipo(self.get_numero_de_juegos())
        planificador.setNumeroDeSeriesPorEquipo(self.get_numero_de_series())
        #result = planificador.getFechasDeProgramaGenetico()        
        coordenadas_equipos = pd.DataFrame(Equipo.objects.filter(ligas__torneos__pk=self.pk).values_list('team_abbreviation', 'lat', 'lon'), columns=['equipo', 'lat', 'lon'])  
        #print(coordenadas_equipos)
        planificador.establecer_coordenadas_equipos(coordenadas_equipos)
        planificador.iniciar_planificacion()
        
        
        result = planificador.obtener_expresion()
        return result
    def ver_evaluacion(self):
        planificador = ModuloPlanificador()
        result = planificador.evaluacion()
        return result

class Configuracion(models.Model):
    """ Configuracion Model:
    This model represents the Configuracion class.
    args
        torneo: ForeignKey to the tournament.
        poblacion: IntegerField for the population size.
        generaciones: IntegerField for the number of generations.
        probabilidad_de_cruce: FloatField for the crossover probability.
        probabilidad_de_reproduccion: FloatField for the reproduction probability.
    """
    calendario = models.OneToOneField('Calendario', on_delete=models.CASCADE, default=None, blank=True, null=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    poblacion = models.IntegerField()
    generaciones = models.IntegerField()
    probabilidad_de_cruce = models.FloatField()
    probabilidad_de_reproduccion = models.FloatField()
    def __str__(self):
        #return "CONF" + str(self.id) + " " + str(self.poblacion) + "" + str(self.generaciones) + "" + str(self.probabilidad_de_cruce) + "" + str(self.probabilidad_de_reproduccion) + " Calendario: " + str(self.calendario.id)
        return "CONF" + str(self.id) + "CA" + str(self.calendario.id) + "P" + str(self.poblacion) + "G" + str(self.generaciones) + "X" + str(self.probabilidad_de_cruce) + "R" + str(self.probabilidad_de_reproduccion)
    def get_absolute_url(self):
        return reverse("tesis:configuracion_detail", kwargs={"pk": self.pk})
    def test_communication_configuracion(self):
        return "test_communication_configuracion called"
    def generar_calendario_aleatorio(self):
        if self.calendario == None:
            calendario = Calendario.objects.create(torneo=self.torneo)
            self.calendario = calendario
        # Recover teams and dates
        print("Getting teams and dates")
        print(f'Generating random schedule for {self.calendario} cAlendario')
        torneo = Torneo.objects.get(pk=self.calendario.torneo.id)
        print(f'Getting teams for {torneo.nombre} tournament')
        print(f'and this {self.calendario.torneo} tournament')
        
        equipos = torneo.obtener_equipos_del_torneo()
        fechas = torneo.obtener_fechas_del_torneo()

        # Initialize planificador
        planificador = ModuloPlanificador()
        planificador.establecer_equipos(equipos)
        planificador.establecer_fechas(fechas)
        planificador.establecer_numero_de_juegos_por_equipo(self.calendario.torneo.get_numero_de_juegos())
        planificador.setNumeroDeSeriesPorEquipo(self.calendario.torneo.get_numero_de_series())  
        planificador.iniciar_planificacion()

        # Get initial schedule and series list
        juegos = planificador.obtener_calendario_inicial()
        
        # Create games and series in the database
        for juego in juegos:
            print(f"Creating game {juego['numero_de_serie']} between {juego['equipo1']} and {juego['equipo2']} on {juego['fecha_de_inicio']}")
            serie = Serie.objects.get_or_create(calendario=self.calendario, numero_de_serie=juego['numero_de_serie'])
            serie = serie[0] # first argument from a (serie, boolean) tuple
            serie.save()
            equipo_en_casa = Equipo.objects.get(team_abbreviation=juego['equipo1'].team_abbreviation)
            equipo_visita = Equipo.objects.get(team_abbreviation=juego['equipo2'].team_abbreviation)
            juego = Juego.objects.get_or_create(serie=serie, fecha_de_inicio=juego['fecha_de_inicio'], fecha_de_fin=juego['fecha_de_fin'], equipo_en_casa=equipo_en_casa, equipo_visita=equipo_visita)
            juego = juego[0]
            juego.save()        
    def duplicar_calendario_configuracion_y_generar_nuevo_calendario(self):
        # Create a new configuration with the same parameters
        nueva_configuracion = Configuracion.objects.create(poblacion=self.poblacion, generaciones=self.generaciones, probabilidad_de_cruce=self.probabilidad_de_cruce, probabilidad_de_reproduccion=self.probabilidad_de_reproduccion)
        # Create a new calendar with the same tournament
        nuevo_calendario = Calendario.objects.create(torneo=self.calendario.torneo)
        # Assign the new calendar to the new configuration
        nueva_configuracion.calendario = nuevo_calendario
        # Save the new configuration
        nueva_configuracion.save()
        # Generate a new random schedule for the new calendar
        nueva_configuracion.generar_calendario_aleatorio()
        # Return the new configuration
        return nueva_configuracion, nuevo_calendario              
class Condicion(models.Model):
    calendario = models.ForeignKey('Calendario', on_delete=models.CASCADE, related_name='condiciones', default=-1)
    texto_condicion = models.CharField(max_length=100, blank=True, null=True, default=None)
    def __str__(self):
        return "condicion: " + str(self.id)
    def get_absolute_url(self):
        return reverse("tesis:condicion_detail", kwargs={"pk": self.pk})
    def test_communication_condicion(self):
        return "test_communication_condicion called"