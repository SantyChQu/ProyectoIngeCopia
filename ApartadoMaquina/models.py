from django.db import models

# Create your models here.
class Maquina(models.Model):
    numero_de_serie = models.CharField(max_length=100, unique=True)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    año_compra = models.PositiveIntegerField()
    localidad = models.CharField(max_length=100)
    imagen = models.ImageField(upload_to='maquinas/', null=True, blank=True)
    
    def __str__(self):
        return f"Marca:{self.marca} Modelo:{self.modelo} N° de Serie:({self.numero_de_serie})"