from django.shortcuts import render, redirect,  get_object_or_404
from .models import Cliente
from General.models import Cliente

def ver_clientes(request):
    # pylint: disable=no-member
    #clientes = Cliente.objects.filter(estado='habilitado').order_by('apellido')
    #clientes = Cliente.objects.all().order_by('apellido')
    #return render(request, 'listadoCliente.html', {'clientes': clientes})
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
