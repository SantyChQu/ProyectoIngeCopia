from collections import defaultdict
from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .forms import ClienteEdicionForm, ClienteRegistroForm, CambiarContraseñaForm, tarjetaForm, LocalidadForm, EmpleadoRegistroForm,CalificacionForm, FiltroAnioForm
from django.contrib.auth import login,logout
from django.db import IntegrityError
from .models import Cliente,Maquinaria, Localidad, Tarjeta, Alquiler,Calificacion, Observacion
from django.contrib import messages
from django.contrib.auth.hashers import check_password 
from django.db import connection
from django.contrib.auth.decorators import login_required
from datetime import date, datetime, timedelta, time
from django.utils.crypto import get_random_string
from decimal import Decimal
from django.db.models import Q
from django.utils import timezone
from django.db.models import Q, Case, When, Value, IntegerField
from django.views.decorators.http import require_POST
from django.urls import reverse
from math import ceil

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

import json  # Por si querés usar JsonResponse en otra parte

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

    # Generar fechas ocupadas sumando un día extra al final
    fechas_ocupadas = []
    for alquiler in alquileres_existentes:
        actual = alquiler.desde
        fin_con_extra = alquiler.hasta + timedelta(days=1)
        while actual <= fin_con_extra:
            fechas_ocupadas.append(actual.strftime("%Y-%m-%d"))
            actual += timedelta(days=1)

    return render(request, 'HacerReserva.html', {
        'maquinaria': maquinaria,
        'fechas_ocupadas': fechas_ocupadas,
    })

# ------------------------- AUTODESTRUIR MAQUINARIAS -----------------------------------------
def autodestruir_maquinarias(request):
    Maquinaria.objects.all().delete()
    messages.success(request, "Se eliminaron todas las maquinarias.")
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
                messages.error(request, 'Mail y/o Contraseña incorrecta.')

        except Cliente.DoesNotExist:
            messages.error(request, 'Mail y/o Contraseña incorrecta.')

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


from decimal import Decimal
def realizar_pago(request):
    if 'cliente_id' not in request.session:
        return redirect('/registro/')

    cliente_id = request.session.get('cliente_id')
    c = Cliente.objects.get(id=cliente_id)

    alquiler_id = request.GET.get('alquiler_id')
    monto_total = request.GET.get('monto')
    if monto_total:
        try:
            monto_total = Decimal(monto_total)
        except:
            messages.error(request, 'Monto inválido.')
            return redirect('ver_alquileres')
    # Si es pago por devolución con retraso (pago pendiente)
    if alquiler_id and monto_total:
        alquiler = get_object_or_404(Alquiler, id=alquiler_id)

        try:
            monto_total = Decimal(monto_total)
        except ValueError:
            messages.error(request, 'Monto inválido.')
            return redirect('ver_alquileres')

    else:
        # Pago normal (reserva nueva)
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
            numero = form.cleaned_data['numero'].replace(" ", "").replace("-", "")
            numeroseguridad = form.cleaned_data['numeroseguridad']
            nombre_propietario = form.cleaned_data['nombre_propietario']
            fecha_desde = form.cleaned_data['fecha_desde']
            fecha_hasta = form.cleaned_data['fecha_hasta']

            try:
                tarjeta = Tarjeta.objects.get(numero_tarjeta=numero)
            except Tarjeta.DoesNotExist:
                messages.error(request, 'Tarjeta no registrada')
                return render(request, 'RealizarPago.html', {'form': form, 'monto_total': monto_total})

            errores = []
            if tarjeta.numero_seguridad != numeroseguridad:
                errores.append('Número de seguridad inválido.')
            if tarjeta.nombre_propietario.lower() != nombre_propietario.lower():
                errores.append('El nombre del propietario no coincide.')
            if tarjeta.fecha_desde != fecha_desde:
                errores.append('La fecha de inicio de vigencia no coincide.')
            if tarjeta.fecha_hasta != fecha_hasta:
                errores.append('La fecha de vencimiento no coincide.')

            if errores:
                for e in errores:
                    messages.error(request, e)
                return render(request, 'RealizarPago.html', {'form': form, 'monto_total': monto_total})

            if tarjeta.monto < monto_total:
                messages.error(request, 'Saldo insuficiente.')
                return render(request, 'RealizarPago.html', {'form': form, 'monto_total': monto_total})

            # Todo OK: descontar monto
  
            tarjeta.monto -= monto_total
            tarjeta.save()

            if alquiler_id and monto_total:
                # Pago por devolución con retraso
                alquiler.estado = 'finalizado'
                alquiler.tarjeta = tarjeta
                alquiler.precio += monto_total  # sumamos recargo
                alquiler.save()
                messages.success(request, 'Pago de devolución con retraso realizado correctamente.')
                return redirect('ver_alquileres')
            else:
                # Pago normal: crear alquiler nuevo
                alquiler = Alquiler(
                    codigo_identificador=datos_reserva['codigo'],
                    codigo_maquina=maquinaria,
                    mail=c,
                    desde=datos_reserva['fecha_inicio'],
                    hasta=datos_reserva['fecha_fin'],
                    tarjeta=tarjeta,
                    precio=monto_total,
                    precioPorDia=Decimal(maquinaria.precio_alquiler_diario),
                )
                alquiler.save()
                messages.success(request, 'Pago realizado correctamente.')
                return redirect('/misalquileres/')

        else:
            messages.error(request, 'Formulario inválido.')
            return render(request, 'RealizarPago.html', {'form': form, 'monto_total': monto_total})

    else:
        form = tarjetaForm()
        return render(request, 'RealizarPago.html', {'form': form, 'monto_total': monto_total})


