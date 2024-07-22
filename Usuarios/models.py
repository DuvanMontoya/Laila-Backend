# Usuarios/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from Cursos.models import Curso
# from Matriculas.models import Inscripcion


class Perfil(models.Model):
    GENDER_CHOICES = [
        ('masculino', 'Masculino'),
        ('femenino', 'Femenino'),
        ('otro', 'Otro'),
    ]
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    biografia = models.TextField(blank=True)
    avatar_url = models.URLField(max_length=1024, blank=True)
    cursos_inscritos = models.ManyToManyField(Curso, through='Matriculas.Inscripcion', related_name="perfiles_inscritos")
    nombre = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z\s]*$',
                message='El nombre solo debe contener letras y espacios.'
            ),
        ]
    )
    apellido = models.CharField(max_length=255, blank=True)
    profesion = models.CharField(max_length=255, blank=True, default="Estudiante")
    edad = models.PositiveIntegerField(blank=True, null=True)
    genero = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    pais = models.CharField(max_length=255, blank=True)
    ciudad = models.CharField(max_length=255, blank=True)
    whatsapp = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?[0-9]{9,15}$',
                message=_("Número de teléfono debe estar en el formato: '+999999999'. Hasta 15 dígitos permitidos.")
            )
        ]
    )
    correo = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    avatar = models.URLField(max_length=1024, blank=True, null=True)
    biografia = models.TextField(blank=True, null=True, help_text="Una breve biografía sobre ti.", max_length=5000)
    twitter = models.URLField(max_length=1024, blank=True, null=True)
    linkedin = models.URLField(max_length=1024, blank=True, null=True)
    github = models.URLField(max_length=1024, blank=True, null=True)
    website = models.URLField(max_length=1024, blank=True, null=True, help_text="Tu sitio web personal o portafolio.")
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    universidad = models.ForeignKey('Articulos.Universidad', on_delete=models.SET_NULL, null=True, blank=True, related_name="perfiles")

    def __str__(self):
        return f'Perfil de {self.usuario.username}'

    class Meta:
        verbose_name = _("Perfil")
        verbose_name_plural = _("Perfiles")




