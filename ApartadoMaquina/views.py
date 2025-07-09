from django.shortcuts import render, redirect
from .forms import MaquinariaForm
from django.db import IntegrityError
from django.contrib import messages
from General.models import Maquinaria, Localidad, Alquiler, Politica, Observacion, Cliente
from datetime import datetime
from PIL import Image

def agregar_maquina(request):
    mensaje = ''
    maquinaria_agregada = None

    if request.method == 'POST':
        form = MaquinariaForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                maquinaria_agregada = form.save(commit=False)  
                maquinaria_agregada.estado = 'habilitado'      
                maquinaria_agregada.save()
                mensaje = '¡Maquinaria agregada correctamente!'
                form = MaquinariaForm()  
            except IntegrityError:
                form.add_error('numero_de_serie', 'Ya existe una máquina con ese número de serie.')
    else:
        form = MaquinariaForm()
        
    return render(request, 'ApartadoMaquina/formulario.html', {
        'form': form,
        'mensaje': mensaje,
        'maquinaria_agregada': maquinaria_agregada
    })
from django.utils import timezone

def agregar_observacion_maquinaria(request, id):
    maquinaria = get_object_or_404(Maquinaria, id=id)
    cliente = get_object_or_404(Cliente, id=request.session.get("cliente_id"))
    if request.method == 'POST':
        descripcion = request.POST.get('descripcion')
        if descripcion:
            obs = Observacion(
                observacion=descripcion,
                mail=cliente.mail,
                codigo_maquina=maquinaria,
                fecha=timezone.now().date()
            )
            obs.save()
            messages.success(request, f"Observación agregada a {maquinaria.codigo_serie}.")
    return redirect('ver_maquinarias')

from django.db.models import Q

def ver_maquinarias(request):
    buscar = request.GET.get('buscar', '').lower()

    maquinarias = Maquinaria.objects.exclude(estado='eliminado')

    if buscar:
        maquinarias = maquinarias.filter(
            Q(codigo_serie__icontains=buscar) |
            Q(estado__icontains=buscar)
        )

    for maquina in maquinarias:
        maquina.verificar_estado()

    localidades = Localidad.objects.all()
    politicas = Politica.objects.all()

    soyEmpleado = request.session.get('cliente_rol') == "empleados"

    return render(request, 'ApartadoMaquina/listadoMaquinas.html', {
        'maquinarias': maquinarias,
        'localidades': localidades,
        'politicas': politicas,
        'empleado': soyEmpleado
    })

##
from django.shortcuts import get_object_or_404

from django.utils import timezone
from datetime import timedelta

def cambiar_estado_maquinaria(request, id):

    if request.method == 'POST':
        maquina = get_object_or_404(Maquinaria, id=id)
        empleado_mail = get_object_or_404(Cliente, id=request.session.get("cliente_id"))
        if maquina.estado == 'habilitado':
            opcion = request.POST.get('opcion')
            if opcion == '1':
                maquina.estado = 'inhabilitado'
                maquina.fecha_habilitacion = timezone.now() + timedelta(days=1)
                
            elif opcion == 'varios':
                dias = int(request.POST.get('dias_extra', 1))
                maquina.estado = 'inhabilitado'
                maquina.fecha_habilitacion = timezone.now() + timedelta(days=dias)
                messages.error(request, f"La maquinaria '{maquina.codigo_serie}' fue Inhabilitada correctamente.")

                
        else:
            maquina.estado = 'habilitado'
            maquina.fecha_habilitacion = None
            messages.success(request, f"La maquinaria '{maquina.codigo_serie}' fue habilitada correctamente.")

        maquina.save()
        return redirect('ver_maquinarias')


   
def eliminar_maquinaria(request, maquinaria_id):
    maquinaria = get_object_or_404(Maquinaria, id=maquinaria_id)

    if maquinaria.estado == 'eliminado':
        messages.warning(request, 'La maquinaria ya está marcada como eliminada.')
    else:
        maquinaria.estado = 'eliminado'
        maquinaria.save()
        messages.success(request, 'Eliminacion Exitosa')

    return redirect('ver_maquinarias')