def misalquileres(request):
    if 'cliente_id' not in request.session:
        return redirect('/registro/')

    cliente_id = request.session['cliente_id']
    cliente = Cliente.objects.get(id=cliente_id)

    # Orden descendente por fecha: más recientes primero
    alquileres = Alquiler.objects.filter(mail=cliente).order_by('-desde')

    # Emparejamos alquiler con su formulario (solo si se puede puntuar)
    alquileres_forms = []
    for a in alquileres:
        if a.estado == 'finalizado' and a.calificacion is None:
            form = CalificacionForm()
        else:
            form = None
        alquileres_forms.append((a, form))

    context = {
        'alquileres_forms': alquileres_forms
    }

    return render(request, 'misalquileres.html', context)


def cancelar_alquiler(request, alquiler_id):
    alquiler = get_object_or_404(Alquiler, id=alquiler_id)

    cliente_id = request.session.get('cliente_id')
    rol_cliente = request.session.get('cliente_rol')

    # Solo cliente propietario o jefe puede cancelar
    if alquiler.mail.id != cliente_id and rol_cliente != 'jefe':
        messages.error(request, 'No tenés permiso para cancelar este alquiler.')
        return redirect('/misalquileres')

    # No se puede cancelar si ya está finalizado
    if alquiler.estado == 'finalizado':
        messages.error(request, 'Este alquiler ya fue finalizado.')
        return redirect('/misalquileres')

    # Solo los clientes (no jefes) deben cumplir la condición de los 2 días de anticipación
    if rol_cliente != 'jefe':
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
    if rol_cliente == 'jefe':
        monto_a_devolver = monto_total  # devolución completa
    else:
        porcentaje_devolucion = politica.porcentaje / Decimal(100)
        monto_a_devolver = monto_total * porcentaje_devolucion

    tarjeta = alquiler.tarjeta
    if tarjeta:
        tarjeta.monto += monto_a_devolver
        tarjeta.save()

    alquiler.precio = monto_total - monto_a_devolver
    alquiler.estado = 'finalizado'
    alquiler.cancelado = True
    alquiler.save()

    if rol_cliente == 'jefe':
        messages.success(
            request,
            f'Alquiler cancelado por jefe. Se devolvió el 100% (${monto_a_devolver:.2f}) al cliente.'
        )
        return redirect('/alquileres')
    else:
        messages.success(
            request,
            f'Alquiler cancelado. Se devolvieron ${monto_a_devolver:.2f} según la política de cancelación.'
        )
        return redirect('/misalquileres')

