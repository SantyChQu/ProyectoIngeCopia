# yo cree este archivo 
from django import forms
from django.core.exceptions import ValidationError
from .models import Cliente,Localidad
from django.core.validators import RegexValidator
from django.forms import DateInput
from datetime import date, timedelta

solo_letras = RegexValidator(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', 
                             'Solo se permiten letras y espacios.',
                             code='invalid')
class ClienteRegistroForm(forms.ModelForm):
    nombre = forms.CharField(required=True, validators=[solo_letras])
    apellido = forms.CharField(required=True, validators=[solo_letras])
    fecha_nacimiento = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'}),
        error_messages={'invalid': 'Ingrese una fecha válida.'}
    )
    telefono = forms.IntegerField(required=True)
    dni = forms.IntegerField(required=True, label="DNI")

    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'fecha_nacimiento', 'telefono','dni', 'mail', 'contraseña']

    def clean_contraseña(self):
        contraseña = self.cleaned_data['contraseña']
        if len(contraseña) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
        return contraseña
    


    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data['fecha_nacimiento']
        hoy = date.today()
        edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
        if edad < 18:
             raise forms.ValidationError('Se debe tener al menos 18 años.')
        if edad > 100:
            raise forms.ValidationError('La edad no puede ser mayor a 100 años.')

        return fecha
    
    def clean(self):
        cleaned_data = super().clean()
        dni = cleaned_data.get('dni')
        mail = cleaned_data.get('mail')

        if Cliente.objects.filter(dni=dni).exists():
            self.add_error('dni', 'Ya existe un usuario con este DNI.')

        if Cliente.objects.filter(mail=mail).exists():
            self.add_error('mail', 'Ya existe un usuario registrado con este mail.')
    
class ClienteEdicionForm(forms.ModelForm):
    nombre = forms.CharField(required=True, validators=[solo_letras])
    apellido = forms.CharField(required=True, validators=[solo_letras])
    fecha_nacimiento = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'}),
        error_messages={'invalid': 'Ingrese una fecha válida.'}
    )
    telefono = forms.IntegerField(required=True)
    dni = forms.CharField(required=True, label="DNI")

    class Meta:
        model = Cliente
        fields = ['nombre', 'apellido', 'fecha_nacimiento','dni', 'telefono', 'mail']

    def __init__(self, *args, **kwargs):
          super().__init__(*args, **kwargs)
          if self.instance and self.instance.pk:
            self.fields['mail'].disabled = True  
          if self.instance and self.instance.pk:
            self.fields['dni'].disabled = True   
          if self.instance and self.instance.fecha_nacimiento:
            self.initial['fecha_nacimiento'] = self.instance.fecha_nacimiento.strftime('%Y-%m-%d')  #esto hizo que se muestre la fecha

    def clean_fecha_nacimiento(self):
          fecha = self.cleaned_data['fecha_nacimiento']
          hoy = date.today()
          edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
          if edad < 18:
             raise forms.ValidationError('Se debe tener al menos 18 años.')
          return fecha  
    
    
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
    numero = forms.CharField(
        label="Número de tarjeta",
        max_length=16,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: 1234 5678 9012 3456', 'class': 'form-control'})
    )
    numeroseguridad  = forms.CharField(
        label="Número de seguridad",
        max_length=4,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: 123', 'class': 'form-control'})
    )
    nombre_propietario = forms.CharField(
        label="Nombre del titular",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Ej: Juan Pérez', 'class': 'form-control'})
    )
    fecha_desde = forms.DateField(
        label="Válida desde",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_hasta = forms.DateField(
        label="Válida hasta",
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )


    class LocalidadForm(forms.ModelForm):
        class Meta:
          model = Localidad
          fields = ['nombre', 'codigo_postal', 'ubicacion']
          widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_postal': forms.TextInput(attrs={'class': 'form-control'}),
            'ubicacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }