from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class Rol(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre


class UsuarioRol(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)

    def __str__(self):
        return self.usuario.username + ' - ' + self.rol.nombre



class Token(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.token


class Solicitud(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usuario')
    usuario_solicitud = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usuario_solicitud')
    fecha = models.DateTimeField(auto_now_add=True)
    aceptado = models.BooleanField(default=False)

    def __str__(self):
        return self.usuario.username + ' - ' + self.usuario_solicitud.username


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)    

    def __str__(self):
        return self.user.username


# class Mensaje(models.Model):
#     usuario = models.ForeignKey(User, on_delete=models.CASCADE)
#     usuario_destino = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usuario_destino')
#     mensaje = models.TextField()
#     fecha = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.usuario.username + ' - ' + self.usuario_destino.username


# class Publicacion(models.Model):
#     usuario = models.ForeignKey(User, on_delete=models.CASCADE)
#     mensaje = models.TextField()
#     fecha = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.usuario.username + ' - ' + self.mensaje


# class Comentario(models.Model):
#     usuario = models.ForeignKey(User, on_delete=models.CASCADE)
#     publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE)
#     mensaje = models.TextField()
#     fecha = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.usuario.username + ' - ' + self.mensaje


# class Like(models.Model):
#     usuario = models.ForeignKey(User, on_delete=models.CASCADE)
#     publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE)
#     fecha = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return self.usuario.username + ' - ' + self.publicacion.mensaje

    

# class Notificacion(models.Model):
#     usuario = models.ForeignKey(User, on_delete=models.CASCADE)
#     mensaje = models.TextField()
#     fecha = models.DateTimeField(auto_now_add=True)
#     leido = models.BooleanField(default=False)

#     def __str__(self):
#         return self.mensaje