def puntuar_alquiler(request, alquiler_id):
    if request.method == 'POST':
        alquiler = get_object_or_404(
            Alquiler,
            id=alquiler_id,
            mail_id=request.session.get("cliente_id")
        )

        # Validación única
        if alquiler.estado != 'finalizado' or alquiler.cancelado or alquiler.calificacion is not None:
            return redirect('/misalquileres')

        form = CalificacionForm(request.POST)
        if form.is_valid():
            calificacion = Calificacion.objects.create(
                cliente_id=request.session.get("cliente_id"),
                estrellas=form.cleaned_data['estrellas'],
                nota=form.cleaned_data['nota']
            )
            alquiler.calificacion = calificacion  
            alquiler.save()

    return redirect('/misalquileres')

def agregar_observacion(request, maquina_id):
    if request.method == 'POST':
        maquinaria = get_object_or_404(Maquinaria, id=maquina_id)
        texto = request.POST.get('observacion')
        cliente = get_object_or_404(Cliente, id=request.session.get("cliente_id"))
        Observacion.objects.create(
            observacion=texto,
            mail = cliente.mail,
            codigo_maquina=maquinaria,
            fecha=timezone.now()
        )
    return redirect('/alquileres') 


def ver_localidades(request):
    localidades = Localidad.objects.all()

    buscar = request.GET.get('buscar', '')
    if buscar:
        localidades = localidades.filter(nombre__icontains=buscar)

    localidades = localidades.order_by('nombre')  

    if request.method == 'POST':
        form = LocalidadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('ver_localidades')
    else:
        form = LocalidadForm()

    return render(request, 'ver_localidades.html', {
        'localidades': localidades,
        'form': form
    })


def agregar_localidad(request):
    if request.method == 'POST':
        form = LocalidadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('ver_localidades')
    else:
        form = LocalidadForm()
    return render(request, 'agregar_localidad.html', {'form': form})

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Localidad, Alquiler


def eliminar_localidad(request, localidad_id):
    localidad = get_object_or_404(Localidad, id=localidad_id)

    tiene_alquileres = Alquiler.objects.filter(
        localidad=localidad,
        estado__in=['pendienteRetiro', 'enCurso', 'pendienteDevolucion']
    ).exists()

    maquinaria_asociada = Maquinaria.objects.filter(localidad=localidad).exists()

    if request.method == 'POST':
        if tiene_alquileres or maquinaria_asociada:
            mensaje = f"No se puede eliminar la localidad '{localidad.nombre}' porque "
            motivos = []
            if tiene_alquileres:
                motivos.append("tiene alquileres pendientes o en curso")
            if maquinaria_asociada:
                motivos.append("tiene maquinarias asociadas")
            mensaje += " y ".join(motivos) + "."
            messages.error(request, mensaje)
            return redirect('ver_localidades')

        localidad.delete()
        messages.success(request, f"Localidad '{localidad.nombre}' eliminada correctamente.")
        return redirect('ver_localidades')

    return render(request, 'confirmar_eliminacion.html', {
        'localidad': localidad,
        'maquinaria_asociada': maquinaria_asociada,
        'tiene_alquileres': tiene_alquileres,
    })

def proximo(request):

    return render(request,'proximamente.html')

