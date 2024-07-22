from django.contrib import admin
from .models import Curso, Tema, Categoria, Instructor, Reseña, Tag
from Matriculas.models import Inscripcion, SolicitudInscripcion
from django.utils.html import format_html

class TemaInline(admin.TabularInline):
    model = Tema
    extra = 1

class InscripcionInline(admin.TabularInline):
    model = Inscripcion
    extra = 1

@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'categoria', 'instructor_name', 'fecha_inicio', 'fecha_fin', 'calificacion_promedio', 'mostrar_imagen')
    list_filter = ('categoria', 'fecha_inicio', 'fecha_fin', 'profesor')
    search_fields = ('titulo', 'descripcion')
    inlines = [TemaInline, InscripcionInline]

    def mostrar_imagen(self, obj):
        if obj.imagen_principal_url:
            return format_html('<img src="{}" style="width: 50px; height:50px;" />', obj.imagen_principal_url)
        return "(No image)"
    mostrar_imagen.short_description = 'Imagen'

    def instructor_name(self, obj):
        return obj.profesor.usuario.username
    instructor_name.short_description = 'Instructor'

@admin.register(Tema)
class TemaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'curso', 'tiempo_estimado', 'microlearning')
    list_filter = ('curso', 'tiempo_estimado', 'microlearning')
    search_fields = ('titulo',)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'curso', 'fecha_inscripcion', 'progreso', 'calificacion_final')
    list_filter = ('fecha_inscripcion', 'curso', 'calificacion_final')
    search_fields = ('usuario__username', 'curso__titulo')

@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'titulo', 'bio', 'num_estudiantes', 'promedio_calificacion')
    search_fields = ('usuario__username', 'titulo', 'bio')
    list_filter = ('num_estudiantes', 'promedio_calificacion')

@admin.register(Reseña)
class ReseñaAdmin(admin.ModelAdmin):
    list_display = ('curso', 'usuario', 'calificacion', 'fecha_creacion')
    list_filter = ('curso', 'calificacion', 'fecha_creacion')
    search_fields = ('usuario__username', 'curso__titulo', 'comentario')

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(SolicitudInscripcion)
class SolicitudInscripcionAdmin(admin.ModelAdmin):
    list_display = ('perfil', 'curso', 'fecha_solicitud', 'estado')
    list_filter = ('fecha_solicitud', 'estado')
    search_fields = ('perfil__username', 'curso__titulo')

# Customizing the admin interface for the Cursos app
admin.site.site_header = "Laila Cursos Admin"
admin.site.site_title = "Laila Cursos Admin Portal"
admin.site.index_title = "Welcome to Laila Cursos Administration"
