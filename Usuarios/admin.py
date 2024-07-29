from django.contrib import admin
from .models import Perfil

@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'nombre', 'apellido', 'profesion', 'edad', 'genero', 'pais', 'ciudad', 'fecha_creacion', 'fecha_actualizacion')
    list_filter = ('genero', 'pais', 'ciudad', 'profesion', 'fecha_creacion', 'fecha_actualizacion')
    search_fields = ('usuario__username', 'nombre', 'apellido', 'correo', 'whatsapp')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    fieldsets = (
        (None, {
            'fields': ('usuario', 'avatar_url', 'nombre', 'apellido', 'profesion', 'edad', 'genero', 'fecha_nacimiento', 'pais', 'ciudad', 'direccion', 'whatsapp', 'correo', 'biografia', 'avatar')
        }),
        ('Redes Sociales', {
            'fields': ('twitter', 'linkedin', 'github', 'website')
        }),
        ('Información Adicional', {
            'fields': ( 'fecha_creacion', 'fecha_actualizacion')
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('usuario')

# Customizing the admin interface for the Usuarios app
admin.site.site_header = "Laila Usuarios Admin"
admin.site.site_title = "Laila Usuarios Admin Portal"
admin.site.index_title = "Welcome to Laila Usuarios Administration"
