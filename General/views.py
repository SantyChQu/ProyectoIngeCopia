from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .forms import ClienteEdicionForm, ClienteRegistroForm, CambiarContraseñaForm, tarjetaForm
from django.contrib.auth import login,logout
from django.db import IntegrityError
from .models import Cliente,Maquinaria, Localidad, Tarjeta, Alquiler
from django.contrib import messages
from django.contrib.auth.hashers import check_password 
from django.db import connection
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from datetime import date
from django.utils.crypto import get_random_string
from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Q
from django.utils import timezone


def inicio(request):
    localidad_filtro = request.GET.get('localidad')
    marca_filtro = request.GET.get('marca')

    maquinarias = Maquinaria.objects.filter(estado='habilitado')

    if localidad_filtro:
        maquinarias = maquinarias.filter(localidad__id=localidad_filtro)
    if marca_filtro:
        maquinarias = maquinarias.filter(marca__icontains=marca_filtro)

    localidades = Localidad.objects.all()

    return render(request, 'PaginaPrincipal.html', {
        'maquinarias': maquinarias,
        'localidades': localidades,
        'marca_filtro': marca_filtro or '',
        'localidad_filtro': int(localidad_filtro) if localidad_filtro else ''
    })

def hacer_reserva(request, maquinaria_id):
    if 'cliente_id' not in request.session:
        return redirect('/registro/')

    maquinaria = get_object_or_404(Maquinaria, id=maquinaria_id)
    cliente = Cliente.objects.get(id=request.session['cliente_id'])

    alquileres_existentes = Alquiler.objects.filter(
       codigo_maquina=maquinaria,
      estado='pendienteRetiro'
    )
    if request.method == 'POST':
        fecha_inicio_str = request.POST.get('fecha_inicio')
        fecha_fin_str = request.POST.get('fecha_fin')

        if fecha_inicio_str and fecha_fin_str:
            fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
            fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()
            hoy = datetime.today().date()

            if fecha_inicio < hoy:
                messages.error(request, 'La fecha de inicio no puede ser anterior a hoy.')
            elif fecha_fin < fecha_inicio:
                messages.error(request, 'La fecha de fin no puede ser anterior a la fecha de inicio.')
            else:
                conflicto = alquileres_existentes.filter(
                    Q(desde__lte=fecha_fin) & Q(hasta__gte=fecha_inicio)
                ).exists()

                if conflicto:
                    messages.error(request, 'La máquina ya está reservada en ese rango de fechas.')
                else:
                    codigo = get_random_string(10)
                    request.session['reserva'] = {
                        'codigo': codigo,
                        'maquinaria_id': maquinaria.id,
                        'fecha_inicio': fecha_inicio.strftime("%Y-%m-%d"),
                        'fecha_fin': fecha_fin.strftime("%Y-%m-%d")
                    }
                    return redirect('pago')
        else:
            messages.error(request, 'Fechas inválidas.')

    # Generar fechas ocupadas para mostrar en el calendario
    fechas_ocupadas = []
    for alquiler in alquileres_existentes:
        actual = alquiler.desde
        while actual <= alquiler.hasta:
            fechas_ocupadas.append(actual.strftime("%Y-%m-%d"))
            actual += timedelta(days=1)

    return render(request, 'HacerReserva.html', {
        'maquinaria': maquinaria,
        'fechas_ocupadas': fechas_ocupadas,
    })
# ------------------------- AUTODESTRUIR MAQUINARIAS -----------------------------------------
def autodestruir_maquinarias(request):
#    with connection.cursor() as cursor:
#        cursor.execute("DELETE FROM General_maquinaria")
#    return redirect('ver_clientes') 
    maquinarias = Maquinaria.objects.all()

    for maq in maquinarias:
        if Alquiler.objects.filter(codigo_maquina_id=maq).exists():
            # Si hay relaciones, no la borres
            continue
        maq.delete()

    messages.success(request, "Se eliminaron todas las maquinarias que no estaban en uso.")
    return redirect('ver_maquinarias')





def registro(request):
    if request.method == 'GET':
        print('Enviando formulario')
        form = ClienteRegistroForm()
        return render(request, 'registro.html', {'form': form})
    
    else:  
        form = ClienteRegistroForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Registro exitoso')
                return redirect('ingreso') 
            except IntegrityError:
                return render(request, 'registro.html', {
                    'form': form,
                    'error': 'Ya existe un cliente con esos datos.'
                })
        else:
          
            return render(request, 'registro.html', {'form': form})

