from django.shortcuts import render, redirect,  get_object_or_404

from General.models import Cliente
from django.db.models import Q
from django.contrib import messages

#from django.db.models.functions import TruncDate
from .forms import FiltroFechaForm
from collections import defaultdict

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
    clientes = Cliente.objects.exclude(Q(rol='jefe') | Q(rol='empleados')).order_by('dni')

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
            messages.error(request, f"El cliente  '{cliente.mail} ' fue inhabilitado correctamente")
        else:
            cliente.estado = 'habilitado'
            messages.success(request, f"El cliente  '{cliente.mail}' fue habilitado correctamente")
        cliente.save()
        return redirect('ver_clientes')

def estadisticas_clientes(request):

    # Detectamos si se presionó "Filtrar"
    se_presiono_filtrar = 'fecha_desde' in request.GET or 'fecha_hasta' in request.GET
    #form = FiltroFechaForm(request.GET if se_presiono_filtrar else None)
    mostrar_errores = se_presiono_filtrar

    #form = FiltroFechaForm(request.GET or None)
    form = FiltroFechaForm(request.GET if se_presiono_filtrar else None)
    
    etiquetas = []
    datos_habilitados = []
    datos_inhabilitados = []
    
    if se_presiono_filtrar and form.is_valid(): #if form.is_valid():
        fecha_desde = form.cleaned_data['fecha_desde']
        fecha_hasta = form.cleaned_data['fecha_hasta']

        clientes = Cliente.objects.exclude(rol='jefe') \
                    .filter(fecha_registro__range=[fecha_desde, fecha_hasta])

        # Agrupamos por fecha y estado
        agrupados = defaultdict(lambda: {'habilitado': 0, 'inhabilitado': 0})

        for cliente in clientes:
            fecha = cliente.fecha_registro.strftime('%Y-%m-%d')
            agrupados[fecha][cliente.estado] += 1

        # Ordenamos por fecha
        etiquetas = sorted(agrupados.keys())
        datos_habilitados = [agrupados[fecha]['habilitado'] for fecha in etiquetas]
        datos_inhabilitados = [agrupados[fecha]['inhabilitado'] for fecha in etiquetas]

    return render(request, 'estadisticasClientes.html', {
        'form': form,
        'etiquetas': etiquetas,
        'habilitados': datos_habilitados,
        'inhabilitados': datos_inhabilitados,
        'mostrar_errores': mostrar_errores,
    })