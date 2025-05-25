from django.db import models

class Cliente(models.Model):

  nombre = models.CharField(max_length=200)
  apellido = models.CharField(max_length=200)
  edad = models.IntegerField()
  telefono = models.IntegerField()
  mail = models.EmailField() 
  contraseña = models.CharField(max_length=20)
  estado = models.BooleanField(default=True)

  def __str__(self):
    return f"{self.nombre} {self.apellido} {self.mail}"
