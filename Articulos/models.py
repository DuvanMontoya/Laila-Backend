from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.text import slugify
from django.conf import settings
from Usuarios.models import Perfil


class Universidad(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)
    logo_url = models.URLField(max_length=1024, blank=True)
    sitio_web = models.URLField(max_length=1024, blank=True)
    direccion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    correo_contacto = models.EmailField(blank=True)
    es_publica = models.BooleanField(default=False)
    fecha_fundacion = models.DateField(null=True, blank=True)
    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']



class Area(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']

class CategoriaArticulo(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True, null=True)
    area = models.ForeignKey(Area, related_name='categorias', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']

class TemaArticulo(models.Model):
    nombre = models.CharField(max_length=200)
    categoria = models.ForeignKey(CategoriaArticulo, related_name='temas', on_delete=models.CASCADE)
    descripcion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']

class Articulo(models.Model):
    titulo = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    area = models.ForeignKey('Area', related_name='articulos', on_delete=models.SET_NULL, null=True, blank=True)
    categoria_articulo = models.ForeignKey('CategoriaArticulo', related_name='articulos', on_delete=models.SET_NULL, null=True, blank=True)
    tema = models.ForeignKey('TemaArticulo', related_name='articulos', on_delete=models.SET_NULL, null=True, blank=True)
    autor = models.ForeignKey(Perfil, related_name='articulos', on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=[('articulo', 'Artículo'), ('investigacion', 'Investigación')])
    nivel = models.CharField(max_length=10, choices=[('basico', 'Básico'), ('avanzado', 'Avanzado')])
    acceso = models.CharField(max_length=12, choices=[('gratis', 'Gratis'), ('pago', 'Pago')])
    precio = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    publicado = models.BooleanField(default=False)
    contenido_html = models.TextField(blank=True, null=True)
    preview_html = models.TextField(blank=True, null=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    calificacion_promedio = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    num_vistas = models.PositiveIntegerField(default=0)
    num_favoritos = models.PositiveIntegerField(default=0)
    es_destacado = models.BooleanField(default=False)
    imagen_url = models.URLField(max_length=1024, blank=True, null=True)
    estudiantes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='articulos_matriculados', through='UsuarioArticulo')
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='articulos_liked', blank=True)
    portada_articulo = models.ImageField(upload_to='portadas_articulos/', blank=True, null=True)

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-creado']

class UsuarioArticulo(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='usuario_articulos', on_delete=models.CASCADE)
    articulo = models.ForeignKey(Articulo, related_name='usuario_articulos', on_delete=models.CASCADE)
    favorito = models.BooleanField(default=False)
    calificacion = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    like = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('usuario', 'articulo')

    def __str__(self):
        return f'{self.usuario.username} - {self.articulo.titulo}'

class Comentario(models.Model):
    articulo = models.ForeignKey('Articulo', related_name='comentarios', on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='comentarios', on_delete=models.CASCADE)
    contenido = models.TextField()
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-creado']

    def __str__(self):
        return f'Comentario por {self.usuario.username} en {self.articulo.titulo}'












class ArticuloView(models.Model):
    articulo = models.ForeignKey(Articulo, related_name='vistas', on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, related_name='vistas_articulos', on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f'{self.usuario.username} vio {self.articulo.titulo}'



class Like(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='likes_given')
    articulo = models.ForeignKey('Articulo', on_delete=models.CASCADE, related_name='likes_received')
    fecha = models.DateTimeField(default=timezone.now)
    class Meta:
        unique_together = ('user', 'articulo')

    def __str__(self):
        return f'{self.user.username} likes "{self.articulo.titulo}"'

    def clean(self):
        if Like.objects.filter(user=self.user, articulo=self.articulo).exists():
            raise ValidationError("El usuario ya ha dado 'like' a este artículo.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Tag(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)

    def __str__(self):
        return self.nombre

