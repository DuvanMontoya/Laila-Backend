from django.contrib import admin
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from Autenticacion.models import UserProfile
from Autenticacion.models import Token
from Autenticacion.models import Solicitud
from Autenticacion.models import Rol




class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

class UsuarioArticuloInline(admin.TabularInline):
    model = UsuarioArticulo
    extra = 1

class ArticuloAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'categoria_articulo', 'publicado', 'num_vistas', 'num_likes', 'calificacion_promedio')
    list_filter = ('categoria_articulo', 'publicado', 'autor')
    search_fields = ('titulo', 'contenido', 'autor__username')
    inlines = (UsuarioArticuloInline,)
    actions = ['publicar_articulos', 'despublicar_articulos']

    def num_vistas(self, obj):
        return obj.vistas.count()

    def num_likes(self, obj):
        return obj.likes.count()

    def publicar_articulos(self, request, queryset):
        queryset.update(publicado=True)
    publicar_articulos.short_description = "Publicar artículos seleccionados"

    def despublicar_articulos(self, request, queryset):
        queryset.update(publicado=False)
    despublicar_articulos.short_description = "Despublicar artículos seleccionados"

class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'articulo', 'contenido', 'creado', 'actualizado')
    list_filter = ('creado', 'actualizado', 'usuario')
    search_fields = ('contenido', 'usuario__username', 'articulo__titulo')

class UsuarioArticuloAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'articulo', 'favorito', 'calificacion')
    list_filter = ('favorito', 'calificacion')
    search_fields = ('usuario__username', 'articulo__titulo')

class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')

class CategoriaArticuloAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')

class TemaArticuloAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')

# Unregister the existing User admin
admin.site.unregister(User)

# Register all models in admin site
admin.site.register(User, UserAdmin)
admin.site.register(Area, admin.ModelAdmin)
admin.site.register(Articulo, ArticuloAdmin)
admin.site.register(Comentario, ComentarioAdmin)
admin.site.register(UsuarioArticulo, UsuarioArticuloAdmin)
admin.site.register(Rol, RolAdmin)
admin.site.register(CategoriaArticulo, CategoriaArticuloAdmin)
admin.site.register(TemaArticulo, TemaArticuloAdmin)
admin.site.register(Solicitud, admin.ModelAdmin)
admin.site.register(Token, admin.ModelAdmin)

# Customizing the admin interface
admin.site.site_header = "Laila Admin"
admin.site.site_title = "Laila Admin Portal"
admin.site.index_title = "Welcome to Laila Administration"