def modificar_maquina(request, id):
    maquina = get_object_or_404(Maquinaria, id=id)
    
    if request.method == "POST":
        maquina.marca = request.POST.get('marca')
        maquina.modelo = request.POST.get('modelo')
        maquina.año_compra = request.POST.get('año_compra')
        maquina.precio_alquiler_diario = request.POST.get('precio_alquiler_diario')
        
        politica_id = request.POST.get('politica')
        localidad_id = request.POST.get('localidad')

        # ✅ Asignar política correctamente
        if politica_id:
            try:
                maquina.politica = Politica.objects.get(id=politica_id)
            except Politica.DoesNotExist:
                messages.error(request, "La política seleccionada no existe.")
                return redirect('ver_maquinarias')

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

        # Validar precio
        try:
            precio = float(request.POST.get('precio_alquiler_diario'))
            if precio < 0:
                messages.error(request, "El precio no puede ser negativo.")
                return redirect('ver_maquinarias')
            maquina.precio_alquiler_diario = precio
        except (TypeError, ValueError):
            messages.error(request, "Precio inválido.")
            return redirect('ver_maquinarias')

        # Asignar localidad si se seleccionó
        if localidad_id:
            try:
                maquina.localidad = Localidad.objects.get(id=localidad_id)
            except Localidad.DoesNotExist:
                messages.error(request, "La localidad seleccionada no existe.")
                return redirect('ver_maquinarias')

        # Guardar imagen si se subió una nueva
        if request.method == 'POST':
         if 'imagen' in request.FILES:
            imagen = request.FILES['imagen']

            # Verifica el tipo MIME
            if not imagen.content_type.startswith('image/'):
                messages.error(request, "El archivo debe ser una imagen (JPEG, PNG, GIF, etc)")
                return redirect('ver_maquinarias')

            # Verifica internamente con imghdr (más seguro contra archivos falsos) NO LO PUEDO USAR
            #if imghdr.what(imagen) not in ['jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']:
            try:
              with Image.open(imagen) as img:
                 tipo = img.format.lower()  # devuelve 'jpeg', 'png', etc.
            except:
                 messages.error(request, "No se pudo verificar la imagen. El archivo puede estar corrupto.")
                 return redirect('ver_maquinarias')
            if tipo not in ['jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']:   
                 messages.error(request, "Formato de imagen no válido")
                 return redirect('ver_maquinarias')

            maquina.imagen = imagen

        maquina.save()
        messages.success(request, "Máquina modificada correctamente")
        return redirect('ver_maquinarias')

    localidades = Localidad.objects.all()
    politicas = Politica.objects.all()
    
    return render(request, 'ApartadoMaquina/modificar_maquina.html', {
        'maquina': maquina,
        'localidades': localidades,
        'politicas': politicas,
    })
   
   
   
   # maquinaria = get_object_or_404(Maquinaria, id=id)
   #maquinaria.estado = 'inhabilitado' if maquinaria.estado == 'habilitado' else 'habilitado'
    #maquinaria.save()
    #return redirect('ver_maquinarias')

from django.db.models import Count

def alquileres_por_maquina(request):
    # Traer todas las máquinas que NO están eliminadas
    maquinas = Maquinaria.objects.exclude(estado='eliminado').annotate(
        cantidad_alquileres=Count('alquiler')  
    ).order_by('-cantidad_alquileres')

    # Chart.js
    labels = [f"{m.marca} {m.modelo}" for m in maquinas]
    data = [m.cantidad_alquileres for m in maquinas]

    return render(request, 'alquileresPorMaquinaria.html', {
        'labels': labels,
        'data': data,
        'maquinas': maquinas,
    })

def eliminarObservacion(request,id):


    observacion = get_object_or_404(Observacion,id=id)

    observacion.delete()
    messages.success(request,"observacion eliminada correctamente")
    return redirect('ver_maquinarias')