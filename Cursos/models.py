from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
import logging
import Matriculas.models as Matriculas


logger = logging.getLogger(__name__)

class Categoria(models.Model):
    """
    Modelo para representar las categorías de los cursos.
    """
    nombre = models.CharField(max_length=255, unique=True, verbose_name=_("Nombre"))
    descripcion = models.TextField(blank=True, verbose_name=_("Descripción"))
    imagen = models.ImageField(upload_to='categorias/', blank=True, null=True, verbose_name=_("Imagen"))
    slug = models.SlugField(max_length=255, unique=True, editable=False, verbose_name=_("Slug"))

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para generar automáticamente el slug.
        """
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = _("Categoría")
        verbose_name_plural = _("Categorías")
        ordering = ['nombre']

class Instructor(models.Model):
    """
    Modelo para representar los perfiles de los instructores.
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_instructor', verbose_name=_("Usuario"))
    titulo = models.CharField(max_length=255, blank=True, verbose_name=_("Título"))
    bio = models.TextField(blank=True, verbose_name=_("Biografía"))
    foto_url = models.URLField(max_length=1024, blank=True, verbose_name=_("URL de la foto"))
    promedio_calificacion = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, verbose_name=_("Promedio de calificación"))
    num_reseñas = models.PositiveIntegerField(default=0, verbose_name=_("Número de reseñas"))
    num_estudiantes = models.PositiveIntegerField(default=0, verbose_name=_("Número de estudiantes"))
    especialidades = models.ManyToManyField(Categoria, related_name='instructores_especializados', verbose_name=_("Especialidades"))
    redes_sociales = models.JSONField(default=dict, blank=True, verbose_name=_("Redes sociales"))

    def __str__(self):
        return f"Perfil de {self.usuario.get_full_name() or self.usuario.username}"

    def actualizar_estadisticas(self):
        """
        Actualiza las estadísticas del instructor basándose en sus cursos y reseñas.
        """
        self.num_estudiantes = self.cursos_creados.aggregate(total=Count('inscritos', distinct=True))['total']
        self.promedio_calificacion = self.cursos_creados.aggregate(promedio=Avg('calificacion_promedio'))['promedio']
        self.num_reseñas = Reseña.objects.filter(curso__profesor=self).count()
        self.save()
        logger.info(f"Estadísticas actualizadas para el instructor {self.usuario.username}")

    def cursos_activos(self):
        """
        Retorna el número de cursos activos del instructor.
        """
        return self.cursos_creados.filter(es_activo=True).count()

    class Meta:
        verbose_name = _("Perfil de Instructor")
        verbose_name_plural = _("Perfiles de Instructores")

