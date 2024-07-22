from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from Lecciones.models import Leccion





class Tarea(models.Model):
    class EstadoChoices(models.TextChoices):
        PENDIENTE = 'Pendiente', _('Pendiente')
        EN_PROGRESO = 'En Progreso', _('En Progreso')
        COMPLETADA = 'Completada', _('Completada')
        APROBADA = 'Aprobada', _('Aprobada')
        RECHAZADA = 'Rechazada', _('Rechazada')

    titulo = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, help_text=_("Versión amigable del título para URL."))
    descripcion = models.TextField()
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateTimeField()
    peso_en_calificacion_final = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    revisiones_permitidas = models.PositiveIntegerField()
    peso_tareas_colaborativas = models.BooleanField(default=False)
    es_opcional = models.BooleanField(default=False)
    estado = models.CharField(max_length=12, choices=EstadoChoices.choices, default=EstadoChoices.PENDIENTE)
    calificacion = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    evaluacion_asociada = models.OneToOneField('Evaluacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='tarea_evaluacion')
    leccion = models.ForeignKey(Leccion, on_delete=models.CASCADE, related_name='tareas')
    entregas = models.ManyToManyField(User, through='EntregaTarea', related_name='tareas_entregadas')
    evaluacion_asociada = models.ForeignKey('Evaluaciones.Evaluacion', on_delete=models.CASCADE, related_name='tareas')


    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = _("Tarea")
        verbose_name_plural = _("Tareas")

class EntregaTarea(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name='entregas_tarea')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entregas_usuario')
    fecha_entrega = models.DateTimeField(auto_now_add=True)
    archivo = models.FileField(upload_to='entregas/')

    def __str__(self):
        return f"Entrega {self.id} de {self.usuario.username}"
