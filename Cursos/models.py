# cursos/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.core.exceptions import ValidationError
import logging
from Matriculas.models import Inscripcion

logger = logging.getLogger(__name__)

class Categoria(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='categorias/', blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = _("Categoría")
        verbose_name_plural = _("Categorías")


class Instructor(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_instructor')
    titulo = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    foto_url = models.URLField(max_length=1024, blank=True)
    promedio_calificacion = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    num_reseñas = models.PositiveIntegerField(default=0)
    num_estudiantes = models.PositiveIntegerField(default=0)
    especialidades = models.ManyToManyField(Categoria, related_name='instructores_especializados')
    redes_sociales = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Perfil de {self.usuario}"

    def actualizar_estadisticas(self):
        self.num_estudiantes = self.cursos_creados.aggregate(total=Count('inscritos', distinct=True))['total']
        self.promedio_calificacion = self.cursos_creados.aggregate(promedio=Avg('calificacion_promedio'))['promedio']
        self.num_reseñas = Reseña.objects.filter(curso__profesor=self).count()
        self.save()

    class Meta:
        verbose_name = _("Perfil de Instructor")
        verbose_name_plural = _("Perfiles de Instructores")


class Curso(models.Model):
    class DificultadChoices(models.TextChoices):
        PRINCIPIANTE = 'Principiante', _('Principiante')
        INTERMEDIO = 'Intermedio', _('Intermedio')
        AVANZADO = 'Avanzado', _('Avanzado')

    class ModalidadChoices(models.TextChoices):
        SINCRONICO = 'Sincrónico', _('Sincrónico')
        ASINCRONICO = 'Asincrónico', _('Asincrónico')
        HIBRIDO = 'Híbrido', _('Híbrido')

    titulo = models.CharField(max_length=255, verbose_name=_("Título"))
    slug = models.SlugField(max_length=255, unique=True, help_text=_("Versión amigable del título para URL."))
    descripcion = models.TextField(verbose_name=_("Descripción detallada del curso"))
    descripcion_corta = models.CharField(max_length=1000, verbose_name=_("Descripción corta"))
    lo_que_aprenderas = models.TextField(blank=True, verbose_name=_("Lo que aprenderás"))
    video_introductorio = models.URLField(max_length=1024, blank=True)
    materiales_incluidos = models.TextField(_("Materiales incluidos"))
    audiencia = models.TextField(blank=True, verbose_name=_("Audiencia objetivo"))
    modalidad = models.CharField(max_length=20, choices=ModalidadChoices.choices)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)
    imagen_principal_url = models.URLField(max_length=1024, blank=True)
    tags = models.ManyToManyField("Tag", related_name='cursos', blank=True)
    dificultad = models.CharField(max_length=12, choices=DificultadChoices.choices)
    prerrequisitos = models.TextField(blank=True, verbose_name=_("Prerrequisitos"))
    profesor = models.ForeignKey('Instructor', on_delete=models.CASCADE, related_name='cursos_creados')
    categoria = models.ForeignKey('Categoria', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Categoría"), related_name='cursos')
    es_activo = models.BooleanField(default=True)
    es_destacado = models.BooleanField(default=False)
    es_premium = models.BooleanField(default=False)
    precio = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    calificacion_promedio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    progreso_promedio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    tasa_finalizacion = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    inscritos = models.ManyToManyField(User, related_name='cursos_inscritos', blank=True)
    portada_curso = models.ImageField(upload_to='portadas_cursos/', blank=True)
    requisitos_tecnicos = models.TextField(blank=True, verbose_name=_("Requisitos técnicos"))
    fecha_actualizacion = models.DateField(auto_now=True)
    duracion_total = models.PositiveIntegerField(help_text=_("Duración total en minutos"), default=0)
    nivel_satisfaccion = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    certificado_disponible = models.BooleanField(default=False)
    idiomas_disponibles = models.JSONField(default=list, blank=True)

    def clean(self):
        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio > self.fecha_fin:
            raise ValidationError(_("La fecha de inicio debe ser anterior a la fecha de fin."))

    def calcular_promedio_calificaciones(self):
        promedio = self.inscritos.aggregate(promedio_calificaciones=Avg('calificacion_final'))['promedio_calificaciones']
        return round(promedio, 2) if promedio else None

    def calcular_progreso_promedio(self):
        inscritos_total = self.inscritos.count()
        if inscritos_total == 0:
            return 0
        promedio = self.progresos.aggregate(progreso_promedio=Avg('porcentaje'))['progreso_promedio']
        return round(promedio, 2) if promedio else 0
        
        total_progreso = 0
        for usuario in self.inscritos.all():
            total_progreso += self.calcular_progreso(usuario)
        
        return round(total_progreso / total_usuarios, 2) if total_usuarios > 0 else 0

    def calcular_tasa_finalizacion(self):
        inscritos_total = self.inscritos.count()
        if inscritos_total == 0:
            return 0
        inscritos_finalizados = self.progresos.filter(porcentaje=100).count()
        tasa_finalizacion = (inscritos_finalizados / inscritos_total) * 100
        return round(tasa_finalizacion, 2)

    def calcular_progreso(self, usuario):
        progreso = self.progresos.filter(usuario=usuario).first()
        return progreso.porcentaje if progreso else 0
    
    def esta_inscrito(self, usuario):
        inscrito = Inscripcion.objects.filter(usuario=usuario, curso=self).exists()
        logger.info(f"Verificando si el usuario {usuario.id} está inscrito en el curso {self.id}: {inscrito}")
        return inscrito
    


    def actualizar_duracion_total(self):
        self.duracion_total = sum(tema.tiempo_estimado for tema in self.temas.all())
        self.save()

    def calcular_nivel_satisfaccion(self):
        reseñas = self.reseñas.all()
        if reseñas:
            self.nivel_satisfaccion = reseñas.aggregate(promedio=Avg('calificacion'))['promedio']
            self.save()

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = _("Curso")
        verbose_name_plural = _("Cursos")


class Tema(models.Model):
    curso = models.ForeignKey(Curso, related_name='temas', on_delete=models.CASCADE)
    titulo = models.CharField(max_length=255)
    nombre = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, help_text=_("Versión amigable del título para URL."))
    contenido = models.TextField()
    orden = models.PositiveIntegerField()
    tiempo_estimado = models.PositiveIntegerField(help_text=_("Tiempo estimado en minutos"))
    microlearning = models.BooleanField(default=False, help_text=_("Indica si el tema es parte de una estrategia de microaprendizaje"))
    contribuyentes = models.ManyToManyField(User, related_name='temas_contribuidos', blank=True)
    # evaluacion_asociada = models.OneToOneField('Evaluaciones.Evaluacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='leccion_evaluacion')
    evaluacion_asociada = models.OneToOneField(
        'Evaluaciones.Evaluacion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tema_asociado'  # Cambio aquí para evitar conflictos
    )
    recursos_adicionales = models.JSONField(default=list, blank=True)
    objetivos_aprendizaje = models.TextField(blank=True)


    def calcular_progreso(self, usuario):
        lecciones = self.lecciones.all()
        lecciones_completadas = lecciones.filter(completada_por=usuario).count()
        progreso = (lecciones_completadas / lecciones.count()) * 100 if lecciones else 0
        return round(progreso, 2)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = _("Tema")
        verbose_name_plural = _("Temas")
        unique_together = ('titulo', 'slug')

class Reseña(models.Model):
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='reseñas')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reseñas')
    calificacion = models.PositiveIntegerField()
    comentario = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    utilidad = models.PositiveIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.curso.calcular_promedio_calificaciones()
        self.curso.calcular_nivel_satisfaccion()
        self.curso.profesor.actualizar_estadisticas()

    def __str__(self):
        return f"Reseña de {self.usuario} para {self.curso}"

    class Meta:
        verbose_name = _("Reseña")
        verbose_name_plural = _("Reseñas")
        unique_together = ('curso', 'usuario')
        ordering = ['-fecha_creacion']


class Tag(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")


class TemaCompletado(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='temas_completados')
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE, related_name='usuarios_completados')
    fecha_completado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario} ha completado {self.tema}"

    class Meta:
        verbose_name = _("Tema Completado")
        verbose_name_plural = _("Temas Completados")
        unique_together = ('usuario', 'tema')
        ordering = ['-fecha_completado']



class Progreso(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='curso_progresos')
    curso = models.ForeignKey('Curso', on_delete=models.CASCADE, related_name='progresos')
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('usuario', 'curso')
        verbose_name = _("Progreso")
        verbose_name_plural = _("Progresos")

    def __str__(self):
        return f"{self.usuario.username} - {self.curso.titulo} - {self.porcentaje}%"