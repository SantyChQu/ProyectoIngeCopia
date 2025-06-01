from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .forms import ClienteForm, CambiarContraseñaForm, tarjetaForm
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
        return redirect('/registro/')  # o donde tengas el login o registro

    maquinaria = get_object_or_404(Maquinaria, id=maquinaria_id)
    cliente = Cliente.objects.get(id=request.session['cliente_id'])

    if request.method == 'POST':
        fecha_inicio = request.POST.get('fecha_inicio')
        fecha_fin = request.POST.get('fecha_fin')

        if fecha_inicio and fecha_fin:
            # Generar un código de alquiler único
            codigo = get_random_string(10)

            # Guardar en sesión los datos del alquiler (o pasarlos por GET/POST a la siguiente vista)
            request.session['reserva'] = {
                'codigo': codigo,
                'maquinaria_id': maquinaria.id,
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            }

            return redirect('pago')  # Redirige a la vista de pago
        else:
            messages.error(request, 'Fechas inválidas.')

    return render(request, 'HacerReserva.html', {'maquinaria': maquinaria})
    #return render(request, 'HacerReserva.html', {'maquinaria': maquinaria})

def autodestruir_maquinarias(request):
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM General_maquinaria")
    return redirect('ver_clientes') 

def registro(request):
    if request.method == 'GET':
        print('Enviando formulario')
        form = ClienteForm()
        return render(request, 'registro.html', {'form': form})
    
    else:  
        form = ClienteForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, '¡Registro exitoso! Ya podés iniciar sesión.')
                return redirect('ingreso') 
            except IntegrityError:
                return render(request, 'registro.html', {
                    'form': form,
                    'error': 'Ya existe un cliente con esos datos.'
                })
        else:
          
            return render(request, 'registro.html', {'form': form})

def ingresar(request):
    if request.method == 'POST':
        mail = request.POST.get('mail')
        contraseña = request.POST.get('contraseña')

        try:
            cliente = Cliente.objects.get(mail=mail)

            if cliente.estado != "habilitado":
                messages.error(request, 'Tu cuenta está deshabilitada. Contacta al administrador.')
            elif cliente.contraseña == contraseña:  # Si usas hashing, reemplaza esto por check_password
                # Guardamos datos en la sesión
                request.session['cliente_id'] = cliente.id
                request.session['cliente_nombre'] = cliente.nombre
                request.session['cliente_rol'] = cliente.rol

                # Redirección según rol
                return redirect('/')
            else:
                messages.error(request, 'Contraseña incorrecta')

        except Cliente.DoesNotExist:
            messages.error(request, 'Correo no registrado')

        # En todos los casos de error, se vuelve al formulario con el mail ya cargado
        return render(request, 'ingreso.html', {'mail': mail})

    return render(request, 'ingreso.html')
                  
def cerrarSesion(request):
    request.session.flush()  # Limpia la sesión por completo
    return redirect('/')  # Redirige al login o página principa


def VerDatos(request):
    cliente_id = request.session.get('cliente_id')
    cliente = Cliente.objects.get(id=cliente_id)

    if request.method == 'GET':
        form = ClienteForm(instance=cliente)
        return render(request, 'VerDatos.html', {
            'form': form,
            'form_cambiar_contraseña': CambiarContraseñaForm(),
            'mostrar_modal': False
        })

    elif request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
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

    cliente_form = ClienteForm(instance=cliente)

    return render(request, 'VerDatos.html', {
        'form': cliente_form,
        'form_cambiar_contraseña': form,
        'mostrar_modal': True,  # Esto hace que el modal se abra con errores
        'error_contraseña': True  # Esto hace que el JS también lo abra
    })



#REALIZAR PAGO

def realizar_pago(request):

    cliente_id = request.session.get('cliente_id')
    c = Cliente.objects.get(id=cliente_id)
    try:
        datos_reserva = request.session.get('reserva')
        maquinaria = Maquinaria.objects.get(id=datos_reserva['maquinaria_id'])
    except (KeyError, Maquinaria.DoesNotExist, TypeError):
        messages.error(request, 'Hubo un problema con la reserva. Volvé a intentarlo.')
        return redirect('/')  

    if 'cliente_id' not in request.session:
        return redirect('/registro/') 
    if request.method == 'POST':
        form = tarjetaForm(request.POST)
        if form.is_valid():
            numero = form.cleaned_data['numero']
            numeroseguridad = form.cleaned_data['numeroseguridad']
            monto = form.cleaned_data['monto']

            try:
                tarjeta = Tarjeta.objects.get(numero_tarjeta=numero)
            except Tarjeta.DoesNotExist:
                messages.error(request, 'Tarjeta no encontrada.')
                return render(request, 'RealizarPago.html', {'form': form})

            if tarjeta.numero_seguridad != numeroseguridad:
                messages.error(request, 'Número de seguridad inválido.')
            elif tarjeta.monto < monto:
                messages.error(request, 'Saldo insuficiente.')
            else:
                tarjeta.monto -= monto
                tarjeta.save()
                a = Alquiler.objects.create(
                 codigo_identificador=datos_reserva['codigo'],
                 codigo_maquina=maquinaria,
                 mail=c,
                 desde=datos_reserva['fecha_inicio'],
                 hasta=datos_reserva['fecha_fin'],
                 tarjeta=tarjeta  # ← Esta línea debe estar alineada con las anteriores
                )
                messages.success(request, 'Pago realizado correctamente.')
                return render(request,'PaginaPrincipal.html',{'mensajeExito':True})

        else:
            messages.error(request, 'Formulario inválido.')

        return render(request, 'RealizarPago.html', {'form': form})

    else:
        form = tarjetaForm()
        return render(request, 'RealizarPago.html', {'form': form})

def misalquileres(request):

    if 'cliente_id' not in request.session:
        return redirect('/registro/')  # o a tu vista de login

    cliente_id = request.session['cliente_id']
    cliente = Cliente.objects.get(id=cliente_id)

    # Obtener todos los alquileres del cliente
    alquileres = Alquiler.objects.filter(mail=cliente)
    for a in alquileres:
        dias = (a.hasta - a.desde).days
        a.precio_total = a.codigo_maquina.precio_alquiler_diario * dias

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

    alquiler.estado = 'finalizado'
    alquiler.save()

    messages.success(request, f'Alquiler cancelado. Se devolvieron ${monto_a_devolver:.2f} según la política de cancelación.')
    return redirect('/misalquileres')