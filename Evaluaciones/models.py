from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils import timezone
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django_ckeditor_5.fields import CKEditor5Field

class Evaluacion(models.Model):
    class TipoEvaluacionChoices(models.TextChoices):
        LECCION = 'Lección', _('Lección')
        TEMA = 'Tema', _('Tema')
        CURSO = 'Curso', _('Curso')
        DIAGNOSTICA = 'Diagnóstica', _('Diagnóstica')
        LIBRE = 'Libre', _('Libre')

    titulo = models.CharField(max_length=255)
    tipo = models.CharField(max_length=11, choices=TipoEvaluacionChoices.choices, default=TipoEvaluacionChoices.LIBRE)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateTimeField(blank=True, null=True)
    fecha_fin = models.DateTimeField(blank=True, null=True)
    intentos_permitidos = models.PositiveIntegerField(default=1)
    ponderacion = models.DecimalField(max_digits=5, decimal_places=2)
    criterios_aprobacion = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    tiempo_limite = models.PositiveIntegerField(blank=True, null=True, help_text=_("Tiempo límite en minutos"))
    preguntas = models.ManyToManyField('Pregunta', related_name='evaluaciones', blank=True)
    resultados_visibles = models.BooleanField(default=False, help_text=_("Permite mostrar u ocultar los resultados a los estudiantes"))
    leccion_evaluacion = models.ForeignKey('Lecciones.Leccion', on_delete=models.SET_NULL, null=True, blank=True)
    tema_evaluacion = models.ForeignKey('Cursos.Tema', on_delete=models.SET_NULL, null=True, blank=True)
    curso_evaluacion = models.ForeignKey('Cursos.Curso', on_delete=models.SET_NULL, null=True, blank=True)
    mostrar_resultados = models.BooleanField(default=False, help_text=_("Permite mostrar u ocultar los resultados a los estudiantes"))
    mostrar_opciones_correctas = models.BooleanField(default=False, help_text=_("Permite mostrar u ocultar las opciones correctas a los estudiantes"))
    usuarios_permitidos = models.ManyToManyField(User, related_name='evaluaciones_permitidas', blank=True)
    puntaje_maximo = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    rubrica = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)
        if is_new:
            self.calcular_puntaje_maximo()

    def calcular_puntaje_maximo(self):
        if not hasattr(self, '_calculating_puntaje'):
            setattr(self, '_calculating_puntaje', True)
            puntaje_maximo = sum(pregunta.puntos for pregunta in self.preguntas.all())
            Evaluacion.objects.filter(pk=self.pk).update(puntaje_maximo=puntaje_maximo)
            delattr(self, '_calculating_puntaje')

    def clean(self):
        super().clean()
        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio > self.fecha_fin:
            raise ValidationError(_("La fecha de inicio debe ser anterior a la fecha de fin."))
        if self.tipo == self.TipoEvaluacionChoices.LECCION and not self.leccion_evaluacion:
            raise ValidationError(_("Debe seleccionar una lección para este tipo de evaluación."))

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = _("Evaluación")
        verbose_name_plural = _("Evaluaciones")

@receiver(pre_save, sender=Evaluacion)
def ensure_evaluacion_id(sender, instance, **kwargs):
    if not instance.pk and not hasattr(instance, '_saving'):
        setattr(instance, '_saving', True)
        instance.save()
        delattr(instance, '_saving')

class Pregunta(models.Model):
    class DificultadChoices(models.TextChoices):
        FACIL = 'Fácil', _('Fácil')
        MODERADO = 'Moderado', _('Moderado')
        DIFICIL = 'Difícil', _('Difícil')

    class TipoPreguntaChoices(models.TextChoices):
        SIMPLE = 'Simple', _('Simple')
        MULTIPLE = 'Múltiple', _('Múltiple')
        ABIERTA = 'Abierta', _('Abierta')
        VERDADERO_FALSO = 'Verdadero/Falso', _('Verdadero/Falso')

    texto_pregunta = CKEditor5Field(blank=True, config_name='default')
    tipo_pregunta = models.CharField(max_length=15, choices=TipoPreguntaChoices.choices, default=TipoPreguntaChoices.SIMPLE)
    dificultad = models.CharField(max_length=12, choices=DificultadChoices.choices)
    puntos = models.DecimalField(max_digits=5, decimal_places=2)
    tiempo_estimado = models.PositiveIntegerField(null=True, blank=True)
    categoria = models.CharField(max_length=50, blank=True)
    imagen_svg = CKEditor5Field(blank=True, config_name='default')
    marcar_respuesta = models.BooleanField(default=False)
    explicacion_respuesta = models.TextField(blank=True)
    tags = models.ManyToManyField("Tag", related_name='preguntas', blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    activa = models.BooleanField(default=True)
    comentarios = models.TextField(blank=True)

    def __str__(self):
        return self.texto_pregunta

    def clean(self):
        super().clean()
        if self.pk:
            if self.tipo_pregunta in [self.TipoPreguntaChoices.SIMPLE, self.TipoPreguntaChoices.MULTIPLE, self.TipoPreguntaChoices.VERDADERO_FALSO]:
                if not self.opciones.exists():
                    raise ValidationError(_("Debe proporcionar al menos una opción para preguntas de tipo simple, múltiple o verdadero/falso."))

    class Meta:
        verbose_name = _("Pregunta")
        verbose_name_plural = _("Preguntas")

class Opcion(models.Model):
    pregunta = models.ForeignKey(Pregunta, related_name='opciones', on_delete=models.CASCADE)
    texto_opcion = models.TextField()
    es_correcta = models.BooleanField(default=False)
    puntos = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text=_("Puntos ganados si esta opción es seleccionada correctamente"))

    def __str__(self):
        return self.texto_opcion

    def clean(self):
        super().clean()
        if self.es_correcta and self.puntos <= 0:
            raise ValidationError(_("Una opción correcta debe tener puntos positivos."))

    class Meta:
        verbose_name = _("Opción")
        verbose_name_plural = _("Opciones")

