from rest_framework.permissions import BasePermission, SAFE_METHODS




class IsOwnerOrReadOnly(BasePermission):
    """
    Objeto de permiso personalizado que permite solo a los propietarios del objeto editarlos.
    """
    def has_object_permission(self, request, view, obj):
        # Los métodos de lectura son permitidos para cualquier solicitud,
        # así que siempre permitiremos GET, HEAD o OPTIONS.
        if request.method in SAFE_METHODS:
            return True

        # Escribir permisos son solo permitidos al propietario del objeto.
        return obj.owner == request.user