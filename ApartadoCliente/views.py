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
from django.db.models import Q, Case, When, Value, IntegerField
def ver_clientes(request):
    cliente_id = request.session.get('cliente_id')
    cliente_actual = Cliente.objects.filter(id=cliente_id).first()

    # Excluye a los jefes del listado
    clientes = Cliente.objects.exclude(Q(rol='jefe') | Q(rol='empleados')).order_by('apellido')
   
    clientes = clientes.order_by(
        Case(
            When(estado='habilitado', then=Value(0)),
            When(estado='inhabilitado', then=Value(1)),
            default=Value(2),  # por si hay otro estado
            output_field=IntegerField()
        ),
        'apellido'
    )

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



from collections import defaultdict

def estadisticas_clientes(request):
    se_presiono_filtrar = 'fecha_desde' in request.GET or 'fecha_hasta' in request.GET
    form = FiltroFechaForm(request.GET if se_presiono_filtrar else None)

    etiquetas = []
    datos_habilitados = []
    datos_inhabilitados = []

    hay_rango = False
    hay_datos = False

    if se_presiono_filtrar and form.is_valid():
        fecha_desde = form.cleaned_data['fecha_desde']
        fecha_hasta = form.cleaned_data['fecha_hasta']

        hay_rango = True  

        clientes = Cliente.objects.exclude(rol='jefe') \
            .filter(fecha_registro__range=[fecha_desde, fecha_hasta])

        agrupados = defaultdict(lambda: {'habilitado': 0, 'inhabilitado': 0})

        for cliente in clientes:
            fecha = cliente.fecha_registro.strftime('%Y-%m-%d')
            agrupados[fecha][cliente.estado] += 1

        etiquetas = sorted(agrupados.keys())
        datos_habilitados = [agrupados[fecha]['habilitado'] for fecha in etiquetas]
        datos_inhabilitados = [agrupados[fecha]['inhabilitado'] for fecha in etiquetas]

        total = sum(datos_habilitados) + sum(datos_inhabilitados)
        hay_datos = total > 0  

    return render(request, 'estadisticasClientes.html', {
        'form': form,
        'etiquetas': etiquetas,
        'habilitados': datos_habilitados,
        'inhabilitados': datos_inhabilitados,
        'mostrar_errores': se_presiono_filtrar,
        'hay_rango': hay_rango,  
        'hay_datos': hay_datos,   
    })


