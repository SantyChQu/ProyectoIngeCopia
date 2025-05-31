# yo cree este archivo 
from django import forms
from django.core.exceptions import ValidationError
from .models import Cliente
from django.core.validators import RegexValidator
from django.forms import DateInput
from datetime import date, timedelta

solo_letras = RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 
                             'Solo se permiten letras y espacios.',
                             code='invalid')
class ClienteForm(forms.ModelForm):
    nombre= forms.CharField(required=True,validators=[solo_letras],
        error_messages={'invalid': 'Solo se permiten letras.'}
    )
    apellido= forms.CharField(required=True,validators=[solo_letras],
        error_messages={'invalid': 'Solo se permiten letras.'})
    
    fecha_nacimiento = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'}),
        error_messages={'invalid': 'Ingrese una fecha válida.'}
    )
    telefono = forms.IntegerField(required=True)
    # edad= forms.IntegerField(required=True, min_value=18)
    
    edad_calculada = forms.IntegerField(
        required=False,
        label='Edad',
        widget=forms.NumberInput(attrs={'readonly': 'readonly'})
    )

    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'fecha_nacimiento', 'telefono', 'mail','contraseña']
       # exclude = ['contraseña']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.fecha_nacimiento:
            hoy = date.today()
            edad = hoy.year - self.instance.fecha_nacimiento.year - (
                (hoy.month, hoy.day) < (self.instance.fecha_nacimiento.month, self.instance.fecha_nacimiento.day)
            )
            self.fields['edad_calculada'].initial = edad

        if self.instance and self.instance.pk:
            self.fields['mail'].widget.attrs['readonly'] = True
            self.fields['mail'].widget.attrs['style'] = 'background-color: #e9ecef; cursor: not-allowed;'

    
    #    super().__init__(*args, **kwargs)
    #    if self.instance and self.instance.pk:
    #      self.fields['mail'].widget.attrs['readonly'] = True
    #      self.fields['mail'].widget.attrs['style'] = 'background-color: #e9ecef; cursor: not-allowed;'



    def clean_contraseña(self):
        contraseña = self.cleaned_data['contraseña']
        if len(contraseña) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
        return contraseña

# agregar verificacion por mail repetido- o mial que no contenga @ y .
    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data['fecha_nacimiento']
        hoy = date.today()
        edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
        if edad < 18:
            raise forms.ValidationError('El cliente debe tener al menos 18 años.')
        return fecha
    #def clean(self):
     #   cleaned_data = super().clean()
      #  edad = cleaned_data.get('edad')
       # if edad is not None and edad < 18:
        #    raise ValidationError("El cliente debe ser mayor de edad.")
        #return cleaned_data
    
class CambiarContraseñaForm(forms.Form):
    actual = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput,
        required=True
    )
    nueva = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput,
        required=True,
        min_length=8,
        error_messages={
            'min_length': 'La nueva contraseña debe tener al menos 8 caracteres.'
        }
    )
    nueva2 = forms.CharField(
        label="Repetir nueva contraseña",
        widget=forms.PasswordInput,
        required=True
    )

    def clean(self):
        cleaned_data = super().clean()
        nueva = cleaned_data.get("nueva")
        nueva2 = cleaned_data.get("nueva2")

        if nueva and nueva2 and nueva != nueva2:
            raise forms.ValidationError("Las nuevas contraseñas no coinciden.")
        return cleaned_data   

class tarjetaForm(forms.Form):

    numero = forms.CharField(label="Número de tarjeta")
    numeroseguridad = forms.CharField(label="Número de seguridad")
    monto = forms.DecimalField(label="Monto a pagar", decimal_places=2)


