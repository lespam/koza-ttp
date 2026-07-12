from django import forms
from .models import Calendario, Equipo, Liga, Torneo, Configuracion, Juego, Serie



class LigaForm(forms.Form):
        nombre = forms.CharField(max_length=100)
        equipos = forms.ModelMultipleChoiceField(queryset=Equipo.objects.all(), widget=forms.CheckboxSelectMultiple)
        def send_data(self):
            # send
            pass

class ConfiguracionForm(forms.ModelForm):
    # get torneo from the view to preselect or leave it blank
    #calendario = forms.ModelChoiceField(queryset=Calendario.objects.all(), widget=forms.Select)
    class Meta:
        model = Configuracion
        fields = "__all__"

class CalendarioForm(forms.ModelForm):
    # get torneo from the view to preselect or leave it blank
    #torneo = forms.ModelChoiceField(queryset=Torneo.objects.all(), widget=forms.Select)
    class Meta:
        model = Calendario
        fields = "__all__"

class JuegoForm(forms.ModelForm):
    class Meta:
        model = Juego
        fields = "__all__"

class SerieForm(forms.ModelForm):
    class Meta:
        model = Serie
        fields = "__all__"

class ProgramaFacadeForm(forms.Form):
        # Le pedimos al usuario que ingrese los datos.
        metodo = forms.CharField(max_length=100)
        unidad = forms.CharField(max_length=100)
        probabilidad_cruce = forms.FloatField()
        probabilidad_reproduccion = forms.FloatField()
        num_generaciones = forms.IntegerField()
        num_juegos = forms.IntegerField()
        equipos = forms.ModelMultipleChoiceField(queryset=Equipo.objects.all(), widget=forms.SelectMultiple)
        calendario_inicial = forms.BooleanField()
        fecha_inicio = forms.DateField()
        condiciones = forms.CharField()
        
        def iniciaPrograma(self):
            # send
            pass