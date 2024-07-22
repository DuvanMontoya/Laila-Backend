from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime




class Leccion(models.Model):
    class EstadoChoices(models.TextChoices):
        BORRADOR = 'Borrador', _('Borrador')
        PUBLICADA = 'Publicada', _('Publicada')
        ARCHIVADA = 'Archivada', _('Archivada')

    titulo = models.CharField(max_length=255)
    nombre = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, help_text=_("Versión amigable del título para URL."))
    estado = models.CharField(max_length=10, choices=EstadoChoices.choices, default=EstadoChoices.BORRADOR)
    tiempo_estimado = models.PositiveIntegerField(help_text=_("Tiempo estimado en minutos"))
    tiene_material = models.BooleanField(default=False)
    es_demo = models.BooleanField(default=False)
    tipo_leccion = models.CharField(max_length=9, choices=[('Video', _('Video')), ('Texto', _('Texto')), ('Seminario', _('Seminario'))], default='Video')
    contenido_texto = models.TextField(blank=True)
    contenido_multimedia = models.URLField(max_length=1024, blank=True)
    orden = models.PositiveIntegerField()
    prerrequisitos = models.ManyToManyField('self', symmetrical=False, related_name='lecciones_siguientes', blank=True)
    # tema = models.ForeignKey('Tema', on_delete=models.CASCADE, related_name='lecciones')
    tema = models.ForeignKey('Cursos.Tema', on_delete=models.CASCADE, related_name='lecciones')

    calificacion = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Calificación de la lección del 1 al 10")
    # evaluacion_asociada = models.OneToOneField('Evaluaciones.Evaluacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='leccion_evaluacion')
    evaluacion_asociada = models.OneToOneField(
        'Evaluaciones.Evaluacion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leccion_asociada'  # Cambio aquí para evitar conflictos
    )
    progreso_por_usuario = models.JSONField(default=dict)
    eventos = models.JSONField(default=list)
    feedbacks = models.JSONField(default=list)
    completada_por = models.ManyToManyField(User, related_name='lecciones_completadas', blank=True)

    owner = models.ForeignKey(User, related_name='lecciones', on_delete=models.CASCADE)

    def clean(self):
        super().clean()
        if self.calificacion and not (1 <= self.calificacion <= 10):
            raise ValidationError("La calificación debe estar entre 1 y 10.")


    def ha_sido_comprendida(self):
        comprendida = self.calificacion and self.calificacion >= 7
        if self.evaluacion_asociada:
            comprendida = comprendida and self.evaluacion_asociada.calcular_calificacion_ponderada() >= 70
        return comprendida

    def calcular_progreso(self, usuario_id):
        return self.progreso_por_usuario.get(str(usuario_id), 0)

    def registrar_evento(self, tipo, usuario_id):
        self.eventos.append({'tipo': tipo, 'usuario_id': usuario_id, 'timestamp': datetime.now()})
        self.save()

    def agregar_feedback(self, usuario_id, comentario, calificacion):
        self.feedbacks.append({'usuario_id': usuario_id, 'comentario': comentario, 'calificacion': calificacion, 'timestamp': datetime.now()})
        self.save()

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = _("Lección")
        verbose_name_plural = _("Lecciones")
        unique_together = ('titulo', 'slug')



class Progreso(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progresos')
    leccion = models.ForeignKey(Leccion, on_delete=models.CASCADE, related_name='progresos')
    completado = models.BooleanField(default=False)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return f"Progreso de {self.usuario} en {self.leccion}"

    class Meta:
        verbose_name = _("Progreso")
        verbose_name_plural = _("Progresos")
        unique_together = ('usuario', 'leccion')



class LeccionPendiente(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    leccion = models.ForeignKey('Lecciones.Leccion', on_delete=models.CASCADE)
    fecha_asignada = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'leccion')


class LeccionCompletada(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    leccion = models.ForeignKey('Leccion', on_delete=models.CASCADE)
    fecha_completado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'leccion')

