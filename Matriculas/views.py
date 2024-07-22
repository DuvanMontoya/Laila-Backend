from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import *
from .serializers import *
from rest_framework import generics




from django.db.models.query import QuerySet

class InscripcionViewSet(viewsets.ModelViewSet):
    queryset = Inscripcion.objects.all()
    serializer_class = InscripcionSerializer

    def get_queryset(self) -> QuerySet:
        if getattr(self, 'swagger_fake_view', False):
            # Cuando se genera la documentación de la API, no filtra por usuario
            return self.queryset
        return self.queryset.filter(usuario=self.request.user)




class SolicitudInscripcionViewSet(viewsets.ModelViewSet):
    queryset = SolicitudInscripcion.objects.all()
    serializer_class = SolicitudInscripcionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        curso_id = self.request.query_params.get('curso')
        if curso_id:
            return self.queryset.filter(curso_id=curso_id, perfil=self.request.user)
        return self.queryset

    def perform_create(self, serializer):
        serializer.save(perfil=self.request.user)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def listar_solicitudes(self, request):
        curso_id = request.query_params.get('curso')
        if curso_id:
            solicitudes = SolicitudInscripcion.objects.filter(curso_id=curso_id)
        else:
            solicitudes = SolicitudInscripcion.objects.all()
        serializer = self.get_serializer(solicitudes, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def aceptar(self, request, pk=None):
        try:
            solicitud = self.get_object()
            inscripcion, created = Inscripcion.objects.get_or_create(usuario=solicitud.perfil.usuario, curso=solicitud.curso)
            if created:
                solicitud.delete()
                return Response({'status': 'Inscripción aceptada'})
            return Response({'status': 'El usuario ya está inscrito en este curso'}, status=status.HTTP_400_BAD_REQUEST)
        except SolicitudInscripcion.DoesNotExist:
            return Response({'error': 'La solicitud no existe'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def rechazar(self, request, pk=None):
        try:
            solicitud = self.get_object()
            solicitud.delete()
            return Response({'status': 'Solicitud rechazada'})
        except SolicitudInscripcion.DoesNotExist:
            return Response({'error': 'La solicitud no existe'}, status=status.HTTP_404_NOT_FOUND)
        


class InscripcionList(generics.ListAPIView):
    serializer_class = InscripcionSerializer

    def get_queryset(self):
        usuario_id = self.request.query_params.get('usuario')
        if usuario_id:
            return Inscripcion.objects.filter(usuario_id=usuario_id)
        return Inscripcion.objects.all()