class Curso(models.Model):
    """
    Modelo principal para representar los cursos.
    """
    class DificultadChoices(models.TextChoices):
        PRINCIPIANTE = 'Principiante', _('Principiante')
        INTERMEDIO = 'Intermedio', _('Intermedio')
        AVANZADO = 'Avanzado', _('Avanzado')

    class ModalidadChoices(models.TextChoices):
        SINCRONICO = 'Sincrónico', _('Sincrónico')
        ASINCRONICO = 'Asincrónico', _('Asincrónico')
        HIBRIDO = 'Híbrido', _('Híbrido')

    titulo = models.CharField(max_length=255, verbose_name=_("Título"))
    slug = models.SlugField(max_length=255, unique=True, editable=False, verbose_name=_("Slug"))
    descripcion = models.TextField(verbose_name=_("Descripción detallada del curso"))
    descripcion_corta = models.CharField(max_length=1000, verbose_name=_("Descripción corta"))
    lo_que_aprenderas = models.TextField(blank=True, verbose_name=_("Lo que aprenderás"))
    video_introductorio = models.URLField(max_length=1024, blank=True, verbose_name=_("Video introductorio"))
    materiales_incluidos = models.TextField(verbose_name=_("Materiales incluidos"))
    audiencia = models.TextField(blank=True, verbose_name=_("Audiencia objetivo"))
    modalidad = models.CharField(max_length=20, choices=ModalidadChoices.choices, verbose_name=_("Modalidad"))
    fecha_inicio = models.DateField(verbose_name=_("Fecha de inicio"))
    fecha_fin = models.DateField(blank=True, null=True, verbose_name=_("Fecha de fin"))
    imagen_principal_url = models.URLField(max_length=1024, blank=True, verbose_name=_("URL de la imagen principal"))
    tags = models.ManyToManyField("Tag", related_name='curso', blank=True, verbose_name=_("Tags"))
    dificultad = models.CharField(max_length=12, choices=DificultadChoices.choices, verbose_name=_("Dificultad"))
    prerrequisitos = models.TextField(blank=True, verbose_name=_("Prerrequisitos"))
    profesor = models.ForeignKey(Instructor, on_delete=models.CASCADE, related_name='cursos_creados', verbose_name=_("Profesor"))
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Categoría"), related_name='cursos')
    es_activo = models.BooleanField(default=True, verbose_name=_("¿Está activo?"))
    es_destacado = models.BooleanField(default=False, verbose_name=_("¿Está destacado?"))
    es_premium = models.BooleanField(default=False, verbose_name=_("¿Es premium?"))
    precio = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name=_("Precio"))
    calificacion_promedio = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, verbose_name=_("Calificación promedio"))
    progreso_promedio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_("Progreso promedio"))
    tasa_finalizacion = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name=_("Tasa de finalización"))
    inscritos = models.ManyToManyField(User, through='Matriculas.Inscripcion', related_name='cursos_inscritos', verbose_name=_("Inscritos"))
    inscripciones = models.ManyToManyField('Matriculas.Inscripcion', related_name='inscripciones_curso')
    portada_curso = models.ImageField(upload_to='Matriculas.portadas_cursos/', blank=True, verbose_name=_("Portada del curso"))
    requisitos_tecnicos = models.TextField(blank=True, verbose_name=_("Requisitos técnicos"))
    fecha_actualizacion = models.DateField(auto_now=True, verbose_name=_("Fecha de actualización"))
    duracion_total = models.PositiveIntegerField(help_text=_("Duración total en minutos"), default=0, verbose_name=_("Duración total"))
    nivel_satisfaccion = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, verbose_name=_("Nivel de satisfacción"))
    certificado_disponible = models.BooleanField(default=False, verbose_name=_("¿Certificado disponible?"))
    idiomas_disponibles = models.JSONField(default=list, blank=True, verbose_name=_("Idiomas disponibles"))    

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.titulo)
        super().save(*args, **kwargs)

    def clean(self):
        """
        Realiza validaciones personalizadas antes de guardar el modelo.
        """
        if self.fecha_inicio and self.fecha_fin and self.fecha_inicio > self.fecha_fin:
            raise ValidationError(_("La fecha de inicio debe ser anterior a la fecha de fin."))

    def calcular_promedio_calificaciones(self):
        """
        Calcula y actualiza el promedio de calificaciones del curso.
        """
        promedio = self.reseñas.aggregate(Avg('calificacion'))['calificacion__avg']
        self.calificacion_promedio = round(promedio, 2) if promedio else None
        self.save(update_fields=['calificacion_promedio'])
        logger.info(f"Promedio de calificaciones actualizado para el curso {self.titulo}")

    def calcular_progreso(self, usuario):
        """
        Calcula y actualiza el progreso promedio de todos los estudiantes inscritos en el curso.
        """
        progresos = Progreso.objects.filter(curso=self)
        if progresos.exists():
            self.progreso_promedio = progresos.aggregate(Avg('porcentaje'))['porcentaje__avg']
        else:
            self.progreso_promedio = 0
        self.save(update_fields=['progreso_promedio'])
        logger.info(f"Progreso promedio actualizado para el curso {self.titulo}")

    def calcular_progreso_promedio(self):
        """
        Calcula y actualiza el progreso promedio de todos los estudiantes inscritos en el curso.
        """
        progresos = Progreso.objects.filter(curso=self)
        if progresos.exists():
            progreso_promedio = progresos.aggregate(Avg('porcentaje'))['porcentaje__avg']
        else:
            progreso_promedio = 0
        self.progreso_promedio = progreso_promedio
        self.save(update_fields=['progreso_promedio'])
        logger.info(f"Progreso promedio actualizado para el curso {self.titulo}")
        return progreso_promedio
    

    def calcular_tasa_finalizacion(self):
        """
        Calcula y actualiza la tasa de finalización del curso.
        """
        total_inscritos = self.inscritos.count()
        if total_inscritos > 0:
            finalizados = Progreso.objects.filter(curso=self, porcentaje=100).count()
            self.tasa_finalizacion = (finalizados / total_inscritos) * 100
        else:
            self.tasa_finalizacion = 0
        self.save(update_fields=['tasa_finalizacion'])
        logger.info(f"Tasa de finalización actualizada para el curso {self.titulo}")

    def esta_inscrito(self, usuario):
        """
        Verifica si un usuario está inscrito en el curso.
        """
        return Matriculas.Inscripcion.objects.filter(usuario=usuario, curso=self).exists()

    def actualizar_duracion_total(self):
        """
        Actualiza la duración total del curso sumando la duración de todos sus temas.
        """
        self.duracion_total = sum(tema.tiempo_estimado for tema in self.temas.all())

    def calcular_nivel_satisfaccion(self):
        """
        Calcula y actualiza el nivel de satisfacción del curso basado en las reseñas.
        """
        reseñas = self.reseñas.all()
        if reseñas:
            self.nivel_satisfaccion = reseñas.aggregate(Avg('calificacion'))['calificacion__avg']
            self.save(update_fields=['nivel_satisfaccion'])
            logger.info(f"Nivel de satisfacción actualizado para el curso {self.titulo}")

    def temas_completados(self, usuario):
        """
        Retorna el número de temas completados por un usuario específico.
        """
        return TemaCompletado.objects.filter(tema__curso=self, usuario=usuario).count()

    def total_temas(self):
        """
        Retorna el número total de temas en el curso.
        """
        return self.temas.count()

    def lecciones_completadas(self, usuario):
        """
        Retorna el número de lecciones completadas por un usuario específico.
        """
        return LeccionCompletada.objects.filter(leccion__tema__curso=self, usuario=usuario).count()

    def total_lecciones(self):
        """
        Retorna el número total de lecciones en el curso.
        """
        return sum(tema.lecciones.count() for tema in self.temas.all())

    def actualizar_estadisticas(self):
        """
        Actualiza todas las estadísticas del curso.
        """
        self.calcular_promedio_calificaciones()
        self.calcular_progreso_promedio()
        self.calcular_tasa_finalizacion()
        self.calcular_nivel_satisfaccion()
        self.profesor.actualizar_estadisticas()

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = _("Curso")
        verbose_name_plural = _("Cursos")
        ordering = ['-fecha_inicio']

