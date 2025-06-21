from django import forms
from General.models import Cliente
from django.core.validators import RegexValidator
from datetime import date
solo_letras = RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 'Solo se permiten letras y espacios.')

class ClienteUpdateForms(forms.ModelForm):

    nombre= forms.CharField(required=True,validators=[solo_letras],
        error_messages={'invalid': 'Solo se permiten letras.'}
    )
    apellido= forms.CharField(required=True,validators=[solo_letras],
        error_messages={'invalid': 'Solo se permiten letras.'})
    edad= forms.IntegerField(required=True, min_value=18)
    telefono= forms.IntegerField(required=True)
    contraseña = forms.CharField(required=False,
        widget=forms.PasswordInput,
        min_length=8,  # Aquí definís el mínimo
        error_messages={
            'min_length': 'La contraseña debe tener al menos 8 caracteres.'
        }
    )
    
    class Meta: #class meta nos sirve para indicarle a la clase a que modelo
                 #esta relacionado para que pueda tomar los tipos de datos que estan definidos en el modelo
        model=Cliente
        fields= ["nombre","apellido","edad","telefono","dni","mail","contraseña"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mail'].widget.attrs['readonly'] = True 
        self.fields['nombre'].widget.attrs['placeholder'] = 'Ingrese su nombre'
        self.fields['apellido'].widget.attrs['placeholder'] = 'Ingrese su apellido'

class FiltroFechaForm(forms.Form):
    hoy = date.today()

    fecha_desde = forms.DateField(
        label='Desde',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'max': hoy.strftime('%Y-%m-%d')
        })
    )

    fecha_hasta = forms.DateField(
        label='Hasta',
        widget=forms.DateInput(attrs={
            'type': 'date',
            'max': hoy.strftime('%Y-%m-%d')
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        desde = cleaned_data.get("fecha_desde")
        hasta = cleaned_data.get("fecha_hasta")
        hoy = date.today()

        if hasta and hasta > hoy:
            self.add_error('fecha_hasta', 'La fecha de fin no puede ser mayor a hoy.')

        if desde and hasta and desde > hasta:
            self.add_error('fecha_desde', 'La fecha de inicio no puede ser posterior a la de fin.')