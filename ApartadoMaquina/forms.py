from django import forms
from General.models import Maquinaria
from datetime import datetime

class MaquinariaForm(forms.ModelForm):
    class Meta:
        model = Maquinaria
        exclude = ['estado','fecha_habilitacion']
        widgets = {
            'codigo_serie': forms.TextInput(attrs={'minlength': 1}),
        }

    def clean_año_compra(self):
        año = self.cleaned_data.get('año_compra')
        año_actual = datetime.now().year
        if año < 1950 or año > año_actual:
            raise forms.ValidationError(f"El año de compra debe estar entre 1950 y {año_actual}.")
        return año
    
    def clean_codigo_serie(self):
        codigo = self.cleaned_data.get('codigo_serie')
        if not codigo.isalnum():
            raise forms.ValidationError("El código de serie debe contener sólo letras y/o números.")
        return codigo
    
    def clean_imagen(self):
        imagen = self.cleaned_data.get('imagen')
        if not imagen:
            raise forms.ValidationError("La imagen es obligatoria.")
        return imagen
    
    def clean_precio_alquiler_diario(self):
        precio = self.cleaned_data.get('precio_alquiler_diario')
        if precio is None or precio <= 0:
            raise forms.ValidationError("El precio de alquiler diario debe ser un número positivo.")
        return precio