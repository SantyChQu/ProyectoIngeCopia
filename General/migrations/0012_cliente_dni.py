# Generated by Django 5.2.1 on 2025-06-03 11:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('General', '0011_remove_cliente_dni'),
    ]

    operations = [
        migrations.AddField(
            model_name='cliente',
            name='dni',
            field=models.CharField(default=1, max_length=20, unique=True),
            preserve_default=False,
        ),
    ]