#from django.shortcuts import render
from General.models import Alquiler, Localidad
from collections import defaultdict
from datetime import date, datetime
from General.forms import FiltroFechaForm
from datetime import datetime, time
from django.contrib import messages
def estadisticas_alquileres_localidad(request):
    form = FiltroFechaForm(request.GET or None)
    etiquetas, pendiente, en_curso, finalizado = [], [], [], []
    hay_datos = False 
    hay_rango = False
    fecha_desde = None
    fecha_hasta = None

    if request.method == 'GET' and form.is_valid():
        fecha_desde = form.cleaned_data['fecha_desde']
        fecha_hasta = form.cleaned_data['fecha_hasta']    
        localidades = Localidad.objects.all()
        estados = ['pendienteRetiro', 'enCurso', 'finalizado']
        datos = defaultdict(lambda: {estado: 0 for estado in estados})
        hay_rango = fecha_desde is not None and fecha_hasta is not None

        for localidad in localidades:
            fecha_desde_dt = datetime.combine(fecha_desde, time.min)
            fecha_hasta_dt = datetime.combine(fecha_hasta, time.max)

            alquileres = Alquiler.objects.filter(
                codigo_maquina__localidad=localidad,
                desde__range=(fecha_desde_dt, fecha_hasta_dt)
            )
            datos[localidad.nombre]['pendienteRetiro'] = alquileres.filter(estado='pendienteRetiro').count()
            datos[localidad.nombre]['enCurso'] = alquileres.filter(estado='enCurso').count()
            datos[localidad.nombre]['finalizado'] = alquileres.filter(estado='finalizado').count()

        etiquetas = list(datos.keys())
        pendiente = [datos[loc]['pendienteRetiro'] for loc in etiquetas]
        en_curso = [datos[loc]['enCurso'] for loc in etiquetas]
        finalizado = [datos[loc]['finalizado'] for loc in etiquetas]

        
        hay_datos = any(
            valor > 0 for valor in pendiente + en_curso + finalizado
        )

    return render(request, 'estadisticasAlquileres.html', {
        'form': form,  
        'etiquetas': etiquetas,
        'pendiente': pendiente,
        'en_curso': en_curso,
        'finalizado': finalizado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'hay_datos': hay_datos,  
        'hay_rango': hay_rango, 
    })


import secrets
import string
from django.contrib.auth.hashers import make_password
import random
def generar_password_aleatoria(longitud=10):
    caracteres = string.ascii_letters + string.digits
    return ''.join(random.choice(caracteres) for _ in range(longitud))


from django.core.mail import EmailMultiAlternatives
from email.header import Header
from django.core.mail import send_mail
from django.conf import settings
def enviar_mail(empleado, password):
    try:
        asunto = 'Tu cuenta fue creada'
        #asunto = Header('Tu cuenta fue creada', 'utf-8').encode()
        nombre = str(empleado.nombre)
        cuerpo = f'Hola {nombre}, tu contraseña es: {password}'
        from_email = settings.DEFAULT_FROM_EMAIL
        

        
        email = EmailMultiAlternatives(
            subject=asunto,
            body=cuerpo,
            #from_email='no-reply@manimaquinas.com',
            from_email = from_email, 
            to=[empleado.mail],
        )
        email.encoding = 'utf-8'

       
        email.send(fail_silently=False)

    except Exception as e:
        
        print(f"Tipo: {type(e)}")
        print(f"Mensaje: {e}")
        raise   
def registro_empleado(request):
    if request.session.get('cliente_rol') != 'jefe':
        messages.error(request, "No tenés permiso para acceder a esta sección.")
        return redirect('inicio')

    if request.method == 'POST':
        form = EmpleadoRegistroForm(request.POST)
        if form.is_valid():
            empleado = form.save(commit=False)

            password = generar_password_aleatoria()
            empleado.contraseña =password
            empleado.save()
           
            try:
                enviar_mail(empleado, password)
            except Exception as e:
             
                messages.error(request, f"No se pudo enviar el correo: {e}")


            messages.success(request, "Empleado registrado exitosamente. Se le envió la contraseña por mail.")
            return redirect('registro_empleado')
    else:
        form = EmpleadoRegistroForm()

    return render(request, 'registro_empleado.html', {'form': form})

