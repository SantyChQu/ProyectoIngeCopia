from django.shortcuts import render, redirect
from .forms import MaquinariaForm
from django.db import IntegrityError
from django.contrib import messages
from General.models import Maquinaria, Localidad, Alquiler
from datetime import datetime
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
    localidades = Localidad.objects.all()
    return render(request, 'ApartadoMaquina/listadoMaquinas.html', {
        'maquinarias': maquinarias,
        'localidades': localidades
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

def modificar_maquina(request, id):
    maquina = get_object_or_404(Maquinaria, id=id)
    if request.method == "POST":
        maquina.marca = request.POST.get('marca')
        maquina.modelo = request.POST.get('modelo')
        maquina.año_compra = request.POST.get('año_compra')
        maquina.precio_alquiler_diario = request.POST.get('precio_alquiler_diario')
        
        # Obtener el objeto Localidad según el id enviado en el formulario
        localidad_id = request.POST.get('localidad')



        # Validar año de compra
        try:
            año_actual = datetime.now().year
            año = int(maquina.año_compra)
            if año < 1950 or año > año_actual:
                messages.error(request, f"El año de compra debe estar entre 1950 y {año_actual}.")
                return redirect('ver_maquinarias')
            maquina.año_compra = año
        except (TypeError, ValueError):
            messages.error(request, "Año de compra inválido.")
            return redirect('ver_maquinarias')

        try:
            precio = float(request.POST.get('precio_alquiler_diario'))
            if precio < 0:
                messages.error(request, "El precio no puede ser negativo.")
                return redirect('ver_maquinarias')
            maquina.precio_alquiler_diario = precio
        except (TypeError, ValueError):
            messages.error(request, "Precio inválido.")
            return redirect('ver_maquinarias')

        localidad_id = request.POST.get('localidad')

        if localidad_id:
            maquina.localidad = Localidad.objects.get(id=localidad_id)
        
        if 'imagen' in request.FILES:
            maquina.imagen = request.FILES['imagen']
        
        maquina.save()
        messages.success(request, "Maquina modificada correctamente")
        return redirect('ver_maquinarias')

    localidades = Localidad.objects.all()
    return render(request, 'ApartadoMaquina/modificar_maquina.html', {
        'maquina': maquina,
        'localidades': localidades,
    })
   
   
   
   # maquinaria = get_object_or_404(Maquinaria, id=id)
   #maquinaria.estado = 'inhabilitado' if maquinaria.estado == 'habilitado' else 'habilitado'
    #maquinaria.save()
    #return redirect('ver_maquinarias')


