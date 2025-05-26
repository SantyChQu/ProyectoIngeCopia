from django.shortcuts import render
from .models import Cliente
from General.models import Cliente

def ver_clientes(request):
    # pylint: disable=no-member
    clientes = Cliente.objects.all().order_by('apellido')
    return render(request, 'listadoCliente.html', {'clientes': clientes})