from django.contrib import admin
from .models import Tarea, EntregaTarea

class EntregaTareaInline(admin.TabularInline):
    model = EntregaTarea
    extra = 1
    readonly_fields = ('fecha_entrega',)
    can_delete = True

@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'slug', 'estado', 'fecha_asignacion', 'fecha_vencimiento', 'calificacion', 'leccion')
    list_filter = ('estado', 'fecha_asignacion', 'fecha_vencimiento', 'leccion')
    search_fields = ('titulo', 'descripcion')
    inlines = [EntregaTareaInline]
    readonly_fields = ('fecha_asignacion',)

    fieldsets = (
        (None, {
            'fields': ('titulo', 'slug', 'descripcion', 'fecha_asignacion', 'fecha_vencimiento', 'peso_en_calificacion_final', 'revisiones_permitidas', 'peso_tareas_colaborativas', 'es_opcional', 'estado', 'calificacion', 'leccion', 'evaluacion_asociada')
        }),
    )

@admin.register(EntregaTarea)
class EntregaTareaAdmin(admin.ModelAdmin):
    list_display = ('tarea', 'usuario', 'fecha_entrega', 'archivo')
    list_filter = ('fecha_entrega', 'tarea', 'usuario')
    search_fields = ('tarea__titulo', 'usuario__username')

# Customizing the admin interface for the Tareas app
admin.site.site_header = "Laila Tareas Admin"
admin.site.site_title = "Laila Tareas Admin Portal"
admin.site.index_title = "Welcome to Laila Tareas Administration"
