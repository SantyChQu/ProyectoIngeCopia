from django import forms
from .models import Maquina
from datetime import datetime

class MaquinaForm(forms.ModelForm):
    class Meta:
        model = Maquina
        fields = '__all__'
        widgets = {
            'numero_de_serie': forms.NumberInput(attrs={'min': 0}),
        }

    def clean_año_compra(self):
        año = self.cleaned_data.get('año_compra')
        año_actual = datetime.now().year
        if año < 1950 or año > año_actual:
            raise forms.ValidationError(f"El año de compra debe estar entre 1930 y {año_actual}.")
        return año
    
    def clean_numero_de_serie(self):
        numero = self.cleaned_data.get('numero_de_serie')
        if not numero.isdigit():
            raise forms.ValidationError("El número de serie debe contener sólo números.")
        return numero