from django.db.models import Q, Case, When, Value, IntegerField

def verEmpleados(request):
    buscar = request.GET.get('buscar', '').strip()

    cliente_id = request.session.get('cliente_id')
    cliente_actual = Cliente.objects.filter(id=cliente_id).first()

    empleados = Cliente.objects.filter(
        rol='empleados'
    )

    if buscar:
        empleados = empleados.filter(
            Q(nombre__icontains=buscar) | Q(mail__icontains=buscar)
        )

    empleados = empleados.order_by(
        Case(
            When(estado='habilitado', then=Value(0)),
            When(estado='inhabilitado', then=Value(1)),
            default=Value(2),
            output_field=IntegerField()
        ),
        'dni'
    )

    hay_clientes_no_jefes = empleados.exists()

    return render(request, 'listadoEmpleados.html', {
        'empleados': empleados,
        'cliente_actual': cliente_actual,
        'hay_clientes_no_jefes': hay_clientes_no_jefes,
        'buscar': buscar
    })


def cambiar_estado_Empleado(request, id):
   if request.method == 'POST':
        cliente = get_object_or_404(Cliente, id=id)
        if cliente.estado == 'habilitado':
            cliente.estado = 'inhabilitado'
            messages.error(request, f"El empleado  '{cliente.mail} ' fue dado de baja correctamente")
        else:
            cliente.estado = 'habilitado'
            messages.success(request, f"El empleado  '{cliente.mail}' fue recuperado correctamente")
        cliente.save()
        return redirect('verEmpleados')  

def estadisticas_ingresos_por_mes(request):
    form = FiltroAnioForm(request.GET or None)

    etiquetas = []
    ingresos = []
    hay_anio = False
    hay_datos = False

    if form.is_valid():
        anio = form.cleaned_data['anio']
        hay_anio = True

        alquileres = Alquiler.objects.filter(
            estado__in=['finalizado', 'pendienteRetiro', 'enCurso'],
            desde__year=anio
        )

        agrupados = defaultdict(float)

        for alquiler in alquileres:
            mes = alquiler.desde.strftime('%Y-%m')
            agrupados[mes] += float(alquiler.precio)

        meses = [f"{anio}-{str(m).zfill(2)}" for m in range(1, 13)]

        etiquetas = meses
        ingresos = [round(agrupados.get(mes, 0), 2) for mes in meses]

        hay_datos = sum(ingresos) > 0

    return render(request, 'estadisticaIngresos.html', {
        'form': form,
        'etiquetas': etiquetas,
        'ingresos': ingresos,
        'hay_anio': hay_anio,
        'hay_datos': hay_datos,
    })

from django.db.models import Q
from datetime import date
def ver_alquileres(request):
    alquileres = Alquiler.objects.all()

    hoy = date.today()

    if 'cliente_id' not in request.session:
        return redirect('/registro/')

    cliente_id = request.session['cliente_id']
    cliente = Cliente.objects.get(id=cliente_id)


    # Actualizar a pendienteDevolucion si corresponde
    alquileres_en_curso = alquileres.filter(estado='enCurso', hasta__lt=hoy)
    for alquiler in alquileres_en_curso:
        alquiler.estado = 'pendienteDevolucion'
        alquiler.save()

    # Búsqueda
    buscar = request.GET.get('buscar', '')
    if buscar:
        alquileres = alquileres.filter(
            Q(codigo_identificador__icontains=buscar) |
            Q(mail__mail__icontains=buscar)
        )

    alquileres = alquileres.order_by('-desde')

    # División en dos listas
    alquileres_finalizados = alquileres.filter(estado='finalizado')
    alquileres_no_finalizados = alquileres.exclude(estado='finalizado')


    def calcular_retraso_y_recargo(alquiler):
        dias_atraso = max((hoy - alquiler.hasta).days, 0)
        monto_recargo = alquiler.precioPorDia * dias_atraso
        alquiler.dias_atraso = dias_atraso
        alquiler.monto_recargo = monto_recargo

    for alquiler in alquileres_no_finalizados:
        calcular_retraso_y_recargo(alquiler)

    for alquiler in alquileres_finalizados:
        calcular_retraso_y_recargo(alquiler)

    context = {
        'alquileres_finalizados': alquileres_finalizados,
        'alquileres_no_finalizados': alquileres_no_finalizados,
        'buscar': buscar,
        'cliente': cliente,
    }

    return render(request, 'listadoAlquileres.html', context)