class IntentoEvaluacion(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name='intento_evaluacion')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='intento_evaluacion')
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    hora_inicio = models.DateTimeField(default=timezone.now)
    hora_fin = models.DateTimeField(null=True, blank=True)
    puntaje_obtenido = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    respuestas = models.JSONField(default=dict)
    completado = models.BooleanField(default=False)

    def __str__(self):
        return f"Intento de {self.usuario} en {self.evaluacion}"
    
    @property
    def porcentaje_puntaje(self):
        if self.evaluacion.puntaje_maximo:
            return (self.puntaje_obtenido / self.evaluacion.puntaje_maximo) * 100
        return 0
    
    @property
    def aprobacion(self):
        if self.evaluacion.criterios_aprobacion:
            return self.porcentaje_puntaje >= self.evaluacion.criterios_aprobacion
        return False
    
    @property
    def tiempo_restante(self):
        if not self.evaluacion.tiempo_limite:
            return None
        tiempo_transcurrido = (timezone.now() - self.fecha_inicio).total_seconds()
        tiempo_limite_segundos = self.evaluacion.tiempo_limite * 60
        return max(0, tiempo_limite_segundos - tiempo_transcurrido)
    
    @property
    def tiempo_tomado(self):
        if self.fecha_fin and self.fecha_inicio:
            return (self.fecha_fin - self.fecha_inicio).total_seconds()
        return None
    
    class Meta:
        verbose_name = _("Intento de Evaluación")
        verbose_name_plural = _("Intentos de Evaluaciones")

class RespuestaPregunta(models.Model):
    intento = models.ForeignKey('IntentoEvaluacion', on_delete=models.CASCADE, related_name='respuesta_pregunta')
    pregunta = models.ForeignKey('Pregunta', on_delete=models.CASCADE)
    respuesta = models.TextField()
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='respuestas')
    es_correcta = models.BooleanField(default=False)
    puntos_obtenidos = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fecha_respuesta = models.DateTimeField(auto_now_add=True)
    opcion_seleccionada = models.ForeignKey('Opcion', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Respuesta a {self.pregunta} por {self.usuario} en intento {self.intento}"
    
    def clean(self):
        super().clean()
        if self.pregunta.tipo_pregunta == Pregunta.TipoPreguntaChoices.SIMPLE:
            opcion_seleccionada = self.respuesta.get('opcion_seleccionada')
            if opcion_seleccionada:
                opcion = Opcion.objects.get(id=opcion_seleccionada)
                self.es_correcta = opcion.es_correcta
                self.puntos_obtenidos = opcion.puntos if opcion.es_correcta else 0
            else:
                raise ValidationError(_("Debe seleccionar una opción para preguntas simples."))
        elif self.pregunta.tipo_pregunta == Pregunta.TipoPreguntaChoices.MULTIPLE:
            opciones_seleccionadas = self.respuesta.get('opciones_seleccionadas', [])
            if opciones_seleccionadas:
                opciones = Opcion.objects.filter(id__in=opciones_seleccionadas)
                self.es_correcta = all(opcion.es_correcta for opcion in opciones)
                self.puntos_obtenidos = sum(opcion.puntos for opcion in opciones if opcion.es_correcta)
            else:
                raise ValidationError(_("Debe seleccionar al menos una opción para preguntas de opción múltiple."))
        elif self.pregunta.tipo_pregunta == Pregunta.TipoPreguntaChoices.VERDADERO_FALSO:
            respuesta_seleccionada = self.respuesta.get('respuesta_seleccionada')
            if respuesta_seleccionada is not None:
                opcion = Opcion.objects.get(pregunta=self.pregunta, es_correcta=respuesta_seleccionada)
                self.es_correcta = opcion.es_correcta
                self.puntos_obtenidos = opcion.puntos if opcion.es_correcta else 0
            else:
                raise ValidationError(_("Debe seleccionar una respuesta para preguntas de verdadero/falso."))
        elif self.pregunta.tipo_pregunta == Pregunta.TipoPreguntaChoices.ABIERTA:
            respuesta_texto = self.respuesta.get('respuesta_texto')
            if respuesta_texto:
                # Aquí podrías implementar algún tipo de validación o asignación de puntaje para preguntas abiertas
                pass
            else:
                raise ValidationError(_("Debe ingresar una respuesta para preguntas abiertas."))
    
    class Meta:
        verbose_name = _("Respuesta a Pregunta")
        verbose_name_plural = _("Respuestas a Preguntas")
        unique_together = ('pregunta', 'usuario', 'intento')

class Tag(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

class ResultadoEvaluacion(models.Model):
    evaluacion = models.ForeignKey(Evaluacion, on_delete=models.CASCADE, related_name='resultados')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resultados')
    puntaje_total = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    fecha_resultado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resultado de {self.usuario} en {self.evaluacion}"

    class Meta:
        verbose_name = _("Resultado de Evaluación")
        verbose_name_plural = _("Resultados de Evaluaciones")