class Tema(models.Model):
    """
    Modelo para representar los temas dentro de un curso.
    """
    curso = models.ForeignKey(Curso, related_name='temas', on_delete=models.CASCADE, verbose_name=_("Curso"))
    titulo = models.CharField(max_length=255, verbose_name=_("Título"))
    slug = models.SlugField(max_length=255, unique=True, editable=False, verbose_name=_("Slug"))
    contenido = models.TextField(verbose_name=_("Contenido"))
    orden = models.PositiveIntegerField(verbose_name=_("Orden"))
    tiempo_estimado = models.PositiveIntegerField(help_text=_("Tiempo estimado en minutos"), verbose_name=_("Tiempo estimado"))
    microlearning = models.BooleanField(default=False, help_text=_("Indica si el tema es parte de una estrategia de microaprendizaje"), verbose_name=_("Microlearning"))
    contribuyentes = models.ManyToManyField(User, related_name='temas_contribuidos', blank=True, verbose_name=_("Contribuyentes"))
    evaluacion_asociada = models.OneToOneField('Evaluaciones.Evaluacion', on_delete=models.SET_NULL, null=True, blank=True, related_name='tema_asociado', verbose_name=_("Evaluación asociada"))
    recursos_adicionales = models.JSONField(default=list, blank=True, verbose_name=_("Recursos adicionales"))
    objetivos_aprendizaje = models.TextField(blank=True, verbose_name=_("Objetivos de aprendizaje"))

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para generar automáticamente el slug.
        """
        if not self.slug:
            self.slug = slugify(f"{self.curso.slug}-{self.titulo}")
        super().save(*args, **kwargs)
        self.curso.actualizar_duracion_total()

    def esta_completado(self, usuario):
        """
        Verifica si el tema está completado por un usuario específico.
        """
        return TemaCompletado.objects.filter(tema=self, usuario=usuario).exists()

    def calcular_progreso(self, usuario):
        """
        Calcula el progreso del usuario en este tema.
        """
        lecciones_totales = self.lecciones.count()
        if lecciones_totales == 0:
            return 0
        lecciones_completadas = LeccionCompletada.objects.filter(leccion__tema=self, usuario=usuario).count()
        return (lecciones_completadas / lecciones_totales) * 100

    def __str__(self):
        return f"{self.curso.titulo} - {self.titulo}"

    class Meta:
        verbose_name = _("Tema")
        verbose_name_plural = _("Temas")
        unique_together = ('curso', 'orden')
        ordering = ['curso', 'orden']

class Leccion(models.Model):
    """
    Modelo para representar las lecciones dentro de un tema.
    """
    tema = models.ForeignKey(Tema, related_name='lecciones_tema', on_delete=models.CASCADE, verbose_name=_("Tema"))
    titulo = models.CharField(max_length=255, verbose_name=_("Título"))
    contenido = models.TextField(verbose_name=_("Contenido"))
    orden = models.PositiveIntegerField(verbose_name=_("Orden"))
    tiempo_estimado = models.PositiveIntegerField(help_text=_("Tiempo estimado en minutos"), verbose_name=_("Tiempo estimado"))
    tipo_contenido = models.CharField(max_length=50, choices=[
        ('video', _('Video')),
        ('texto', _('Texto')),
        ('quiz', _('Quiz')),
        ('tarea', _('Tarea')),
    ], verbose_name=_("Tipo de contenido"))
    url_contenido = models.URLField(max_length=1024, blank=True, verbose_name=_("URL del contenido"))

    def esta_completada_por(self, usuario):
        """
        Verifica si la lección está completada por un usuario específico.
        """
        return LeccionCompletada.objects.filter(leccion=self, usuario=usuario).exists()

    def marcar_como_completada(self, usuario):
        """
        Marca la lección como completada para un usuario específico.
        """
        LeccionCompletada.objects.get_or_create(leccion=self, usuario=usuario)
        self.tema.curso.actualizar_estadisticas()

    def __str__(self):
        return f"{self.tema.titulo} - {self.titulo}"

    class Meta:
        verbose_name = _("Lección")
        verbose_name_plural = _("Lecciones")
        unique_together = ('tema', 'orden')
        ordering = ['tema', 'orden']

class Reseña(models.Model):
    """
    Modelo para representar las reseñas de los cursos.
    """
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='reseñas', verbose_name=_("Curso"))
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reseñas', verbose_name=_("Usuario"))
    calificacion = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Calificación")
    )
    comentario = models.TextField(blank=True, verbose_name=_("Comentario"))
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de creación"))
    utilidad = models.PositiveIntegerField(
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        verbose_name=_("Utilidad")
    )

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para actualizar las estadísticas del curso y del instructor.
        """
        super().save(*args, **kwargs)
        self.curso.actualizar_estadisticas()

    def __str__(self):
        return f"Reseña de {self.usuario} para {self.curso}"

    class Meta:
        verbose_name = _("Reseña")
        verbose_name_plural = _("Reseñas")
        unique_together = ('curso', 'usuario')
        ordering = ['-fecha_creacion']

