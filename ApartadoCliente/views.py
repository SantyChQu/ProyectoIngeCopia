from django.shortcuts import render, redirect,  get_object_or_404

from General.models import Cliente

from django.contrib import messages

def autodestruir_clientes(request):
    cliente_id = request.session.get('cliente_id')
    cliente = Cliente.objects.filter(id=cliente_id).first()

    if request.method == "POST" and cliente and cliente.rol == 'jefe':
        Cliente.objects.exclude(id=cliente_id).delete()          
        return redirect('inicio')  

    return redirect('ver_clientes')

def ver_clientes(request):
    cliente_id = request.session.get('cliente_id')
    cliente_actual = Cliente.objects.filter(id=cliente_id).first()

    # Excluye a los jefes del listado
    clientes = Cliente.objects.exclude(rol='jefe')

    hay_clientes_no_jefes = clientes.exists()
    
    return render(request, 'listadoClientes.html', {
        'clientes': clientes,
        'cliente_actual': cliente_actual,
        'hay_clientes_no_jefes': hay_clientes_no_jefes,
    })

def cambiar_estado_Cliente(request, id):
   if request.method == 'POST':
        cliente = get_object_or_404(Cliente, id=id)
        if cliente.estado == 'habilitado':
            cliente.estado = 'inhabilitado'
            messages.success(request, f"El cliente  '{cliente.mail} ' fue inhabilitado correctamente")
        else:
            cliente.estado = 'habilitado'
            messages.success(request, f"El cliente  '{cliente.mail}' fue habilitado correctamente")
        cliente.save()
        return redirect('ver_clientes')