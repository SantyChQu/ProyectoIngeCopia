"""
URL configuration for ManiMaquinas project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from General import views as general
from ApartadoCliente import views as cliente_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', general.inicio, name='inicio'),
    path('ingreso/', general.ingresar, name='ingreso'),
    path('cerrarSesion/', general.cerrarSesion),
    path('registro/', general.registro),
    path('verMisDatos/',general.VerDatos),
    path('cambiar_contraseña/', general.cambiar_contraseña, name='cambiar_contraseña'),
    path('clientes/', cliente_views.ver_clientes, name='ver_clientes'),
  
    ]
