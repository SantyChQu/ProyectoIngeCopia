from django.db import models
from datetime import date
# Create your models here.

# dios sabra si estan bien creados



class Cliente(models.Model):
    ESTADO_CHOICES = [
        ('habilitado', 'Habilitado'),
        ('inhabilitado', 'Inhabilitado'),
    ]               

    ROL_CHOICES = [
         ('cliente', 'Cliente'),
         ('jefe', 'Jefe'),
         ('empleados', 'Empleados'),
    ]

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    dni = models.CharField(max_length=20, unique=True)
    #edad = models.PositiveIntegerField()
    telefono = models.CharField(max_length=20)
    mail = models.EmailField(unique=True)
    contraseña = models.CharField(max_length=128)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='habilitado')
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='cliente')
   
  # clave= models.CharField(max_length=20)

    @property
    def edad(self):
        hoy = date.today()
        return hoy.year - self.fecha_nacimiento.year - ((hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day))

    def __str__(self):
       return f"{self.nombre} {self.apellido} {self.mail} {self.fecha_nacimiento} {self.telefono} {self.estado} {self.rol} "


class Jefe(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    mail = models.EmailField(unique=True)
    contraseña = models.CharField(max_length=128)



class Empleado(models.Model):
    ESTADO_CHOICES = [
        ('habilitado', 'Habilitado'),
        ('inhabilitado', 'Inhabilitado'),
    ]

    dni = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    mail = models.EmailField(unique=True)
    contraseña = models.CharField(max_length=128)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='habilitado')


class Localidad(models.Model):
    nombre = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=10)
    ubicacion = models.TextField()

    def __str__(self):
        return self.nombre


class Politica(models.Model):
    nombre = models.CharField(max_length=100)
    porcentaje = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.nombre


class Maquinaria(models.Model):
    ESTADO_CHOICES = [
        ('habilitado', 'Habilitado'),
        ('inhabilitado', 'Inhabilitado'),
    ]

    codigo_serie = models.CharField(max_length=50, unique=True)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    año_compra = models.PositiveIntegerField()
    localidad = models.ForeignKey(Localidad, on_delete=models.CASCADE, null=True, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='habilitado')
    precio_alquiler_diario = models.DecimalField(max_digits=30, decimal_places=2)
    politica = models.ForeignKey(Politica, on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to='maquinas/')


class Mantenimiento(models.Model):
    maquinaria = models.ForeignKey(Maquinaria, on_delete=models.CASCADE)
    fecha = models.DateField()


class Observacion(models.Model):
    observacion = models.TextField()
    mail = models.EmailField(null=True, blank=True)
    codigo_maquina = models.ForeignKey(Maquinaria, null=True, blank=True, on_delete=models.SET_NULL)
    fecha = models.DateField()

class Calificacion(models.Model):
    codigo_calif = models.AutoField(primary_key=True)
    estrellas = models.PositiveSmallIntegerField() 
    nota = models.TextField(blank=True, null=True)

class Tarjeta(models.Model):
    numero_tarjeta = models.CharField(max_length=16)
    numero_seguridad = models.CharField(max_length=4)
    nombre_propietario = models.CharField(max_length=100)
    fecha_desde = models.DateField()
    fecha_hasta = models.DateField()
    monto = models.DecimalField(max_digits=100, decimal_places=2)

   

class Alquiler(models.Model):
    ESTADO_CHOICES = [
        ('pendienteRetiro', 'Pendiente de retiro'),
        ('enCurso', 'En curso'),
        ('finalizado', 'Finalizado'),
    ]

    codigo_identificador = models.CharField(max_length=50, unique=True)
    codigo_maquina = models.ForeignKey(Maquinaria, on_delete=models.CASCADE)
    mail = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendienteRetiro')
    desde = models.DateField()
    hasta = models.DateField()
    calificacion = models.ForeignKey(Calificacion, on_delete=models.SET_NULL, null=True, blank=True)
    tarjeta = models.ForeignKey(Tarjeta, on_delete=models.SET_NULL, null=True, blank=True)
    precio = models.DecimalField(max_digits=100, decimal_places=2, default=0)


