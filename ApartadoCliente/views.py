from django.shortcuts import render, redirect,  get_object_or_404

from General.models import Cliente

from django.contrib import messages

def ver_clientes(request):
    cliente_id = request.session.get('cliente_id')

    if not cliente_id:
       # messages.error(request, "Tenés que iniciar sesión.")
        return redirect('inicio')
    try:
        cliente = Cliente.objects.get(id=cliente_id)
    except Cliente.DoesNotExist:
        messages.error(request, "Tu sesión no es válida o el cliente fue eliminado.")
        return redirect('inicio')
    
    if cliente.rol not in ['jefe', 'empleados']:
       #messages.error(request, "No tenés permiso para acceder a esta página.")
       return redirect('inicio')  
    habilitados = Cliente.objects.filter(estado='habilitado').exclude(rol='jefe')
    inhabilitados = Cliente.objects.filter(estado='inhabilitado').exclude(rol='jefe')
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
    cliente_id = request.session.get('cliente_id')
    cliente = Cliente.objects.get(id=cliente_id)
    if request.method == "POST" and cliente.rol == 'jefe':
        Cliente.objects.all().delete()
        return redirect('inicio')  