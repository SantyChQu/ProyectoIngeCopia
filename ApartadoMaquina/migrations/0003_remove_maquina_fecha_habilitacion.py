# Generated by Django 5.2.2 on 2025-07-08 20:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ApartadoMaquina', '0002_maquina_fecha_habilitacion'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='maquina',
            name='fecha_habilitacion',
        ),
    ]
