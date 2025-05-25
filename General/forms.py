# yo cree este archivo 
from django import forms
from django.core.exceptions import ValidationError
from .models import Cliente
from django.core.validators import RegexValidator
solo_letras = RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 
                             'Solo se permiten letras y espacios.',
                             code='invalid')
class ClienteForm(forms.ModelForm):
    nombre= forms.CharField(required=True,validators=[solo_letras],
        error_messages={'invalid': 'Solo se permiten letras.'}
    )
    apellido= forms.CharField(required=True,validators=[solo_letras],
        error_messages={'invalid': 'Solo se permiten letras.'})
    edad= forms.IntegerField(required=True, min_value=18)
    telefono= forms.IntegerField(required=True)
    
    
    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'edad', 'telefono', 'mail']
        exclude = ['contraseña']



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mail'].widget.attrs['readonly'] = True
        self.fields['mail'].widget.attrs['style'] = 'background-color: #e9ecef; cursor: not-allowed;'



    def clean_contraseña(self):
        contraseña = self.cleaned_data['contraseña']
        if len(contraseña) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
        return contraseña



    def clean(self):
        cleaned_data = super().clean()
        edad = cleaned_data.get('edad')
        if edad is not None and edad < 18:
            raise ValidationError("El cliente debe ser mayor de edad.")
        return cleaned_data
    
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