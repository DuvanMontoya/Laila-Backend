# Generated by Django 5.0.6 on 2024-06-17 04:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Evaluaciones', '0003_opcion_pregunta'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pregunta',
            name='opciones',
        ),
        migrations.AlterField(
            model_name='opcion',
            name='pregunta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='opciones', to='Evaluaciones.pregunta'),
        ),
    ]
