from django.shortcuts import render, redirect,  get_object_or_404
from .models import Cliente
from General.models import Cliente

from django.contrib import messages

def ver_clientes(request):
    #agregue el if para que solo los superUsuarios o staff puedar ver el listado y deshabilitar clientes
    #if not request.user.is_superuser and not request.user.is_staff:  
     #   messages.error(request, "No tenés permiso para acceder a esta página.")
      #  return redirect('inicio')  
    # Hasta aca lo de arriba
    habilitados = Cliente.objects.filter(estado='habilitado')
    inhabilitados = Cliente.objects.filter(estado='inhabilitado')
    return render(request, 'listadoCliente.html', {
        'habilitados': habilitados,
        'inhabilitados': inhabilitados
    })

def inhabilitar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    cliente.estado = 'inhabilitado'
    cliente.save()
    return redirect('ver_clientes')


def habilitar_cliente(request,id):
    cliente = get_object_or_404(Cliente, id=id)
    cliente.estado = 'habilitado'
    cliente.save()
    return redirect('ver_clientes')

def autodestruir_clientes(request):
    if request.method == "POST":
        Cliente.objects.all().delete()
    return redirect('ver_clientes')  