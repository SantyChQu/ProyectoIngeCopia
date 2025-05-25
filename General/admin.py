
from .models import Cliente

from .models import Politica
from django.contrib import admin

from .models import Jefe
from .models import Empleado
from .models import Localidad

from .models import Maquinaria
from .models import Mantenimiento
from .models import Observacion
from .models import Calificacion
from .models import Alquiler
from .models import Tarjeta

# Register your models here.

admin.site.register(Cliente)
admin.site.register(Jefe)
admin.site.register(Empleado)
admin.site.register(Localidad)
admin.site.register(Politica)
admin.site.register(Maquinaria)
admin.site.register(Mantenimiento)
admin.site.register(Observacion)
admin.site.register(Calificacion)
admin.site.register(Alquiler)
admin.site.register(Tarjeta)