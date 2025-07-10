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

from django.db.models import Case, When, Value, IntegerField

def ver_maquinarias(request):
    buscar = request.GET.get('buscar', '').lower()

    maquinarias = Maquinaria.objects.exclude(estado='eliminado')

    if buscar:
        maquinarias = maquinarias.filter(
            Q(codigo_serie__icontains=buscar) |
            Q(estado__icontains=buscar)
        )

    # Orden personalizado: primero habilitado (0), luego inhabilitado (1), luego otros estados (2)
    maquinarias = maquinarias.annotate(
        estado_orden=Case(
            When(estado='habilitado', then=Value(0)),
            When(estado='inhabilitado', then=Value(1)),
            default=Value(2),
            output_field=IntegerField(),
        )
    ).order_by('estado_orden')

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

from datetime import timedelta


from datetime import timedelta
from decimal import Decimal
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404

def cambiar_estado_maquinaria(request, id):
    if request.method == 'POST':
        maquina = get_object_or_404(Maquinaria, id=id)
        empleado_mail = get_object_or_404(Cliente, id=request.session.get("cliente_id"))

        # Verificar si tiene alquileres en curso
        if maquina.estado == 'habilitado':
            if Alquiler.objects.filter(codigo_maquina=maquina, estado='enCurso').exists():
                messages.error(request, f"No se puede inhabilitar la maquinaria '{maquina.codigo_serie}' porque tiene un alquiler en curso.")
                return redirect('ver_maquinarias')

            opcion = request.POST.get('opcion')

            if opcion == '1':
                dias_inhabilitacion = 1
            elif opcion == 'varios':
                dias_extra = request.POST.get('dias_extra')
                if not dias_extra or int(dias_extra) < 1:
                    messages.error(request, 'Debés ingresar un número de días válido (mínimo 1) para inhabilitar la maquina.')
                    return redirect('ver_maquinarias')
                dias_inhabilitacion = int(dias_extra)
            else:
                messages.error(request, 'Opción inválida.')
                return redirect('ver_maquinarias')

            # Inhabilitar la máquina
            maquina.estado = 'inhabilitado'
            maquina.fecha_habilitacion = timezone.now() + timedelta(days=dias_inhabilitacion)
            maquina.save()

            # Cancelar alquileres pendientes que empiecen durante la inhabilitación
            fecha_limite = maquina.fecha_habilitacion
            hoy = timezone.now().date()
            alquileres_a_cancelar = Alquiler.objects.filter(
                codigo_maquina=maquina,
                estado='pendienteRetiro',
                desde__lte=fecha_limite.date()
            )

            for alquiler in alquileres_a_cancelar:
                # Calcular monto a devolver
                dias = (alquiler.hasta - alquiler.desde).days
                monto_total = maquina.precio_alquiler_diario * Decimal(dias)
                tarjeta = alquiler.tarjeta
                if tarjeta:
                    tarjeta.monto += monto_total
                    tarjeta.save()
                alquiler.precio = Decimal('0.00')
                alquiler.estado = 'finalizado'
                alquiler.cancelado = True
                alquiler.save()

            messages.success(request, f"La maquinaria '{maquina.codigo_serie}' fue inhabilitada por {dias_inhabilitacion} día(s). Se cancelaron {alquileres_a_cancelar.count()} alquiler(es) pendientes.")

        else:
            # Habilitar la maquinaria
            maquina.estado = 'habilitado'
            maquina.fecha_habilitacion = None
            maquina.save()
            messages.success(request, f"La maquinaria '{maquina.codigo_serie}' fue habilitada correctamente.")

        return redirect('ver_maquinarias')


from decimal import Decimal
from django.utils import timezone

def eliminar_maquinaria(request, maquinaria_id):
    maquinaria = get_object_or_404(Maquinaria, id=maquinaria_id)

    # Impide eliminación si hay un alquiler en curso
    tiene_alquiler_en_curso = Alquiler.objects.filter(
        codigo_maquina=maquinaria,
        estado='enCurso'
    ).exists()

    if tiene_alquiler_en_curso:
        messages.error(request, 'No se puede eliminar la maquinaria porque tiene un alquiler en curso.')
    elif maquinaria.estado == 'eliminado':
        messages.warning(request, 'La maquinaria ya está marcada como eliminada.')
    else:
        # Cancelar alquileres en estado 'pendienteRetiro'
        alquileres_pendientes = Alquiler.objects.filter(
            codigo_maquina=maquinaria,
            estado='pendienteRetiro'
        )

        for alquiler in alquileres_pendientes:
            # Calcular monto total del alquiler
            dias = (alquiler.hasta - alquiler.desde).days
            monto_total = maquinaria.precio_alquiler_diario * Decimal(dias)

            # Devolver 100% del monto
            tarjeta = alquiler.tarjeta
            if tarjeta:
                tarjeta.monto += monto_total
                tarjeta.save()

            alquiler.precio = Decimal('0.00')
            alquiler.estado = 'finalizado'
            alquiler.cancelado = True
            alquiler.save()

        maquinaria.estado = 'eliminado'
        maquinaria.save()

        messages.success(request, 'Maquinaria eliminada. Alquileres pendientes de retiro cancelados y dinero devuelto.')

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
from General.forms import FiltroAnioForm
from collections import defaultdict
def alquileres_por_maquina(request):
    form = FiltroAnioForm(request.GET or None)

    etiquetas = []
    cantidades = []
    hay_anio = False
    hay_datos = False
    maquinas = []

    if form.is_valid() and form.cleaned_data.get('anio'):
        anio = form.cleaned_data['anio']
        hay_anio = True

        alquileres = Alquiler.objects.filter(
            estado__in=['finalizado', 'pendienteRetiro', 'enCurso'],
            desde__year=anio
        )

        agrupados = defaultdict(int)

        for alquiler in alquileres:
            if alquiler.codigo_maquina: 
                clave = f"{alquiler.codigo_maquina.marca} {alquiler.codigo_maquina.modelo}"
                agrupados[clave] += 1

        resultados = sorted(agrupados.items(), key=lambda x: x[1], reverse=True)

        etiquetas = [r[0] for r in resultados]
        cantidades = [r[1] for r in resultados]
        hay_datos = sum(cantidades) > 0

        # Para tabla detalle
        maquinas = (
        Maquinaria.objects.exclude(estado='eliminado')
        .annotate(
            cantidad_alquileres=Count(
                'alquiler',
                filter=Q(
                    alquiler__estado__in=['finalizado', 'pendienteRetiro', 'enCurso'],
                    alquiler__desde__year=anio
                )
            )
        )
        .filter(cantidad_alquileres__gt=0)
        .order_by('-cantidad_alquileres')
    )

    return render(request, 'AlquileresPorMaquinaria.html', {
        'form': form,
        'etiquetas': etiquetas,
        'cantidades': cantidades,
        'hay_anio': hay_anio,
        'hay_datos': hay_datos,
        'maquinas': maquinas,
    })

def eliminarObservacion(request,id):


    observacion = get_object_or_404(Observacion,id=id)

    observacion.delete()
    messages.success(request,"observacion eliminada correctamente")
    return redirect('ver_maquinarias')