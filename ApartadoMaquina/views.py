from django.shortcuts import render, redirect
from .forms import MaquinariaForm
from django.db import IntegrityError
from django.contrib import messages

def agregar_maquina(request):
    mensaje = ''
    maquinaria_agregada = None

    if request.method == 'POST':
        form = MaquinariaForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                maquinaria_agregada = form.save(commit=False)  # No guardamos todavía
                maquinaria_agregada.estado = 'habilitado'      # Asignamos estado
                maquinaria_agregada.save()
                mensaje = '¡Maquinaria agregada correctamente!'
                form = MaquinariaForm()  # reiniciar el form vacío
            except IntegrityError:
                form.add_error('numero_de_serie', 'Ya existe una máquina con ese número de serie.')
    else:
        form = MaquinariaForm()
        
    return render(request, 'ApartadoMaquina/formulario.html', {
        'form': form,
        'mensaje': mensaje,
        'maquinaria_agregada': maquinaria_agregada
    })


def ver_Maquinas(request):
    if not request.user.is_superuser and not request.user.is_staff:  
        messages.error(request, "No tenés permiso para acceder a esta página.")
        return redirect('inicio')  
    return render(request, 'listadoMaquinas.html')