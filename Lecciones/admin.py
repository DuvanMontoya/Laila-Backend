from django.contrib import admin
from .models import Leccion, Progreso

class PrerrequisitoInline(admin.TabularInline):
    model = Leccion.prerrequisitos.through
    fk_name = 'from_leccion'
    verbose_name = "Prerrequisito"
    verbose_name_plural = "Prerrequisitos"
    extra = 1

class ProgresoInline(admin.TabularInline):
    model = Progreso
    extra = 1

@admin.register(Leccion)
class LeccionAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'slug', 'estado', 'tiempo_estimado', 'tiene_material', 'es_demo', 'tipo_leccion', 'tema', 'calificacion', 'owner')
    list_filter = ('estado', 'tipo_leccion', 'tema', 'tiene_material', 'es_demo', 'calificacion')
    search_fields = ('titulo', 'contenido_texto')
    inlines = [PrerrequisitoInline, ProgresoInline]
    readonly_fields = ('progreso_por_usuario', 'eventos', 'feedbacks')

    fieldsets = (
        (None, {
            'fields': ('titulo', 'nombre', 'slug', 'estado', 'tiempo_estimado', 'tiene_material', 'es_demo', 'tipo_leccion', 'contenido_texto', 'contenido_multimedia', 'orden', 'tema', 'evaluacion_asociada', 'calificacion', 'owner')
        }),
        ('Relaciones', {
            'fields': ('prerrequisitos',)
        }),
        ('Avanzado', {
            'classes': ('collapse',),
            'fields': ('progreso_por_usuario', 'eventos', 'feedbacks')
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.owner:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

@admin.register(Progreso)
class ProgresoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'leccion', 'completado', 'fecha_completado')
    list_filter = ('completado', 'fecha_completado', 'leccion')
    search_fields = ('usuario__username', 'leccion__titulo')

# Customizing the admin interface for the Lecciones app
admin.site.site_header = "Laila Lecciones Admin"
admin.site.site_title = "Laila Lecciones Admin Portal"
admin.site.index_title = "Welcome to Laila Lecciones Administration"
