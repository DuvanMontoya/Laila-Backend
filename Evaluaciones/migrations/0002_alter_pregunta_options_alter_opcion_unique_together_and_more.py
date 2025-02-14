# Generated by Django 5.0.6 on 2024-06-17 04:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Evaluaciones', '0001_initial'),
        ('Lecciones', '0003_leccioncompletada'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pregunta',
            options={'verbose_name': 'Pregunta', 'verbose_name_plural': 'Preguntas'},
        ),
        migrations.AlterUniqueTogether(
            name='opcion',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='evaluacion',
            name='banco_de_preguntas',
        ),
        migrations.RemoveField(
            model_name='evaluacion',
            name='competencias_evaluadas',
        ),
        migrations.RemoveField(
            model_name='pregunta',
            name='audio_relacionado_url',
        ),
        migrations.RemoveField(
            model_name='pregunta',
            name='comentarios',
        ),
        migrations.RemoveField(
            model_name='pregunta',
            name='condicionales',
        ),
        migrations.RemoveField(
            model_name='pregunta',
            name='evaluacion',
        ),
        migrations.RemoveField(
            model_name='pregunta',
            name='imagen_relacionada_url',
        ),
        migrations.RemoveField(
            model_name='pregunta',
            name='video_relacionado_url',
        ),
        migrations.AddField(
            model_name='evaluacion',
            name='leccion_evaluacion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Lecciones.leccion'),
        ),
        migrations.AddField(
            model_name='evaluacion',
            name='mostrar_opciones_correctas',
            field=models.BooleanField(default=False, help_text='Permite mostrar u ocultar las opciones correctas a los estudiantes'),
        ),
        migrations.AddField(
            model_name='evaluacion',
            name='mostrar_resultados',
            field=models.BooleanField(default=False, help_text='Permite mostrar u ocultar los resultados a los estudiantes'),
        ),
        migrations.AddField(
            model_name='evaluacion',
            name='resultados_visibles',
            field=models.BooleanField(default=False, help_text='Permite mostrar u ocultar los resultados a los estudiantes'),
        ),
        migrations.AddField(
            model_name='opcion',
            name='puntos',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Puntos ganados si esta opción es seleccionada correctamente', max_digits=5),
        ),
        migrations.AddField(
            model_name='pregunta',
            name='opciones',
            field=models.ManyToManyField(blank=True, related_name='preguntas', to='Evaluaciones.opcion'),
        ),
        migrations.AlterField(
            model_name='evaluacion',
            name='intentos_permitidos',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.CreateModel(
            name='IntentoEvaluacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_intento', models.DateTimeField(auto_now_add=True)),
                ('puntaje_obtenido', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('completado', models.BooleanField(default=False)),
                ('evaluacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='intentos', to='Evaluaciones.evaluacion')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='intentos', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Intento de Evaluación',
                'verbose_name_plural': 'Intentos de Evaluaciones',
            },
        ),
        migrations.CreateModel(
            name='ResultadoEvaluacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puntaje_total', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('fecha_resultado', models.DateTimeField(auto_now_add=True)),
                ('evaluacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resultados', to='Evaluaciones.evaluacion')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resultados', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Resultado de Evaluación',
                'verbose_name_plural': 'Resultados de Evaluaciones',
            },
        ),
        migrations.RemoveField(
            model_name='opcion',
            name='pregunta',
        ),
        migrations.RemoveField(
            model_name='opcion',
            name='puntos_obtenidos',
        ),
    ]
