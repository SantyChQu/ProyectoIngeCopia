from django.shortcuts import render, redirect
from .forms import MaquinariaForm
from django.db import IntegrityError
from django.contrib import messages
from General.models import Maquinaria

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

def ver_maquinarias(request):
    maquinarias = Maquinaria.objects.all()
    return render(request, 'ApartadoMaquina/listadoMaquinas.html', {
        'maquinarias': maquinarias
    })


##
from django.shortcuts import get_object_or_404

def cambiar_estado_maquinaria(request, id):
   if request.method == 'POST':
        maquina = get_object_or_404(Maquinaria, id=id)
        if maquina.estado == 'habilitado':
            maquina.estado = 'inhabilitado'
            messages.success(request, f"La maquinaria '{maquina.marca} {maquina.modelo}' fue inhabilitada correctamente.")
        else:
            maquina.estado = 'habilitado'
            messages.success(request, f"La maquinaria '{maquina.marca} {maquina.modelo}' fue habilitada correctamente.")
        maquina.save()
        return redirect('ver_maquinarias')

   
   
   
   
   # maquinaria = get_object_or_404(Maquinaria, id=id)
   #maquinaria.estado = 'inhabilitado' if maquinaria.estado == 'habilitado' else 'habilitado'
    #maquinaria.save()
    #return redirect('ver_maquinarias')