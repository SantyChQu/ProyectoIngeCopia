from django.shortcuts import render, redirect
from .forms import MaquinaForm
from .models import Maquina
from django.db import IntegrityError


def agregar_maquina(request):
    mensaje = ''
    maquina_agregada = None

    if request.method == 'POST':
        form = MaquinaForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                maquina_agregada = form.save()
                mensaje = '¡Maquinaria agregada correctamente!'
                form = MaquinaForm()  # reiniciar el form vacío
            except IntegrityError:
                form.add_error('numero_de_serie', 'Ya existe una máquina con ese número de serie.')
    else:
        form = MaquinaForm()
        
    return render(request, 'ApartadoMaquina/formulario.html', {
        'form': form,
        'mensaje': mensaje,
        'maquina_agregada': maquina_agregada
    })