from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.utils import timezone
# from Cursos.models import Curso



class Inscripcion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inscripciones_curso')
    perfil = models.ForeignKey('Usuarios.Perfil', on_delete=models.CASCADE, related_name='inscripciones_curso', null=True, blank=True)
    curso = models.ForeignKey("Cursos.Curso", on_delete=models.CASCADE, related_name='inscripciones')
    fecha_inscripcion = models.DateTimeField(auto_now_add=True, verbose_name=("Fecha de Inscripción"))
    progreso = models.FloatField(default=0.0, verbose_name=("Progreso"))
    calificacion_final = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    certificado_url = models.URLField(max_length=1024, blank=True)

    def calcular_progreso(self):
        temas = self.curso.temas.all()
        progreso_total = sum(tema.calcular_progreso(self.usuario) for tema in temas)
        self.progreso = progreso_total / len(temas) if temas else 0
        self.save()

    def calcular_calificacion_final(self):
        temas = self.curso.temas.all()
        calificaciones_temas = [tema.calcular_calificacion() for tema in temas]
        self.calificacion_final = sum(calificaciones_temas) / len(calificaciones_temas) if calificaciones_temas else 0
        self.save()

    def marcar_como_finalizado(self):
        if self.progreso == 100:
            self.fecha_finalizacion = timezone.now()
            self.certificado_url = "enlace_al_certificado"
            self.save()

    def __str__(self):
        return f"Inscripción de {self.usuario} en {self.curso}"

    class Meta:
        verbose_name = _("Inscripción")
        verbose_name_plural = _("Inscripciones")
        unique_together = ('usuario', 'curso')
        ordering = ['fecha_inscripcion']





class SolicitudInscripcion(models.Model):
    perfil = models.ForeignKey(User, on_delete=models.CASCADE)
    curso = models.ForeignKey("Cursos.Curso", on_delete=models.CASCADE)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='pendiente')

    def __str__(self):
        return f'Solicitud de {self.perfil.username} para {self.curso.titulo}'