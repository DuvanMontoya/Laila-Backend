# Generated by Django 5.0.6 on 2024-06-06 16:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255, unique=True)),
                ('descripcion', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Categoría',
                'verbose_name_plural': 'Categorías',
            },
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tags',
            },
        ),
        migrations.CreateModel(
            name='Instructor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(blank=True, max_length=255)),
                ('bio', models.TextField(blank=True)),
                ('foto_url', models.URLField(blank=True, max_length=1024)),
                ('promedio_calificacion', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('num_reseñas', models.PositiveIntegerField(default=0)),
                ('num_estudiantes', models.PositiveIntegerField(default=0)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil_instructor', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Perfil de Instructor',
                'verbose_name_plural': 'Perfiles de Instructores',
            },
        ),
        migrations.CreateModel(
            name='Curso',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=255, verbose_name='Título')),
                ('slug', models.SlugField(help_text='Versión amigable del título para URL.', max_length=255, unique=True)),
                ('descripcion', models.TextField(verbose_name='Descripción detallada del curso')),
                ('descripcion_corta', models.CharField(max_length=1000, verbose_name='Descripción corta')),
                ('lo_que_aprenderas', models.TextField(blank=True, verbose_name='Lo que aprenderás')),
                ('video_introductorio', models.URLField(blank=True, max_length=1024)),
                ('materiales_incluidos', models.TextField(verbose_name='Materiales incluidos')),
                ('audiencia', models.TextField(blank=True, verbose_name='Audiencia objetivo')),
                ('modalidad', models.CharField(choices=[('Sincrónico', 'Sincrónico'), ('Asincrónico', 'Asincrónico'), ('Híbrido', 'Híbrido')], max_length=20)),
                ('fecha_inicio', models.DateField()),
                ('fecha_fin', models.DateField(blank=True, null=True)),
                ('imagen_principal_url', models.URLField(blank=True, max_length=1024)),
                ('dificultad', models.CharField(choices=[('Principiante', 'Principiante'), ('Intermedio', 'Intermedio'), ('Avanzado', 'Avanzado')], max_length=12)),
                ('prerrequisitos', models.TextField(blank=True, verbose_name='Prerrequisitos')),
                ('es_activo', models.BooleanField(default=True)),
                ('es_destacado', models.BooleanField(default=False)),
                ('es_premium', models.BooleanField(default=False)),
                ('precio', models.DecimalField(decimal_places=2, default=0, max_digits=8)),
                ('calificacion_promedio', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('progreso_promedio', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('tasa_finalizacion', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('categoria', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cursos', to='Cursos.categoria', verbose_name='Categoría')),
                ('inscritos', models.ManyToManyField(blank=True, related_name='cursos_inscritos', to=settings.AUTH_USER_MODEL)),
                ('profesor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cursos_creados', to='Cursos.instructor')),
                ('tags', models.ManyToManyField(blank=True, related_name='cursos', to='Cursos.tag')),
            ],
            options={
                'verbose_name': 'Curso',
                'verbose_name_plural': 'Cursos',
            },
        ),
        migrations.CreateModel(
            name='Reseña',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('calificacion', models.PositiveIntegerField()),
                ('comentario', models.TextField(blank=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('curso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reseñas', to='Cursos.curso')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reseñas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Reseña',
                'verbose_name_plural': 'Reseñas',
                'ordering': ['-fecha_creacion'],
                'unique_together': {('curso', 'usuario')},
            },
        ),
        migrations.CreateModel(
            name='Tema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=255)),
                ('nombre', models.CharField(max_length=255)),
                ('slug', models.SlugField(help_text='Versión amigable del título para URL.', max_length=255, unique=True)),
                ('contenido', models.TextField()),
                ('orden', models.PositiveIntegerField()),
                ('tiempo_estimado', models.PositiveIntegerField(help_text='Tiempo estimado en minutos')),
                ('microlearning', models.BooleanField(default=False, help_text='Indica si el tema es parte de una estrategia de microaprendizaje')),
                ('contribuyentes', models.ManyToManyField(blank=True, related_name='temas_contribuidos', to=settings.AUTH_USER_MODEL)),
                ('curso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='temas', to='Cursos.curso')),
            ],
            options={
                'verbose_name': 'Tema',
                'verbose_name_plural': 'Temas',
                'unique_together': {('titulo', 'slug')},
            },
        ),
    ]