def ingresar(request):
    mail = ''  # Inicializamos mail vacío por defecto

    if request.method == 'POST':
        mail = request.POST.get('mail')
        contraseña = request.POST.get('contraseña')

        try:
            cliente = Cliente.objects.get(mail=mail)

            if cliente.estado != "habilitado":
                messages.error(request, 'Tu cuenta está deshabilitada. Contacta al administrador')
            elif cliente.contraseña == contraseña:
                request.session['cliente_id'] = cliente.id
                request.session['cliente_nombre'] = cliente.nombre
                request.session['cliente_rol'] = cliente.rol

                #  si inicia sesión correctamente
                messages.success(request, 'Inicio de sesion correctamente')
                return redirect('/')
            else:
                messages.error(request, 'Contraseña incorrecta')

        except Cliente.DoesNotExist:
            messages.error(request, 'Correo no registrado')

        return render(request, 'ingreso.html', {'mail': mail})

    # Solo muestra el formulario sin mensaje
    return render(request, 'ingreso.html', {'mail': ''})
                  
def cerrarSesion(request):
    request.session.flush()  # Limpia la sesión por completo
    messages.success(request, 'Sesión cerrada correctamente')
    return redirect('/')  # Redirige al login o página principa


def VerDatos(request):
    cliente_id = request.session.get('cliente_id')
    cliente = Cliente.objects.get(id=cliente_id)

    if request.method == 'GET':
        form = ClienteEdicionForm(instance=cliente)
        return render(request, 'VerDatos.html', {
            'form': form,
            'form_cambiar_contraseña': CambiarContraseñaForm(),
            'mostrar_modal': False
        })

    elif request.method == 'POST':
        form = ClienteEdicionForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Datos actualizados correctamente')
            return redirect('/verMisDatos')
        else:
            print(form.errors)
            return render(request, 'VerDatos.html', {
                'form': form,
                'form_cambiar_contraseña': CambiarContraseñaForm(),
                'mostrar_modal': False
            })

        
def cambiar_contraseña(request):
    cliente_id = request.session.get('cliente_id')
    cliente = Cliente.objects.get(id=cliente_id)

    if request.method == 'POST':
        form = CambiarContraseñaForm(request.POST)

        if form.is_valid():
            actual = form.cleaned_data['actual']
            nueva = form.cleaned_data['nueva']

            if cliente.contraseña != actual:
                form.add_error('actual', 'La contraseña actual no es correcta.')
            else:
                cliente.contraseña = nueva
                cliente.save()
                messages.success(request, 'Contraseña actualizada correctamente.')
                return redirect('/verMisDatos')
    else:
        form = CambiarContraseñaForm()

    cliente_form = ClienteEdicionForm(instance=cliente)

    return render(request, 'VerDatos.html', {
        'form': cliente_form,
        'form_cambiar_contraseña': form,
        'mostrar_modal': True,  # Esto hace que el modal se abra con errores
        'error_contraseña': True  # Esto hace que el JS también lo abra
    })



#REALIZAR PAGO


