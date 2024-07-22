from rest_framework.decorators import action
from rest_framework.response import Response
from .models import *
from .serializers import *
from Articulos.permissions import IsOwnerOrReadOnly
from Matriculas.models import Inscripcion, SolicitudInscripcion
from rest_framework import viewsets, permissions, status, generics
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from Matriculas.serializers import InscripcionSerializer
from django.db.models import Count, Avg



class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=True, methods=['get'])
    def cursos(self, request, pk=None):
        categoria = self.get_object()
        cursos = Curso.objects.filter(categoria=categoria)
        serializer = CursoSerializer(cursos, many=True, context={'request': request})
        return Response(serializer.data)

class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.action in ['list', 'create']:
            return CursoSerializer
        return CursoDetailSerializer

    def _check_enrollment(self, user, curso):
        return curso.inscritos.filter(id=user.id).exists()

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def detalles(self, request, pk=None):
        curso = self.get_object()
        user = request.user
        is_enrolled = self._check_enrollment(user, curso)
        curso_data = self.get_serializer(curso, context={'request': request}).data
        curso_data['esta_inscrito'] = is_enrolled
        return Response(curso_data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def inscribir(self, request, pk=None):
        curso = self.get_object()
        if self._check_enrollment(request.user, curso):
            return Response({'status': 'Ya estás inscrito en este curso'}, status=status.HTTP_400_BAD_REQUEST)
        inscripcion, created = Inscripcion.objects.get_or_create(usuario=request.user, curso=curso)
        if created:
            curso.inscritos.add(request.user)
            return Response({'status': 'Inscripción exitosa'})
        return Response({'status': 'Error al inscribirse'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def calificar(self, request, pk=None):
        curso = self.get_object()
        serializer = ReseñaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(usuario=request.user, curso=curso)
            curso.calcular_promedio_calificaciones()
            curso.calcular_nivel_satisfaccion()
            return Response({'status': 'Calificación registrada'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def verificar_inscripcion(self, request, pk=None):
        curso = self.get_object()
        inscrito = Inscripcion.objects.filter(usuario=request.user, curso=curso).exists()
        return Response({'inscrito': inscrito})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def solicitar_inscripcion(self, request, pk=None):
        try:
            curso = self.get_object()
            if self._check_enrollment(request.user, curso):
                return Response({'status': 'inscrito'}, status=status.HTTP_200_OK)
            
            solicitud, created = SolicitudInscripcion.objects.get_or_create(perfil=request.user, curso=curso)
            if not created:
                return Response({'status': 'solicitud_pendiente'}, status=status.HTTP_200_OK)
            
            solicitud.estado = 'pendiente'
            solicitud.save()
            
            return Response({'status': 'solicitud_enviada'}, status=status.HTTP_201_CREATED)
        
        except Curso.DoesNotExist:
            return Response({'error': 'El curso no existe'}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({'error': 'Ocurrió un error en el servidor: ' + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        curso = self.get_object()
        estadisticas = {
            'total_inscritos': curso.inscritos.count(),
            'promedio_calificaciones': curso.calificacion_promedio,
            'tasa_finalizacion': curso.tasa_finalizacion,
            'nivel_satisfaccion': curso.nivel_satisfaccion,
            'distribucion_calificaciones': Reseña.objects.filter(curso=curso).values('calificacion').annotate(count=Count('calificacion')),
        }
        return Response(estadisticas)

class TemaViewSet(viewsets.ModelViewSet):
    queryset = Tema.objects.all()
    serializer_class = TemaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def marcar_completado(self, request, pk=None):
        tema = self.get_object()
        usuario = request.user
        tema_completado, created = TemaCompletado.objects.get_or_create(usuario=usuario, tema=tema)
        if created:
            return Response({'status': 'Tema marcado como completado'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'El tema ya estaba marcado como completado'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def progreso(self, request, pk=None):
        tema = self.get_object()
        usuario = request.user
        progreso = tema.calcular_progreso(usuario)
        return Response({'progreso': progreso})

class CalificarCursoView(generics.CreateAPIView):
    serializer_class = ReseñaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        curso_id = self.kwargs['curso_id']
        curso = get_object_or_404(Curso, id=curso_id)
        
        if not (1 <= serializer.validated_data['calificacion'] <= 5):
            raise ValidationError("La calificación debe estar entre 1 y 5.")

        serializer.save(usuario=self.request.user, curso=curso)
        curso.calcular_promedio_calificaciones()
        curso.calcular_nivel_satisfaccion()

class CalcularProgresoCursoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, curso_id):
        curso = get_object_or_404(Curso, id=curso_id)
        progreso = curso.calcular_progreso(request.user)
        return Response({'progreso': progreso})

class InscribirCursoView(generics.CreateAPIView):
    serializer_class = InscripcionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        curso_id = self.kwargs['curso_id']
        curso = get_object_or_404(Curso, id=curso_id)
        serializer.save(curso=curso, usuario=self.request.user)
        curso.profesor.actualizar_estadisticas()

class InscripcionesUsuarioView(generics.ListAPIView):
    serializer_class = InscripcionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return Inscripcion.objects.filter(usuario_id=user_id)

class InstructorViewSet(viewsets.ModelViewSet):
    queryset = Instructor.objects.all()
    serializer_class = InstructorSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        instructor = self.get_object()
        estadisticas = {
            'total_estudiantes': instructor.num_estudiantes,
            'promedio_calificacion': instructor.promedio_calificacion,
            'total_cursos': instructor.cursos_creados.count(),
            'cursos_por_categoria': instructor.cursos_creados.values('categoria__nombre').annotate(count=Count('id')),
        }
        return Response(estadisticas)

class CursoRecomendacionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        usuario = request.user
        cursos_inscritos = Curso.objects.filter(inscritos=usuario)
        categorias_interes = Categoria.objects.filter(cursos__in=cursos_inscritos).distinct()
        cursos_recomendados = Curso.objects.filter(categoria__in=categorias_interes).exclude(inscritos=usuario).order_by('-calificacion_promedio')[:5]
        serializer = CursoSerializer(cursos_recomendados, many=True, context={'request': request})
        return Response(serializer.data)
    






    # *****************************************************************




class CursoDetallesView(generics.RetrieveAPIView):
    queryset = Curso.objects.all()
    serializer_class = CursoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

class VerificarInscripcionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        curso = get_object_or_404(Curso, pk=pk)
        inscrito = Inscripcion.objects.filter(usuario=request.user, curso=curso).exists()
        return Response({'inscrito': inscrito})

class CursoEstadisticasView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        curso = get_object_or_404(Curso, pk=pk)
        estadisticas = {
            'total_inscritos': curso.inscritos.count(),
            'promedio_calificaciones': curso.calificacion_promedio if curso.calificacion_promedio is not None else 0,
            'tasa_finalizacion': curso.tasa_finalizacion if curso.tasa_finalizacion is not None else 0,
            'nivel_satisfaccion': curso.nivel_satisfaccion if curso.nivel_satisfaccion is not None else 0,
            'distribucion_calificaciones': list(Reseña.objects.filter(curso=curso).values('calificacion').annotate(count=Count('calificacion'))),
        }
        return Response(estadisticas)

class CursoProgresoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        curso = get_object_or_404(Curso, pk=pk)
        progreso = curso.calcular_progreso(request.user)
        return Response({'progreso': progreso})



class TemaCompletadoList(generics.ListAPIView):
    serializer_class = TemaCompletadoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        usuario_id = self.request.query_params.get('usuario')
        if usuario_id:
            return TemaCompletado.objects.filter(usuario_id=usuario_id)
        return TemaCompletado.objects.all()



class CursoDetailView(generics.RetrieveAPIView):
    queryset = Curso.objects.all()
    serializer_class = CursoDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'pk'
