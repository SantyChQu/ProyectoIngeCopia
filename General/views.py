from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .forms import ClienteForm, CambiarContraseñaForm
from django.contrib.auth import login,logout
from django.db import IntegrityError
from .models import Cliente
from django.contrib import messages
from django.contrib.auth.hashers import check_password 

def inicio(request):
    return render(request, 'PaginaPrincipal.html')


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
            if cliente.contraseña == contraseña:  # O usar check_password si estás hasheando
                # Guardamos el cliente en la sesión manualmente
                request.session['cliente_id'] = cliente.id
                request.session['cliente_nombre'] = cliente.nombre
                return redirect('/')  # Cambiá por donde quieras redirigir
            else:
                messages.error(request, 'Contraseña incorrecta')
        except Cliente.DoesNotExist:
            messages.error(request, 'Correo no registrado')

        return render(request, 'ingreso.html', {'mail': mail})  # mantener input si querés

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

