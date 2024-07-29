from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q, F
from .models import Categoria, Curso, Tema, TemaCompletado, Reseña, Instructor, Progreso, Leccion, LeccionCompletada
from Matriculas.models import Inscripcion
from .serializers import *
from django.contrib.auth.models import User
from django.utils.translation import gettext as _
from rest_framework import serializers
from Lecciones.serializers import LeccionSerializer
from Articulos.permissions import IsOwnerOrReadOnly
from Matriculas.serializers import InscripcionSerializer



class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=True, methods=['get'])
    def cursos(self, request, pk=None):
        categoria = self.get_object()
        cursos = Curso.objects.filter(categoria=categoria, es_activo=True)
        serializer = CursoSerializer(cursos, many=True, context={'request': request})
        return Response(serializer.data)


class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.filter(es_activo=True)
    serializer_class = CursoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['list', 'create']:
            return CursoSerializer
        return CursoDetailSerializer

    def _check_enrollment(self, user, curso):
        return Inscripcion.objects.filter(usuario=user, curso=curso, estado='aprobada').exists()

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def detalles(self, request, pk=None):
        curso = self.get_object()
        user = request.user
        is_enrolled = self._check_enrollment(user, curso)
        curso_data = self.get_serializer(curso, context={'request': request}).data
        curso_data['esta_inscrito'] = is_enrolled
        if is_enrolled:
            progreso = Progreso.objects.get_or_create(usuario=user, curso=curso)[0]
            curso_data['progreso'] = progreso.porcentaje
        else:
            inscripcion = Inscripcion.objects.filter(usuario=user, curso=curso).first()
            curso_data['estado_inscripcion'] = inscripcion.estado if inscripcion else None
        return Response(curso_data)

    @action(detail=True, methods=['post'])
    def solicitar_inscripcion(self, request, pk=None):
        curso = self.get_object()
        user = request.user
        inscripcion, created = Inscripcion.objects.get_or_create(
            usuario=user,
            curso=curso,
            defaults={'estado': 'pendiente'}
        )
        if not created and inscripcion.estado == 'pendiente':
            return Response({'status': 'pendiente', 'message': 'Ya has solicitado inscripción a este curso.'}, status=status.HTTP_200_OK)
        
        inscripcion.estado = 'pendiente'
        inscripcion.save()
        return Response({'status': 'pendiente', 'message': 'Solicitud de inscripción enviada correctamente.'}, status=status.HTTP_201_CREATED)

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
    
    @action(detail=True, methods=['get'])
    def estado_inscripcion(self, request, pk=None):
        curso = self.get_object()
        user = request.user
        try:
            inscripcion = Inscripcion.objects.get(usuario=user, curso=curso)
            return Response({'status': inscripcion.estado})
        except Inscripcion.DoesNotExist:
            return Response({'status': 'no_inscrito'})


