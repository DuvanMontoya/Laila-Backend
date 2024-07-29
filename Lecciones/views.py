from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *
from .permissions import IsEnrolledInCourse, IsEnrolled
import logging

from Cursos.models import Curso, Tema

from Cursos.serializers import ProgresoCompletoSerializer

logger = logging.getLogger(__name__)


class LeccionesCompletadasView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, curso_id):
        logger.info(f"Solicitando lecciones completadas para el curso {curso_id} y usuario {request.user.username}")
        lecciones_completadas = LeccionCompletada.objects.filter(
            usuario=request.user,
            leccion__tema__curso_id=curso_id
        )
        logger.info(f"Lecciones completadas encontradas: {lecciones_completadas.count()}")
        
        todas_lecciones = Leccion.objects.filter(tema__curso_id=curso_id)
        
        lecciones_estado = {
            str(leccion.id): {
                'id': leccion.id,
                'completada': lecciones_completadas.filter(leccion=leccion).exists()
            }
            for leccion in todas_lecciones
        }
        
        logger.info(f"Estado de lecciones: {lecciones_estado}")
        return Response(lecciones_estado)

class LeccionViewSet(viewsets.ModelViewSet):
    queryset = Leccion.objects.all()
    serializer_class = LeccionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def marcar_completada(self, request, pk=None):
        leccion = self.get_object()
        usuario = request.user
        leccion_completada, created = LeccionCompletada.objects.get_or_create(usuario=usuario, leccion=leccion)
        if created:
            # Actualizar el progreso del curso aquí si es necesario
            return Response({'status': 'Lección marcada como completada'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'La lección ya estaba marcada como completada'}, status=status.HTTP_200_OK)

   




class CompletarLeccionView(generics.UpdateAPIView):
    serializer_class = LeccionSerializer
    permission_classes = [permissions.IsAuthenticated, IsEnrolled]

    def get_object(self):
        leccion_id = self.kwargs['leccion_id']
        return Leccion.objects.get(id=leccion_id)

    def perform_update(self, serializer):
        leccion = self.get_object()
        leccion.completada_por.add(self.request.user)
        serializer.save()


class LeccionDetallesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        leccion = get_object_or_404(Leccion, pk=pk)
        serializer = LeccionDetallesSerializer(leccion)
        return Response(serializer.data)

    def put(self, request, pk):
        leccion = get_object_or_404(Leccion, pk=pk)
        serializer = LeccionDetallesSerializer(leccion, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class RegistrarProgresoLeccionView(APIView):
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsEnrolled])
    def completar(self, request, pk=None):
        leccion = self.get_object()
        leccion.completada_por.add(request.user)
        leccion.save()

        # Actualizar progreso del tema y curso
        tema = leccion.tema
        curso = tema.curso
        usuario = request.user

        progreso_tema = tema.calcular_progreso(usuario)
        progreso_curso = curso.calcular_progreso(usuario)

        return Response({
            'status': 'Lección marcada como completada',
            'completada': True,
            'progreso_tema': progreso_tema,
            'progreso_curso': progreso_curso
        })

    def post(self, request, pk):
        leccion = get_object_or_404(Leccion, pk=pk)
        progreso = request.data.get('progreso')
        leccion.registrar_progreso(request.user.id, progreso)
        return Response({'status': 'Progreso registrado exitosamente'})
    


class AgregarFeedbackLeccionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        leccion = get_object_or_404(Leccion, pk=pk)
        comentario = request.data.get('comentario')
        calificacion = request.data.get('calificacion')
        leccion.agregar_feedback(request.user.id, comentario, calificacion)
        return Response({'status': 'Feedback agregado exitosamente'})
    


class LeccionPendienteList(generics.ListAPIView):
    serializer_class = LeccionPendienteSerializer

    def get_queryset(self):
        usuario_id = self.request.query_params.get('usuario')
        if usuario_id:
            return LeccionPendiente.objects.filter(usuario_id=usuario_id)
        return LeccionPendiente.objects.all()
    


class LeccionCompletadaList(generics.ListAPIView):
    serializer_class = LeccionCompletadaSerializer

    def get_queryset(self):
        usuario_id = self.request.query_params.get('usuario')
        if usuario_id:
            lecciones_completadas = Leccion.objects.filter(completada_por__id=usuario_id)
            return lecciones_completadas
        return Leccion.objects.none()
    


class LeccionCompletadaDetail(generics.RetrieveAPIView):
    queryset = LeccionCompletada.objects.all()
    serializer_class = LeccionCompletadaSerializer
    permission_classes = [IsAuthenticated, IsEnrolled]

    def get_object(self):
        queryset = self.get_queryset()
        filter = {'usuario': self.request.user.id}
        return get_object_or_404(queryset, **filter)
    

class MarcarLeccionCompletadaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, leccion_id):
        leccion = Leccion.objects.get(id=leccion_id)
        LeccionCompletada.objects.get_or_create(usuario=request.user, leccion=leccion)
        return Response({"status": "Lección marcada como completada"})
    

class ProgresoCompletoPorCursoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, curso_id, user_id):
        curso = Curso.objects.get(id=curso_id)
        temas = Tema.objects.filter(curso=curso)
        lecciones = Leccion.objects.filter(tema__curso=curso)
        
        temas_completados = sum(1 for tema in temas if all(leccion.esta_completada_por(request.user) for leccion in tema.lecciones.all()))
        lecciones_completadas = sum(1 for leccion in lecciones if leccion.esta_completada_por(request.user))
        
        data = {
            'temas_completados': temas_completados,
            'total_temas': temas.count(),
            'lecciones_completadas': lecciones_completadas,
            'total_lecciones': lecciones.count()
        }
        
        serializer = ProgresoCompletoSerializer(data)
        return Response(serializer.data)