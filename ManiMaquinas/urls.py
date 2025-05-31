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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from General import views as general
from ApartadoCliente import views as cliente_views
from ApartadoMaquina import views as maquinas_views

import os
urlpatterns = [
    path("admin/", admin.site.urls),
    path('', general.inicio, name='inicio'),
    path('ingreso/', general.ingresar, name='ingreso'),
    path('cerrarSesion/', general.cerrarSesion),
    path('registro/', general.registro),
    path('verMisDatos/',general.VerDatos),
    path('cambiar_contraseña/', general.cambiar_contraseña, name='cambiar_contraseña'),
    path('clientes/', cliente_views.ver_clientes, name='ver_clientes'), 
   # path('inhabilitar_cliente/<int:id>/', cliente_views.inhabilitar_cliente, name='inhabilitar_cliente'),
   # path('cliente/habilitar/<int:id>/', cliente_views.habilitar_cliente, name='habilitar_cliente'),
    path('agregar_maquina/', maquinas_views.agregar_maquina, name='agregar_maquina'),
    path('autodestruir/', cliente_views.autodestruir_clientes, name='autodestruir_clientes'),
    path('maquinarias/', maquinas_views.ver_maquinarias, name='ver_maquinarias'),
    #
    path('maquinarias/cambiar_estado/<int:id>/', maquinas_views.cambiar_estado_maquinaria, name='cambiar_estado_maquinaria'),
    path('clientes/cambiar_estado/<int:id>/', cliente_views.cambiar_estado_Cliente, name='cambiar_estado_Cliente'),
    path('maquinaria/modificar/<int:id>/', maquinas_views.modificar_maquina, name='modificar_maquina'),
    
    path('maquinarias/autodestruir/', general.autodestruir_maquinarias, name='autodestruir_maquinarias'),
    path('hacer_reserva/<int:maquinaria_id>/', general.hacer_reserva, name='hacer_reserva'),
    path('RealizarPago/',general.realizar_pago , name='pago'),
    path('RealizarPago/',general.realizar_pago , name='pago'),
    path('misalquileres/',general.misalquileres)

    ]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'static'))
