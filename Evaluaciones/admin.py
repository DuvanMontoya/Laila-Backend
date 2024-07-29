from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from django import forms
from .models import (
    Competencia, ContenidoMatematico, Evaluacion, Pregunta, Opcion,
    IntentoEvaluacion, RespuestaPregunta, Tag, ResultadoEvaluacion,
    EstadisticasEvaluacion
)

class CompetenciaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'pregunta_count')
    search_fields = ('nombre', 'descripcion')

    def pregunta_count(self, obj):
        return obj.preguntas.count()
    pregunta_count.short_description = _("Número de Preguntas")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(pregunta_count=Count('preguntas'))

admin.site.register(Competencia, CompetenciaAdmin)

class ContenidoMatematicoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'es_generico', 'pregunta_count')
    list_filter = ('categoria', 'es_generico')
    search_fields = ('nombre',)

    def pregunta_count(self, obj):
        return obj.preguntas.count()
    pregunta_count.short_description = _("Número de Preguntas")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(pregunta_count=Count('preguntas'))

admin.site.register(ContenidoMatematico, ContenidoMatematicoAdmin)

class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 4
    fields = ('texto_opcion', 'es_correcta', 'puntos')

class PreguntaAdminForm(forms.ModelForm):
    class Meta:
        model = Pregunta
        fields = '__all__'
        widgets = {
            'texto_pregunta': forms.Textarea(attrs={'rows': 3}),
            'explicacion_respuesta': forms.Textarea(attrs={'rows': 3}),
        }

class PreguntaAdmin(admin.ModelAdmin):
    form = PreguntaAdminForm
    inlines = [OpcionInline]
    list_display = ('texto_pregunta_truncated', 'tipo_pregunta', 'dificultad', 'puntos', 'competencia', 'contenido_matematico', 'activa')
    list_filter = ('tipo_pregunta', 'dificultad', 'activa', 'competencia', 'contenido_matematico')
    search_fields = ('texto_pregunta', 'categoria')
    filter_horizontal = ('tags',)
    readonly_fields = ('fecha_creacion', 'fecha_modificacion')
    fieldsets = (
        (None, {
            'fields': ('texto_pregunta', 'tipo_pregunta', 'dificultad', 'puntos', 'tiempo_estimado')
        }),
        (_('Categorización'), {
            'fields': ('categoria', 'competencia', 'contenido_matematico', 'situacion', 'tags')
        }),
        (_('Detalles'), {
            'fields': ('imagen_svg', 'marcar_respuesta', 'explicacion_respuesta', 'comentarios')
        }),
        (_('Estado'), {
            'fields': ('activa', 'fecha_creacion', 'fecha_modificacion')
        }),
    )

    def texto_pregunta_truncated(self, obj):
        return obj.texto_pregunta[:100] + '...' if len(obj.texto_pregunta) > 100 else obj.texto_pregunta
    texto_pregunta_truncated.short_description = _("Texto de la Pregunta")

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            instance.save()
        formset.save_m2m()
        
        # Ensure only one option is marked as correct for SIMPLE and VERDADERO_FALSO questions
        if form.instance.tipo_pregunta in [Pregunta.TipoPreguntaChoices.SIMPLE, Pregunta.TipoPreguntaChoices.VERDADERO_FALSO]:
            correct_options = form.instance.opciones.filter(es_correcta=True)
            if correct_options.count() > 1:
                correct_options.update(es_correcta=False)
                correct_options.first().es_correcta = True
                correct_options.first().save()

admin.site.register(Pregunta, PreguntaAdmin)

class EvaluacionPreguntasInline(admin.TabularInline):
    model = Evaluacion.preguntas.through
    extra = 1
    verbose_name = _("Pregunta")
    verbose_name_plural = _("Preguntas")