class TemaViewSet(viewsets.ModelViewSet):
    queryset = Tema.objects.all()
    serializer_class = TemaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        curso_id = self.request.query_params.get('curso', None)
        if curso_id is not None:
            queryset = queryset.filter(curso_id=curso_id)
        return queryset

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def marcar_completado(self, request, pk=None):
        tema = self.get_object()
        usuario = request.user
        tema_completado, created = TemaCompletado.objects.get_or_create(usuario=usuario, tema=tema)
        if created:
            Progreso.objects.filter(usuario=usuario, curso=tema.curso).update(porcentaje=F('porcentaje') + tema.porcentaje_curso)
            return Response({'status': 'Tema marcado como completado'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'El tema ya estaba marcado como completado'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def progreso(self, request, pk=None):
        tema = self.get_object()
        progreso = tema.calcular_progreso(request.user)
        return Response({'progreso': progreso})

class CalificarCursoView(generics.CreateAPIView):
    serializer_class = ReseñaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        curso_id = self.kwargs['curso_id']
        curso = get_object_or_404(Curso, id=curso_id)
        usuario = self.request.user
        
        # Verificar si el usuario está inscrito y ha completado al menos el 80% del curso
        inscripcion = get_object_or_404(Inscripcion, usuario=usuario, curso=curso, estado='aprobada')
        progreso = Progreso.objects.get(usuario=usuario, curso=curso)
        
        if progreso.porcentaje < 80:
            raise serializers.ValidationError("Debes completar al menos el 80% del curso para dejar una reseña.")
        
        if not (1 <= serializer.validated_data['calificacion'] <= 5):
            raise serializers.ValidationError("La calificación debe estar entre 1 y 5.")

        serializer.save(usuario=usuario, curso=curso)
        curso.actualizar_estadisticas()

class CalcularProgresoCursoView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, curso_id):
        curso = get_object_or_404(Curso, id=curso_id)
        progreso, created = Progreso.objects.get_or_create(usuario=request.user, curso=curso)
        if created:
            progreso.actualizar_progreso()
        return Response({'progreso': progreso.porcentaje})

class InscribirCursoView(generics.CreateAPIView):
    serializer_class = InscripcionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        curso_id = self.kwargs['curso_id']
        curso = get_object_or_404(Curso, id=curso_id)
        usuario = self.request.user
        inscripcion = serializer.save(curso=curso, usuario=usuario)
        if inscripcion.estado == 'aprobada':
            Progreso.objects.get_or_create(usuario=usuario, curso=curso)
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
        cursos_inscritos = Curso.objects.filter(inscripciones__usuario=usuario, inscripciones__estado='aprobada')
        categorias_interes = Categoria.objects.filter(cursos__in=cursos_inscritos).distinct()
        cursos_recomendados = Curso.objects.filter(categoria__in=categorias_interes, es_activo=True).exclude(inscripciones__usuario=usuario).order_by('-calificacion_promedio')[:5]
        serializer = CursoSerializer(cursos_recomendados, many=True, context={'request': request})
        return Response(serializer.data)

class CursoDetallesView(generics.RetrieveAPIView):
    queryset = Curso.objects.filter(es_activo=True)
    serializer_class = CursoDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    def get(self, request, *args, **kwargs):
        curso = self.get_object()
        usuario = request.user
        progreso_usuario = curso.calcular_progreso(usuario) if usuario.is_authenticated else 0

        response_data = self.get_serializer(curso).data
        response_data['progreso_usuario'] = progreso_usuario
        return Response(response_data)

class VerificarInscripcionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        curso = get_object_or_404(Curso, pk=pk)
        inscrito = Inscripcion.objects.filter(usuario=request.user, curso=curso, estado='aprobada').exists()
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
        progreso, created = Progreso.objects.get_or_create(usuario=request.user, curso=curso)
        if created:
            progreso.actualizar_progreso()
        return Response({'progreso': progreso.porcentaje})

class CursosMatriculadosView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        cursos = Curso.objects.filter(inscripciones__usuario=user, inscripciones__estado='aprobada', es_activo=True)
        serializer = CursoSerializer(cursos, many=True, context={'request': request})
        return Response(serializer.data)



class BuscarCursosView(generics.ListAPIView):
    serializer_class = CursoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Curso.objects.filter(es_activo=True)
        query = self.request.query_params.get('q', None)
        categoria = self.request.query_params.get('categoria', None)
        dificultad = self.request.query_params.get('dificultad', None)
        ordenar_por = self.request.query_params.get('ordenar_por', '-fecha_inicio')

        if query:
            queryset = queryset.filter(
                Q(titulo__icontains=query) |
                Q(descripcion__icontains=query) |
                Q(tags__nombre__icontains=query)
            ).distinct()

        if categoria:
            queryset = queryset.filter(categoria__slug=categoria)

        if dificultad:
            queryset = queryset.filter(dificultad=dificultad)

        return queryset.order_by(ordenar_por)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    



# ***********************************************


class TemaCompletadoList(generics.ListAPIView):
    serializer_class = TemaCompletadoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        usuario_id = self.request.query_params.get('usuario')
        if usuario_id:
            return TemaCompletado.objects.filter(usuario_id=usuario_id)
        return TemaCompletado.objects.all()