@require_POST
def aceptar_retiro(request, alquiler_id):
    alquiler = get_object_or_404(Alquiler, id=alquiler_id)
    hoy = date.today()
    if alquiler.desde > hoy:
        messages.warning(
        request, f"Aún no estamos en la fecha de inicio del alquiler "
        f"({alquiler.desde}). No se puede aceptar el retiro.")
    else:
        if alquiler.estado == 'pendienteRetiro':
            alquiler.estado = 'enCurso'
            alquiler.save()
            messages.success(request, f"Alquiler {alquiler.codigo_identificador} ahora está En Curso.")
        else:
            messages.warning(request, "No se puede aceptar retiro para este alquiler.")
    return redirect('ver_alquileres')


@require_POST
def aceptar_devolucion(request, alquiler_id):
    alquiler = get_object_or_404(Alquiler, id=alquiler_id)
    if alquiler.estado == 'enCurso':
        alquiler.estado = 'finalizado'
        alquiler.save()
        messages.success(request, f"Alquiler {alquiler.codigo_identificador} finalizado correctamente.")
    else:
        messages.warning(request, "No se puede aceptar devolución para este alquiler.")
    return redirect('ver_alquileres')


@require_POST
def aceptar_devolucion_con_retraso(request, alquiler_id):
    alquiler = get_object_or_404(Alquiler, id=alquiler_id)
    if alquiler.estado == 'pendienteDevolucion':
        hoy = date.today()
        dias_atraso = max((hoy - alquiler.hasta).days, 0)
        monto_recargo = (alquiler.precioPorDia * dias_atraso) * 1.5
        alquiler.dias_atraso = dias_atraso
        alquiler.monto_recargo = monto_recargo
        alquiler.estado = 'finalizado'
        alquiler.save()
        if dias_atraso > 0:
            messages.warning(
                request,
                f" Se aceptó la devolución con {dias_atraso} día(s) de retraso. "
                f"Recargo a cobrar: ${monto_recargo:.2f}."
            )
        else:
            messages.success(request, "Devolución aceptada sin recargo.")
    else:
        messages.error(request, "El alquiler no está en estado 'pendienteDevolucion'.")
    return redirect('ver_alquileres')
    
from django.db.models import Q

def historial_alquileres(request):
    buscar = request.GET.get('buscar', '')
    #alquileres = Alquiler.objects.filter(estado='finalizado')

    finalizados = Alquiler.objects.filter(estado='finalizado', cancelado=False)
    cancelados = Alquiler.objects.filter(estado='finalizado', cancelado=True)

    if buscar:
        finalizados = finalizados.filter(
            Q(codigo_identificador__icontains=buscar) |
            Q(mail__mail__icontains=buscar)
        )
        cancelados = cancelados.filter(
            Q(codigo_identificador__icontains=buscar) |
            Q(mail__mail__icontains=buscar)
        )

    finalizados = finalizados.order_by('-desde')
    cancelados = cancelados.order_by('-desde')

    return render(request, 'historial_alquileres.html', {
        'alquileres_finalizados': finalizados,
        'alquileres_cancelados': cancelados
    })