def realizar_pago(request):
    if 'cliente_id' not in request.session:
        return redirect('/registro/')

    cliente_id = request.session.get('cliente_id')
    c = Cliente.objects.get(id=cliente_id)

    try:
        datos_reserva = request.session.get('reserva')
        maquinaria = Maquinaria.objects.get(id=datos_reserva['maquinaria_id'])

        fecha_inicio = datetime.strptime(datos_reserva['fecha_inicio'], "%Y-%m-%d").date()
        fecha_fin = datetime.strptime(datos_reserva['fecha_fin'], "%Y-%m-%d").date()
        dias = (fecha_fin - fecha_inicio).days

        if dias <= 0:
            messages.error(request, 'La fecha de fin debe ser posterior a la de inicio.')
            return redirect('/')

        monto_total = maquinaria.precio_alquiler_diario * dias

    except (KeyError, Maquinaria.DoesNotExist, TypeError, ValueError):
        messages.error(request, 'Hubo un problema con la reserva. Volvé a intentarlo.')
        return redirect('/')

    if request.method == 'POST':
        form = tarjetaForm(request.POST)
        if form.is_valid():
            numero = form.cleaned_data['numero']
            numeroseguridad = form.cleaned_data['numeroseguridad']
            nombre_propietario = form.cleaned_data['nombre_propietario']
            fecha_desde = form.cleaned_data['fecha_desde']
            fecha_hasta = form.cleaned_data['fecha_hasta']

            try:
                tarjeta = Tarjeta.objects.get(numero_tarjeta=numero)
            except Tarjeta.DoesNotExist:
                messages.error(request, 'Tarjeta no registrada')
                return render(request, 'RealizarPago.html', {'form': form, 'monto_total': monto_total})

            # Validaciones adicionales
            errores = []
            if tarjeta.numero_seguridad != numeroseguridad:
                errores.append('Número de seguridad inválido.')

            if tarjeta.nombre_propietario.lower() != nombre_propietario.lower():
                errores.append('El nombre del propietario no coincide.')

            if tarjeta.fecha_desde != fecha_desde:
                errores.append('La fecha de inicio de vigencia no coincide.')

            if tarjeta.fecha_hasta != fecha_hasta:
                errores.append('La fecha de vencimiento no coincide.')

            if tarjeta.monto < monto_total:
                errores.append('Saldo insuficiente.')

            if errores:
                for e in errores:
                    messages.error(request, e)
                return render(request, 'RealizarPago.html', {'form': form, 'monto_total': monto_total})

            # Si todo está OK, se guarda el pago y el alquiler
            tarjeta.monto -= monto_total
            tarjeta.save()

            Alquiler.objects.create(
                codigo_identificador=datos_reserva['codigo'],
                codigo_maquina=maquinaria,
                mail=c,
                desde=datos_reserva['fecha_inicio'],
                hasta=datos_reserva['fecha_fin'],
                tarjeta=tarjeta,
                precio=monto_total,
            )

            messages.success(request, 'Pago realizado correctamente.')
            return render(request, 'PaginaPrincipal.html', {'mensajeExito': True})

        else:
            messages.error(request, 'Formulario inválido.')
            return render(request, 'RealizarPago.html', {'form': form, 'monto_total': monto_total})

    else:
        form = tarjetaForm()
        return render(request, 'RealizarPago.html', {'form': form, 'monto_total': monto_total})


def misalquileres(request):

    if 'cliente_id' not in request.session:
        return redirect('/registro/')  # o a tu vista de login

    cliente_id = request.session['cliente_id']
    cliente = Cliente.objects.get(id=cliente_id)

    # Obtener todos los alquileres del cliente
    alquileres = Alquiler.objects.filter(mail=cliente).order_by('desde')

    return render(request, 'misalquileres.html', {'alquileres': alquileres})          


def cancelar_alquiler(request, alquiler_id):
    alquiler = get_object_or_404(Alquiler, id=alquiler_id)

    # Verificamos que el alquiler pertenezca al cliente logueado
    cliente_id = request.session.get('cliente_id')
    if alquiler.mail.id != cliente_id:
        messages.error(request, 'No tenés permiso para cancelar este alquiler.')
        return redirect('/misalquileres')

    # Solo se puede cancelar si aún no está finalizado
    if alquiler.estado == 'finalizado':
        messages.error(request, 'Este alquiler ya fue finalizado.')
        return redirect('/misalquileres')

    # Verificamos que falten al menos 2 días para que empiece el alquiler
    hoy = timezone.now().date()
    if (alquiler.desde - hoy).days < 2:
        messages.error(request, 'Solo podés cancelar alquileres con al menos 2 días de anticipación.')
        return redirect('/misalquileres')

    maquinaria = alquiler.codigo_maquina
    politica = maquinaria.politica

    # Calculamos el total pagado
    dias = (alquiler.hasta - alquiler.desde).days
    monto_total = maquinaria.precio_alquiler_diario * Decimal(dias)

    # Porcentaje de devolución
    porcentaje_devolucion = politica.porcentaje / Decimal(100)
    monto_a_devolver = monto_total * porcentaje_devolucion

    tarjeta = alquiler.tarjeta
    if tarjeta:
        tarjeta.monto += monto_a_devolver
        tarjeta.save()

    alquiler.precio = monto_total - monto_a_devolver
    alquiler.estado = 'finalizado'
    alquiler.save()

    messages.success(
        request,
        f'Alquiler cancelado. Se devolvieron ${monto_a_devolver:.2f} según la política de cancelación.'
    )
    return redirect('/misalquileres')