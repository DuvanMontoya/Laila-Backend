from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import *

# Inline for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'profile'

# Extend UserAdmin to include UserProfile
class CustomUserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions',)

# Admin for Rol model
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')

# Admin for UsuarioRol model
class UsuarioRolAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol')
    search_fields = ('usuario__username', 'rol__nombre')
    list_filter = ('rol',)

# Admin for Token model
class TokenAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'token', 'fecha')
    search_fields = ('usuario__username', 'token')
    list_filter = ('fecha',)

# Admin for Solicitud model
class SolicitudAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'usuario_solicitud', 'fecha', 'aceptado')
    search_fields = ('usuario__username', 'usuario_solicitud__username')
    list_filter = ('aceptado', 'fecha')

# Unregister the default UserAdmin
admin.site.unregister(User)

# Register the custom UserAdmin and other models
admin.site.register(User, CustomUserAdmin)

# Avoid multiple registrations
if not admin.site.is_registered(Rol):
    admin.site.register(Rol, RolAdmin)
if not admin.site.is_registered(UsuarioRol):
    admin.site.register(UsuarioRol, UsuarioRolAdmin)
if not admin.site.is_registered(Token):
    admin.site.register(Token, TokenAdmin)
if not admin.site.is_registered(Solicitud):
    admin.site.register(Solicitud, SolicitudAdmin)

# Customizing the admin interface for the Autenticacion app
admin.site.site_header = "Laila Autenticacion Admin"
admin.site.site_title = "Laila Autenticacion Admin Portal"
admin.site.index_title = "Welcome to Laila Autenticacion Administration"
