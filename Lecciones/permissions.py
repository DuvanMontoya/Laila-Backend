from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.permissions import BasePermission




class IsEnrolled(BasePermission):
    def has_object_permission(self, request, view, obj):
        curso = obj.tema.curso
        return curso.inscritos.filter(id=request.user.id).exists()


class IsEnrolledInCourse(BasePermission):
    def has_object_permission(self, request, view, obj):
        curso = obj.tema.curso
        usuario = request.user
        return curso.esta_inscrito(usuario)