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
    path("EliminarObservacion/<int:id>", maquinas_views.eliminarObservacion, name='eliminarO'),
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
    path('maquinarias/eliminar/<int:maquinaria_id>/', maquinas_views.eliminar_maquinaria, name='eliminar_maquinaria'),

    path('maquinarias/autodestruir/', general.autodestruir_maquinarias, name='autodestruir_maquinarias'),
    path('hacer_reserva/<int:maquinaria_id>/', general.hacer_reserva, name='hacer_reserva'),
    path('RealizarPago/',general.realizar_pago , name='pago'),
    path('RealizarPago/',general.realizar_pago , name='pago'),
    path('misalquileres/',general.misalquileres),
    path('cancelar_alquiler/<int:alquiler_id>/', general.cancelar_alquiler, name='cancelar_alquiler'),
    
    path('alquileres/<int:alquiler_id>/puntuar/', general.puntuar_alquiler, name='puntuar_alquiler'),
    path('observacion/<int:maquina_id>/agregar/', general.agregar_observacion, name='agregar_observacion'),

    path('proximamente/',general.proximo),
    path('estadisticas/', cliente_views.estadisticas_clientes, name='estadisticas_clientes'),
    path('localidades/', general.ver_localidades, name='ver_localidades'),
     path('localidades/agregar/', general.agregar_localidad, name='agregar_localidad'),
    path('localidades/eliminar/<int:localidad_id>/', general.eliminar_localidad, name='eliminar_localidad'),
    path('estadisticas_alquileres/', general.estadisticas_alquileres_localidad, name='estadisticas_alquileres_localidad'),
    path('agregar_empleado/',general.registro_empleado, name='registro_empleado'),
    path('empleados/', general.verEmpleados , name="verEmpleados"),
    path('empleados/cambiar_estado/<int:id>/', general.cambiar_estado_Empleado, name='cambiar_estado_Empleado'),
    path('estadisticas/alquileresPorMaquina/', maquinas_views.alquileres_por_maquina, name='alquileres_por_maquina'),
    path('estadisticas/ingresosMensuales/', general.estadisticas_ingresos_por_mes, name='estadisticasMensuales'),
    path('alquileres/', general.ver_alquileres, name='ver_alquileres'),
    path('alquileres/<int:alquiler_id>/aceptar_retiro/', general.aceptar_retiro, name='aceptar_retiro'),
    path('alquileres/<int:alquiler_id>/aceptar_devolucion/', general.aceptar_devolucion, name='aceptar_devolucion'),
    path('alquileres/<int:alquiler_id>/aceptar_devolucion_con_mora/', general.aceptar_devolucion_con_retraso, name='aceptar_devolucion_con_retraso'),
    path('historial_alquileres/', general.historial_alquileres, name='historial_alquileres'),
    path('maquinaria/<int:id>/agregar_observacion/', maquinas_views.agregar_observacion_maquinaria, name='agregar_observacion_maquinaria'),

    ]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=os.path.join(settings.BASE_DIR, 'static'))
