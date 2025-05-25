from django.shortcuts import render, redirect
from .models import Cliente
from .forms import ClienteUpdateForms
# Create your views here.
def home(request):
    return render(request, 'home.html')
def tasks(request):
    return render(request, 'tasks.html') 

def ver_clientes(request):
    # pylint: disable=no-member
    clientes = Cliente.objects.all().order_by('apellido')
    return render(request, 'listadoCliente.html', {'clientes': clientes})

def registrar_cliente(request):
    if request.method == 'POST':
        form = ClienteUpdateForms(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tasks')  
    else:
        form = ClienteUpdateForms()
    
    return render(request, 'signup.html', {'form': form})

