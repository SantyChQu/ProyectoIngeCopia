from django import forms
from .models import Cliente
from django.core.validators import RegexValidator

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