class EvaluacionAdmin(admin.ModelAdmin):
    inlines = [EvaluacionPreguntasInline]
    list_display = ('titulo', 'tipo', 'fecha_inicio', 'fecha_fin', 'ponderacion', 'intentos_permitidos', 'resultados_visibles')
    list_filter = ('tipo', 'resultados_visibles')
    search_fields = ('titulo', 'descripcion')
    filter_horizontal = ('usuarios_permitidos',)
    readonly_fields = ('puntaje_maximo',)
    fieldsets = (
        (None, {
            'fields': ('titulo', 'tipo', 'descripcion', 'ponderacion', 'criterios_aprobacion')
        }),
        (_('Fechas'), {
            'fields': ('fecha_inicio', 'fecha_fin', 'fecha_limite')
        }),
        (_('Configuración'), {
            'fields': ('intentos_permitidos', 'tiempo_limite', 'resultados_visibles', 'mostrar_resultados', 'mostrar_opciones_correctas')
        }),
        (_('Relaciones'), {
            'fields': ('leccion_evaluacion', 'tema_evaluacion', 'curso_evaluacion', 'usuarios_permitidos')
        }),
        (_('Detalles'), {
            'fields': ('puntaje_maximo', 'rubrica')
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.calcular_puntaje_maximo()

    actions = ['recalcular_puntaje_maximo']

    def recalcular_puntaje_maximo(self, request, queryset):
        for evaluacion in queryset:
            evaluacion.calcular_puntaje_maximo()
        self.message_user(request, _("Se ha recalculado el puntaje máximo para las evaluaciones seleccionadas."))
    recalcular_puntaje_maximo.short_description = _("Recalcular puntaje máximo")

admin.site.register(Evaluacion, EvaluacionAdmin)

class RespuestaPreguntaInline(admin.TabularInline):
    model = RespuestaPregunta
    extra = 0
    readonly_fields = ('pregunta', 'respuesta', 'es_correcta', 'puntos_obtenidos', 'fecha_respuesta')
    can_delete = False

class IntentoEvaluacionAdmin(admin.ModelAdmin):
    inlines = [RespuestaPreguntaInline]
    list_display = ('evaluacion', 'usuario', 'fecha_inicio', 'fecha_fin', 'puntaje_obtenido', 'completado')
    list_filter = ('evaluacion', 'completado')
    search_fields = ('usuario__username', 'evaluacion__titulo')
    readonly_fields = ('evaluacion', 'usuario', 'fecha_inicio', 'fecha_fin', 'puntaje_obtenido', 'completado', 'tiempo_tomado', 'porcentaje_puntaje', 'aprobacion')

    fieldsets = (
        (None, {
            'fields': ('evaluacion', 'usuario', 'completado')
        }),
        (_('Fechas'), {
            'fields': ('fecha_inicio', 'fecha_fin', 'hora_inicio', 'hora_fin')
        }),
        (_('Resultados'), {
            'fields': ('puntaje_obtenido', 'porcentaje_puntaje', 'aprobacion', 'tiempo_tomado')
        }),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(IntentoEvaluacion, IntentoEvaluacionAdmin)

class TagAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'slug')
    prepopulated_fields = {'slug': ('nombre',)}
    search_fields = ('nombre', 'slug')

admin.site.register(Tag, TagAdmin)

class ResultadoEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('evaluacion', 'usuario', 'puntaje_total', 'fecha_resultado', 'mejor_intento_link')
    list_filter = ('evaluacion', 'fecha_resultado')
    search_fields = ('usuario__username', 'evaluacion__titulo')
    readonly_fields = ('evaluacion', 'usuario', 'puntaje_total', 'fecha_resultado', 'mejor_intento')

    def mejor_intento_link(self, obj):
        if obj.mejor_intento:
            url = reverse('admin:your_app_intentoevaluacion_change', args=[obj.mejor_intento.id])
            return format_html('<a href="{}">{}</a>', url, obj.mejor_intento)
        return "-"
    mejor_intento_link.short_description = _("Mejor Intento")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(ResultadoEvaluacion, ResultadoEvaluacionAdmin)

class EstadisticasEvaluacionAdmin(admin.ModelAdmin):
    list_display = ('evaluacion', 'numero_intentos', 'puntaje_promedio', 'tiempo_promedio', 'tasa_aprobacion')
    readonly_fields = ('evaluacion', 'numero_intentos', 'puntaje_promedio', 'tiempo_promedio', 'tasa_aprobacion')
    search_fields = ('evaluacion__titulo',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    actions = ['actualizar_estadisticas']

    def actualizar_estadisticas(self, request, queryset):
        for estadistica in queryset:
            estadistica.actualizar_estadisticas()
        self.message_user(request, _("Se han actualizado las estadísticas para las evaluaciones seleccionadas."))
    actualizar_estadisticas.short_description = _("Actualizar estadísticas")

admin.site.register(EstadisticasEvaluacion, EstadisticasEvaluacionAdmin)

# Personalizar el sitio de administración
admin.site.site_header = _("Sistema de Evaluación - Administración")
admin.site.site_title = _("Panel de Administración")
admin.site.index_title = _("Bienvenido al Sistema de Evaluación")