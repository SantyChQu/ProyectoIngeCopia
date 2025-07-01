from collections import defaultdict
from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .forms import ClienteEdicionForm, ClienteRegistroForm, CambiarContraseñaForm, tarjetaForm, LocalidadForm, EmpleadoRegistroForm,CalificacionForm
from django.contrib.auth import login,logout
from django.db import IntegrityError
from .models import Cliente,Maquinaria, Localidad, Tarjeta, Alquiler,Calificacion
from django.contrib import messages
from django.contrib.auth.hashers import check_password 
from django.db import connection
from django.contrib.auth.decorators import login_required
from datetime import date, datetime, timedelta
from django.utils.crypto import get_random_string
from decimal import Decimal
from django.db.models import Q
from django.utils import timezone
from django.db.models import Q, Case, When, Value, IntegerField

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
            numero = numero.replace(" ", "").replace("-", "") 
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

        
            if errores:
                for e in errores:
                    messages.error(request, e)
                return render(request, 'RealizarPago.html', {'form': form, 'monto_total': monto_total})
                        
            try:
                    if tarjeta.monto < monto_total:
                         raise ValueError('Saldo insuficiente.')
            except ValueError as e:
                errores.append(str(e))
                for e in errores:
                    messages.error(request, e)
                return render(request, 'RealizarPago.html', {'form': form, 'monto_total': monto_total})

            # Si todo está OK, se guarda el pago y el alquiler
            tarjeta.monto -= monto_total
            tarjeta.save()

            alquiler = Alquiler(
                codigo_identificador=datos_reserva['codigo'],
                codigo_maquina=maquinaria,
                mail=c,
                desde=datos_reserva['fecha_inicio'],
                hasta=datos_reserva['fecha_fin'],
                tarjeta=tarjeta,
                precio=monto_total,
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

    alquileres = Alquiler.objects.filter(mail=cliente).order_by('desde')

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

def puntuar_alquiler(request, alquiler_id):
    if request.method == 'POST':
        alquiler = get_object_or_404(Alquiler, id=alquiler_id, mail_id=request.session.get("cliente_id"))


        if alquiler.estado != 'finalizado' or alquiler.calificacion is not None:
            return redirect('/misalquileres')

        form = CalificacionForm(request.POST)
        if form.is_valid():
            calificacion = Calificacion.objects.create(
                estrellas=form.cleaned_data['estrellas'],
                nota=form.cleaned_data['nota']
            )
            alquiler.calificacion = calificacion
            alquiler.save()

    return redirect('/misalquileres')



def ver_localidades(request):
    localidades = Localidad.objects.all()
    
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

def eliminar_localidad(request, localidad_id):
    localidad = get_object_or_404(Localidad, id=localidad_id)

    if request.method == 'POST':
        localidad.delete()
        return redirect('ver_localidades')

    return render(request, 'confirmar_eliminacion.html', {'localidad': localidad})

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
    hay_datos = False  # 🔑 NUEVO
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

from django.contrib import messages
from django.shortcuts import render, redirect

def generar_password_aleatoria(longitud=10):
    caracteres = string.ascii_letters + string.digits
    return ''.join(secrets.choice(caracteres) for _ in range(longitud))



from django.core.mail import EmailMultiAlternatives
from email.header import Header

def enviar_mail(empleado, password):
    try:
        
        asunto = Header('Tu cuenta fue creada', 'utf-8').encode()
        cuerpo = f'Hola {empleado.nombre}, tu contraseña es: {password}'

        

        
        email = EmailMultiAlternatives(
            subject=asunto,
            body=cuerpo,
            from_email='no-reply@manimaquinas.com',
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
            empleado.contraseña = make_password(password)
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

def verEmpleados(request):
    cliente_id = request.session.get('cliente_id')
    cliente_actual = Cliente.objects.filter(id=cliente_id).first()

    empleados = Cliente.objects.filter(
        rol='empleados'
    ).order_by(
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