class Tag(models.Model):
    """
    Modelo para representar las etiquetas de los cursos.
    """
    nombre = models.CharField(max_length=255, unique=True, verbose_name=_("Nombre"))
    slug = models.SlugField(max_length=255, unique=True, editable=False, verbose_name=_("Slug"))

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para generar automáticamente el slug.
        """
        if not self.slug:
            self.slug = slugify(self.nombre)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")
        ordering = ['nombre']

class TemaCompletado(models.Model):
    """
    Modelo para registrar los temas completados por los usuarios.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='temas_completados', verbose_name=_("Usuario"))
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE, related_name='usuarios_completados', verbose_name=_("Tema"))
    fecha_completado = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de completado"))

    def __str__(self):
        return f"{self.usuario} ha completado {self.tema}"

    class Meta:
        verbose_name = _("Tema Completado")
        verbose_name_plural = _("Temas Completados")
        unique_together = ('usuario', 'tema')
        ordering = ['-fecha_completado']

class LeccionCompletada(models.Model):
    """
    Modelo para registrar las lecciones completadas por los usuarios.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lecciones_completadass', verbose_name=_("Usuario"))
    leccion = models.ForeignKey(Leccion, on_delete=models.CASCADE, related_name='usuarios_completadoss', verbose_name=_("Lección"))
    fecha_completado = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de completado"))

    def __str__(self):
        return f"{self.usuario} ha completado {self.leccion}"

    class Meta:
        verbose_name = _("Lección Completada")
        verbose_name_plural = _("Lecciones Completadas")
        unique_together = ('usuario', 'leccion')
        ordering = ['-fecha_completado']

class Progreso(models.Model):
    """
    Modelo para registrar el progreso de los usuarios en los cursos.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='curso_progresos', verbose_name=_("Usuario"))
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='progresos', verbose_name=_("Curso"))
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=_("Porcentaje de progreso"))
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name=_("Fecha de actualización"))

    def actualizar_progreso(self):
        """
        Actualiza el porcentaje de progreso basado en las lecciones completadas.
        """
        total_lecciones = self.curso.total_lecciones()
        if total_lecciones > 0:
            lecciones_completadas = self.curso.lecciones_completadas(self.usuario)
            self.porcentaje = (lecciones_completadas / total_lecciones) * 100
        else:
            self.porcentaje = 0
        self.save()
        logger.info(f"Progreso actualizado para el usuario {self.usuario.username} en el curso {self.curso.titulo}")

    def __str__(self):
        return f"{self.usuario.username} - {self.curso.titulo} - {self.porcentaje}%"

    class Meta:
        verbose_name = _("Progreso")
        verbose_name_plural = _("Progresos")
        unique_together = ('usuario', 'curso')
        ordering = ['-fecha_actualizacion']

class Certificado(models.Model):
    """
    Modelo para representar los certificados de finalización de cursos.
    """
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='certificados', verbose_name=_("Usuario"))
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name='certificados', verbose_name=_("Curso"))
    fecha_emision = models.DateTimeField(auto_now_add=True, verbose_name=_("Fecha de emisión"))
    codigo_verificacion = models.CharField(max_length=50, unique=True, verbose_name=_("Código de verificación"))

    def generar_codigo_verificacion(self):
        """
        Genera un código de verificación único para el certificado.
        """
        import uuid
        self.codigo_verificacion = str(uuid.uuid4())[:8].upper()

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para generar el código de verificación si no existe.
        """
        if not self.codigo_verificacion:
            self.generar_codigo_verificacion()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Certificado de {self.usuario.username} para {self.curso.titulo}"

    class Meta:
        verbose_name = _("Certificado")
        verbose_name_plural = _("Certificados")
        unique_together = ('usuario', 'curso')
        ordering = ['-fecha_emision']