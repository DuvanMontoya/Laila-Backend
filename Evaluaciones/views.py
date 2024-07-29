from rest_framework import viewsets, status, generics, filters
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from .models import Evaluacion, Pregunta, RespuestaPregunta, IntentoEvaluacion, ResultadoEvaluacion, Tag, Opcion, Competencia, ContenidoMatematico, EstadisticasEvaluacion
from .serializers import *
from django.core.exceptions import MultipleObjectsReturned
from rest_framework.views import APIView
import logging
from rest_framework.decorators import action, api_view, permission_classes
from django.core.cache import cache
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
from django.db.models import Count, Avg, Sum, F, ExpressionWrapper, fields, Q
from django.db.models import Max, Min
from django.db.models.functions import TruncDate


logger = logging.getLogger(__name__)

class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

class EvaluacionViewSet(BaseViewSet):
    queryset = Evaluacion.objects.all()
    serializer_class = EvaluacionSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['titulo', 'descripcion']
    ordering_fields = ['fecha_inicio', 'fecha_fin', 'puntaje_maximo']

    def get_queryset(self):
        if self.request.user.is_staff:
            return Evaluacion.objects.all()
        return Evaluacion.objects.filter(usuarios_permitidos=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        evaluacion = self.get_object()
        if not evaluacion.usuarios_permitidos.filter(id=request.user.id).exists() and not request.user.is_staff:
            raise PermissionDenied(_("No tienes permiso para acceder a esta evaluación."))

        intentos_usuario = IntentoEvaluacion.objects.filter(evaluacion=evaluacion, usuario=request.user)
        intentos_realizados = intentos_usuario.count()
        mejor_intento = intentos_usuario.order_by('-puntaje_obtenido').first()

        serializer = self.get_serializer(evaluacion, context={'request': request})
        data = serializer.data
        data.update({
            'intentos_realizados': intentos_realizados,
            'mejor_intento': IntentoEvaluacionSerializer(mejor_intento).data if mejor_intento else None
        })

        return Response(data)

    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        evaluacion = self.get_object()
        if not request.user.is_staff:
            raise PermissionDenied(_("No tienes permiso para acceder a las estadísticas de esta evaluación."))
        
        estadisticas, _ = EstadisticasEvaluacion.objects.get_or_create(evaluacion=evaluacion)
        serializer = EstadisticasEvaluacionSerializer(estadisticas)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def distribucion_puntajes(self, request, pk=None):
        evaluacion = self.get_object()
        if not request.user.is_staff:
            raise PermissionDenied(_("No tienes permiso para acceder a esta información."))
        
        intentos = IntentoEvaluacion.objects.filter(evaluacion=evaluacion, completado=True)
        distribucion = intentos.values('puntaje_obtenido').annotate(count=Count('id')).order_by('puntaje_obtenido')
        
        return Response(list(distribucion))

    @action(detail=True, methods=['get'])
    def rendimiento_por_competencia(self, request, pk=None):
        evaluacion = self.get_object()
        if not request.user.is_staff:
            raise PermissionDenied(_("No tienes permiso para acceder a esta información."))
        
        rendimiento = RespuestaPregunta.objects.filter(intento__evaluacion=evaluacion)\
            .values('pregunta__competencia__nombre')\
            .annotate(
                total_puntos=Sum('pregunta__puntos'),
                puntos_obtenidos=Sum('puntos_obtenidos')
            )\
            .annotate(
                porcentaje=ExpressionWrapper(
                    F('puntos_obtenidos') * 100.0 / F('total_puntos'),
                    output_field=fields.FloatField()
                )
            )
        
        return Response(list(rendimiento))

    @action(detail=True, methods=['get'])
    def rendimiento_por_contenido(self, request, pk=None):
        evaluacion = self.get_object()
        if not request.user.is_staff:
            raise PermissionDenied(_("No tienes permiso para acceder a esta información."))
        
        rendimiento = RespuestaPregunta.objects.filter(intento__evaluacion=evaluacion)\
            .values('pregunta__contenido_matematico__categoria', 'pregunta__contenido_matematico__nombre')\
            .annotate(
                total_puntos=Sum('pregunta__puntos'),
                puntos_obtenidos=Sum('puntos_obtenidos')
            )\
            .annotate(
                porcentaje=ExpressionWrapper(
                    F('puntos_obtenidos') * 100.0 / F('total_puntos'),
                    output_field=fields.FloatField()
                )
            )
        
        return Response(list(rendimiento))

    @action(detail=True, methods=['get'])
    def rendimiento_por_situacion(self, request, pk=None):
        evaluacion = self.get_object()
        if not request.user.is_staff:
            raise PermissionDenied(_("No tienes permiso para acceder a esta información."))
        
        rendimiento = RespuestaPregunta.objects.filter(intento__evaluacion=evaluacion)\
            .values('pregunta__situacion')\
            .annotate(
                total_puntos=Sum('pregunta__puntos'),
                puntos_obtenidos=Sum('puntos_obtenidos')
            )\
            .annotate(
                porcentaje=ExpressionWrapper(
                    F('puntos_obtenidos') * 100.0 / F('total_puntos'),
                    output_field=fields.FloatField()
                )
            )
        
        return Response(list(rendimiento))

    @action(detail=True, methods=['get'])
    def analisis_tiempo(self, request, pk=None):
        evaluacion = self.get_object()
        if not request.user.is_staff:
            raise PermissionDenied(_("No tienes permiso para acceder a esta información."))
        
        analisis = IntentoEvaluacion.objects.filter(evaluacion=evaluacion, completado=True)\
            .annotate(
                tiempo_tomado=ExpressionWrapper(
                    F('fecha_fin') - F('fecha_inicio'),
                    output_field=fields.DurationField()
                )
            )\
            .aggregate(
                tiempo_promedio=Avg('tiempo_tomado'),
                tiempo_minimo=Min('tiempo_tomado'),
                tiempo_maximo=Max('tiempo_tomado')
            )
        
        return Response(analisis)

class PreguntaViewSet(BaseViewSet):
    queryset = Pregunta.objects.all()
    serializer_class = PreguntaSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['texto_pregunta', 'categoria']
    ordering_fields = ['dificultad', 'puntos', 'fecha_creacion']

    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        pregunta = self.get_object()
        estadisticas = RespuestaPregunta.objects.filter(pregunta=pregunta)\
            .aggregate(
                total_respuestas=Count('id'),
                respuestas_correctas=Count('id', filter=Q(es_correcta=True)),
                puntaje_promedio=Avg('puntos_obtenidos')
            )
        estadisticas['porcentaje_acierto'] = (estadisticas['respuestas_correctas'] / estadisticas['total_respuestas']) * 100 if estadisticas['total_respuestas'] > 0 else 0
        return Response(estadisticas)

class RespuestaPreguntaViewSet(BaseViewSet):
    queryset = RespuestaPregunta.objects.all()
    serializer_class = RespuestaPreguntaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return RespuestaPregunta.objects.all()
        return RespuestaPregunta.objects.filter(usuario=self.request.user)

class IntentoEvaluacionViewSet(BaseViewSet):
    queryset = IntentoEvaluacion.objects.select_related('evaluacion', 'usuario').all()
    serializer_class = IntentoEvaluacionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['fecha_inicio', 'puntaje_obtenido']

    def get_queryset(self):
        if self.request.user.is_staff:
            return IntentoEvaluacion.objects.all()
        return IntentoEvaluacion.objects.filter(usuario=self.request.user)

    def list(self, request, *args, **kwargs):
        user = request.user
        cache_key = f'intentos_usuario_{user.id}'
        intentos = cache.get_or_set(cache_key, self.get_queryset(), timeout=300)

        serializer = self.get_serializer(intentos, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        intento = self.get_object()
        if intento.usuario != request.user and not request.user.is_staff:
            return Response({'detail': _("No tienes permiso para acceder a este intento.")}, status=status.HTTP_403_FORBIDDEN)
        return Response(self.get_serializer(intento).data)

    def create(self, request, *args, **kwargs):
        evaluacion_id = request.data.get('evaluacion')
        evaluacion = get_object_or_404(Evaluacion, pk=evaluacion_id)
        if not evaluacion.usuarios_permitidos.filter(id=request.user.id).exists():
            return Response({'detail': _("No tienes permiso para iniciar esta evaluación.")}, status=status.HTTP_403_FORBIDDEN)
        
        intentos_previos = IntentoEvaluacion.objects.filter(evaluacion=evaluacion, usuario=request.user).count()
        if intentos_previos >= evaluacion.intentos_permitidos:
            return Response({'detail': _("Has alcanzado el número máximo de intentos permitidos.")}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance.usuario != request.user and not request.user.is_staff:
            return Response({'detail': _("No tienes permiso para modificar este intento.")}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.usuario != request.user and not request.user.is_staff:
            return Response({'detail': _("No tienes permiso para eliminar este intento.")}, status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)

        cache_key = f'intentos_usuario_{request.user.id}'
        cache.delete(cache_key)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def mis_intentos(self, request):
        intentos = IntentoEvaluacion.objects.filter(usuario=request.user)
        return Response(self.get_serializer(intentos, many=True).data)

    def perform_destroy(self, instance):
        instance.delete()
        logger.info(f'Intento de evaluación {instance.id} eliminado por el usuario {instance.usuario.id}')

    class Meta:
        unique_together = ('evaluacion', 'usuario', 'completado')
        verbose_name = _("Intento de Evaluación")
        verbose_name_plural = _("Intentos de Evaluaciones")

class ResultadoEvaluacionViewSet(BaseViewSet):
    queryset = ResultadoEvaluacion.objects.all()
    serializer_class = ResultadoEvaluacionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return ResultadoEvaluacion.objects.all()
        return ResultadoEvaluacion.objects.filter(usuario=self.request.user)

class TagViewSet(BaseViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class CompetenciaViewSet(BaseViewSet):
    queryset = Competencia.objects.all()
    serializer_class = CompetenciaSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class ContenidoMatematicoViewSet(BaseViewSet):
    queryset = ContenidoMatematico.objects.all()
    serializer_class = ContenidoMatematicoSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

class EvaluacionDetail(generics.RetrieveAPIView):
    queryset = Evaluacion.objects.all()
    serializer_class = EvaluacionSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj = super().get_object()
        if not obj.usuarios_permitidos.filter(id=self.request.user.id).exists() and not self.request.user.is_staff:
            raise PermissionDenied(_("No tienes permiso para acceder a esta evaluación."))
        return obj

    def get(self, request, *args, **kwargs):
        evaluacion = self.get_object()
        intentos_usuario = IntentoEvaluacion.objects.filter(evaluacion=evaluacion, usuario=request.user)
        intentos_realizados = intentos_usuario.count()

        logger.debug(f"Evaluacion ID: {evaluacion.id}, Usuario: {request.user.id}, Intentos encontrados: {intentos_realizados}")

        data = self.get_serializer(evaluacion).data
        data['intentos_realizados'] = intentos_realizados

        return Response(data)

class SubmitEvaluacionView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        evaluacion = get_object_or_404(Evaluacion, pk=kwargs.get('pk'))
        usuario = request.user
        if not evaluacion.usuarios_permitidos.filter(id=usuario.id).exists():
            raise PermissionDenied(_("No tienes permiso para enviar esta evaluación."))

        respuestas_data = request.data.get('respuestas', {})
        intento = IntentoEvaluacion.objects.create(evaluacion=evaluacion, usuario=usuario, fecha_inicio=timezone.now())

        puntaje_total = 0
        for pregunta_id, respuesta in respuestas_data.items():
            pregunta = get_object_or_404(Pregunta, id=pregunta_id)
            es_correcta, puntos_obtenidos = self.evaluar_respuesta(pregunta, respuesta)
            RespuestaPregunta.objects.create(
                pregunta=pregunta, usuario=usuario, intento=intento,
                respuesta=respuesta, es_correcta=es_correcta, puntos_obtenidos=puntos_obtenidos
            )
            puntaje_total += puntos_obtenidos

        intento.puntaje_obtenido = puntaje_total
        intento.completado = True
        intento.fecha_fin = timezone.now()
        intento.save()

        resultado, _ = ResultadoEvaluacion.objects.get_or_create(evaluacion=evaluacion, usuario=usuario)
        resultado.intentos.add(intento)
        resultado.actualizar_mejor_intento()

        return Response({
            'message': 'Evaluación enviada correctamente', 
            'puntaje_total': puntaje_total,
            'porcentaje': (puntaje_total / evaluacion.puntaje_maximo) * 100 if evaluacion.puntaje_maximo else 0,
            'aprobado': puntaje_total >= evaluacion.criterios_aprobacion if evaluacion.criterios_aprobacion else None
        }, status=status.HTTP_200_OK)

    def evaluar_respuesta(self, pregunta, respuesta):
        es_correcta = False
        puntos_obtenidos = 0
        if pregunta.tipo_pregunta == Pregunta.TipoPreguntaChoices.SIMPLE:
            opcion = Opcion.objects.filter(id=respuesta).first()
            es_correcta = opcion.es_correcta if opcion else False
            puntos_obtenidos = opcion.puntos if es_correcta else 0
        elif pregunta.tipo_pregunta == Pregunta.TipoPreguntaChoices.MULTIPLE:
            opciones = Opcion.objects.filter(id__in=respuesta)
            es_correcta = all(opcion.es_correcta for opcion in opciones)
            puntos_obtenidos = sum(opcion.puntos for opcion in opciones if opcion.es_correcta)
        elif pregunta.tipo_pregunta == Pregunta.TipoPreguntaChoices.VERDADERO_FALSO:
            opcion = Opcion.objects.filter(pregunta=pregunta, es_correcta=bool(respuesta)).first()
            es_correcta = opcion.es_correcta if opcion else False
            puntos_obtenidos = opcion.puntos if es_correcta else 0
        elif pregunta.tipo_pregunta == Pregunta.TipoPreguntaChoices.ABIERTA:
            es_correcta = True
            puntos_obtenidos = pregunta.puntos
        return es_correcta, puntos_obtenidos




import logging

logger = logging.getLogger(__name__)

import logging

logger = logging.getLogger(__name__)

class ResultadosEvaluacionView(EvaluacionDetail):
    def get(self, request, *args, **kwargs):
        evaluacion = self.get_object()
        if not evaluacion.resultados_visibles and not request.user.is_staff:
            return Response({'message': 'No tienes permiso para ver los resultados de esta evaluación.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            intentos_usuario = IntentoEvaluacion.objects.filter(evaluacion=evaluacion, usuario=request.user).order_by('-puntaje_obtenido')
            mejor_intento = intentos_usuario.first() if intentos_usuario.exists() else None

            resultados = {
                'intentos': IntentoEvaluacionSerializer(intentos_usuario, many=True).data,
                'mejor_intento': IntentoEvaluacionSerializer(mejor_intento).data if mejor_intento else None,
                'mostrar_opciones_correctas': evaluacion.mostrar_opciones_correctas
            }

            if request.user.is_staff:
                try:
                    estadisticas = EstadisticasEvaluacion.objects.get(evaluacion=evaluacion)
                    resultados['estadisticas'] = EstadisticasEvaluacionSerializer(estadisticas).data
                except EstadisticasEvaluacion.DoesNotExist:
                    resultados['estadisticas'] = None

            # Fetch additional data if needed
            resultados['rendimiento_por_competencia'] = [
                {
                    'competencia': res.pregunta.competencia.nombre if res.pregunta.competencia else 'N/A',
                    'porcentaje': (res.puntos_obtenidos / res.pregunta.puntos) * 100 if res.pregunta.puntos > 0 else 0
                }
                for res in RespuestaPregunta.objects.filter(intento__evaluacion=evaluacion)
            ]

            return Response(resultados, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error al obtener los resultados de la evaluación: {e}")
            return Response({'message': 'Ocurrió un error al cargar los resultados. Por favor, intenta nuevamente más tarde.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class EvaluacionList(generics.ListCreateAPIView):
    queryset = Evaluacion.objects.all()
    serializer_class = EvaluacionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['titulo', 'descripcion']
    ordering_fields = ['fecha_inicio', 'fecha_fin', 'puntaje_maximo']   

    def get_queryset(self):
        if self.request.user.is_staff:
            return Evaluacion.objects.all()
        return Evaluacion.objects.filter(usuarios_permitidos=self.request.user)

    def perform_create(self, serializer):
        serializer.save(creador=self.request.user)

    def create(self, request, *args, **kwargs):
        if request.user.is_staff:
            return super().create(request, *args, **kwargs)
        raise PermissionDenied(_("No tienes permiso para crear evaluaciones."))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

class PreguntaList(generics.ListCreateAPIView):
    queryset = Pregunta.objects.all()
    serializer_class = PreguntaSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['texto_pregunta', 'categoria']
    ordering_fields = ['dificultad', 'puntos', 'fecha_creacion']

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def iniciar_evaluacion(request, evaluacion_id):
    evaluacion = get_object_or_404(Evaluacion, pk=evaluacion_id)
    if not evaluacion.usuarios_permitidos.filter(id=request.user.id).exists():
        raise PermissionDenied(_("No tienes permiso para iniciar esta evaluación."))
    
    intentos_previos = IntentoEvaluacion.objects.filter(evaluacion=evaluacion, usuario=request.user).count()
    if intentos_previos >= evaluacion.intentos_permitidos:
        return Response({'message': 'Has alcanzado el número máximo de intentos permitidos.'}, status=status.HTTP_403_FORBIDDEN)
    
    intento = IntentoEvaluacion.objects.create(evaluacion=evaluacion, usuario=request.user, fecha_inicio=timezone.now())
    return Response({
        'id': intento.id, 
        'message': 'Evaluación iniciada correctamente',
        'tiempo_limite': evaluacion.tiempo_limite
    }, status=status.HTTP_200_OK)








@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enviar_evaluacion(request, evaluacion_id):
    import logging
    logger = logging.getLogger(__name__)

    logger.debug(f"Datos de la solicitud: {request.data}")

    evaluacion = get_object_or_404(Evaluacion, pk=evaluacion_id)
    usuario = request.user

    if not evaluacion.usuarios_permitidos.filter(id=usuario.id).exists():
        logger.warning("Permiso denegado para enviar la evaluación.")
        raise PermissionDenied(_("No tienes permiso para enviar esta evaluación."))

    respuestas_data = request.data.get('respuestas', {})
    if not respuestas_data:
        logger.warning("Datos de respuesta faltantes en la solicitud.")
        return Response({'detail': 'Datos de respuesta faltantes'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        intento = get_object_or_404(IntentoEvaluacion, evaluacion=evaluacion, usuario=usuario, completado=False)
    except MultipleObjectsReturned:
        intentos = IntentoEvaluacion.objects.filter(evaluacion=evaluacion, usuario=usuario, completado=False).order_by('-fecha_inicio')
        intento = intentos.first()
        intentos.exclude(pk=intento.pk).update(completado=True)  # Marca otros intentos como completados para evitar futuros conflictos

    puntaje_total = 0
    for pregunta_id, respuesta in respuestas_data.items():
        pregunta = get_object_or_404(Pregunta, id=pregunta_id)
        try:
            es_correcta, puntos_obtenidos = evaluar_respuesta(pregunta, respuesta)
        except TypeError:
            logger.error(f"Error al evaluar la respuesta para la pregunta {pregunta_id}.")
            return Response({'detail': 'Error al evaluar la respuesta'}, status=status.HTTP_400_BAD_REQUEST)
        RespuestaPregunta.objects.create(
            pregunta=pregunta, usuario=usuario, intento=intento,
            respuesta=respuesta, es_correcta=es_correcta, puntos_obtenidos=puntos_obtenidos
        )
        puntaje_total += puntos_obtenidos

    intento.puntaje_obtenido = puntaje_total
    intento.completado = True
    intento.estado = 'finalizado'
    intento.fecha_fin = timezone.now()
    intento.save()

    resultado, _ = ResultadoEvaluacion.objects.get_or_create(evaluacion=evaluacion, usuario=usuario)
    resultado.intentos.add(intento)
    resultado.actualizar_mejor_intento()

    estadisticas, _ = EstadisticasEvaluacion.objects.get_or_create(evaluacion=evaluacion)
    estadisticas.actualizar_estadisticas()

    return Response({
        'message': 'Evaluación enviada correctamente', 
        'puntaje_total': puntaje_total,
        'porcentaje': (puntaje_total / evaluacion.puntaje_maximo) * 100 if evaluacion.puntaje_maximo else 0,
        'aprobado': puntaje_total >= evaluacion.criterios_aprobacion if evaluacion.criterios_aprobacion is not None else None
    }, status=status.HTTP_200_OK)



# Función auxiliar para calcular el puntaje
def calcular_puntaje(evaluacion, respuestas):
    puntaje_total = 0
    for pregunta in evaluacion.preguntas.all():
        respuesta = respuestas.get(str(pregunta.id))
        if respuesta:
            if pregunta.tipo_pregunta == 'Simple':
                opcion = pregunta.opciones.filter(id=respuesta, es_correcta=True).first()
                if opcion:
                    puntaje_total += pregunta.puntos
            elif pregunta.tipo_pregunta == 'Múltiple':
                opciones_correctas = set(pregunta.opciones.filter(es_correcta=True).values_list('id', flat=True))
                if set(respuesta) == opciones_correctas:
                    puntaje_total += pregunta.puntos
            # Añadir lógica para otros tipos de preguntas según sea necesario
    return puntaje_total




def evaluar_respuesta(pregunta, respuesta):
    es_correcta = False
    puntos_obtenidos = 0

    if pregunta.tipo_pregunta == Pregunta.TipoPreguntaChoices.SIMPLE:
        opcion = Opcion.objects.filter(id=respuesta).first()
        if opcion:
            es_correcta = opcion.es_correcta
            puntos_obtenidos = opcion.puntos if es_correcta else 0

    elif pregunta.tipo_pregunta == Pregunta.TipoPreguntaChoices.MULTIPLE:
        if isinstance(respuesta, list):
            opciones = Opcion.objects.filter(id__in=respuesta)
            if opciones.exists():
                es_correcta = all(opcion.es_correcta for opcion in opciones)
                puntos_obtenidos = sum(opcion.puntos for opcion in opciones if opcion.es_correcta)

    elif pregunta.tipo_pregunta == Pregunta.TipoPreguntaChoices.VERDADERO_FALSO:
        if isinstance(respuesta, bool):
            opcion = Opcion.objects.filter(pregunta=pregunta, es_correcta=respuesta).first()
            if opcion:
                es_correcta = opcion.es_correcta
                puntos_obtenidos = opcion.puntos if es_correcta else 0

    elif pregunta.tipo_pregunta == Pregunta.TipoPreguntaChoices.ABIERTA:
        es_correcta = True
        puntos_obtenidos = pregunta.puntos

    
    if pregunta.tipo_pregunta == Pregunta.TipoPreguntaChoices.SIMPLE:
            opcion = Opcion.objects.filter(id=respuesta).first()
            es_correcta = opcion.es_correcta if opcion else False
            puntos_obtenidos = opcion.puntos if es_correcta else 0
    elif pregunta.tipo_pregunta == Pregunta.TipoPreguntaChoices.MULTIPLE:
            opciones = Opcion.objects.filter(id__in=respuesta)
            es_correcta = all(opcion.es_correcta for opcion in opciones)
            puntos_obtenidos = sum(opcion.puntos for opcion in opciones if opcion.es_correcta)
    elif pregunta.tipo_pregunta == Pregunta.TipoPreguntaChoices.VERDADERO_FALSO:
            opcion = Opcion.objects.filter(pregunta=pregunta, es_correcta=bool(respuesta)).first()
            es_correcta = opcion.es_correcta if opcion else False
            puntos_obtenidos = opcion.puntos if es_correcta else 0
    elif pregunta.tipo_pregunta == Pregunta.TipoPreguntaChoices.ABIERTA:
            es_correcta = True
            puntos_obtenidos = pregunta.puntos
    return es_correcta, puntos_obtenidos




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def obtener_intento(request, evaluacion_id):
    evaluacion = get_object_or_404(Evaluacion, pk=evaluacion_id)
    usuario = request.user
    if not evaluacion.usuarios_permitidos.filter(id=usuario.id).exists():
        return Response({'message': 'No tienes permiso para acceder a esta evaluación.'}, status=status.HTTP_403_FORBIDDEN)

    # Buscar intentos no completados
    intentos_no_completados = IntentoEvaluacion.objects.filter(
        evaluacion=evaluacion,
        usuario=usuario,
        completado=False
    ).order_by('-fecha_inicio')

    if intentos_no_completados.exists():
        # Si hay intentos no completados, tomar el más reciente
        intento = intentos_no_completados.first()
        # Opcionalmente, puedes marcar los otros intentos como completados
        intentos_no_completados.exclude(id=intento.id).update(completado=True)
    else:
        # Si no hay intentos no completados, crear uno nuevo
        intento = IntentoEvaluacion.objects.create(
            evaluacion=evaluacion,
            usuario=usuario,
            fecha_inicio=timezone.now(),
            estado='en_curso'
        )

    preguntas = [{'id': p.id, 'texto_pregunta': p.texto_pregunta, 'imagen_svg': p.imagen_svg.url if p.imagen_svg else None} for p in intento.evaluacion.preguntas.all()]

    return Response({
        'id': intento.id,
        'evaluacion': {
            'id': intento.evaluacion.id,
            'titulo': intento.evaluacion.titulo,
            'preguntas': preguntas,
        },
        'respuestas': intento.respuestas,
        'tiempo_restante': intento.tiempo_restante,
    }, status=status.HTTP_200_OK)





@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('upload'):
        image = request.FILES['upload']
        fs = FileSystemStorage()
        filename = fs.save(image.name, image)
        return JsonResponse({'url': fs.url(filename)})
    return JsonResponse({'error': 'Failed to upload image'}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def estadisticas_generales(request):
    total_evaluaciones = Evaluacion.objects.count()
    total_preguntas = Pregunta.objects.count()
    total_intentos = IntentoEvaluacion.objects.count()
    promedio_puntaje = IntentoEvaluacion.objects.filter(completado=True).aggregate(Avg('puntaje_obtenido'))['puntaje_obtenido__avg']
    
    return Response({
        'total_evaluaciones': total_evaluaciones,
        'total_preguntas': total_preguntas,
        'total_intentos': total_intentos,
        'promedio_puntaje': promedio_puntaje
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def tendencias_rendimiento(request):
    fecha_inicio = request.query_params.get('fecha_inicio')
    fecha_fin = request.query_params.get('fecha_fin')
    
    intentos = IntentoEvaluacion.objects.filter(completado=True)
    if fecha_inicio:
        intentos = intentos.filter(fecha_fin__gte=fecha_inicio)
    if fecha_fin:
        intentos = intentos.filter(fecha_fin__lte=fecha_fin)
    
    tendencias = intentos.annotate(fecha=TruncDate('fecha_fin')).values('fecha').annotate(
        promedio_puntaje=Avg('puntaje_obtenido'),
        total_intentos=Count('id')
    ).order_by('fecha')
    
    return Response(list(tendencias))

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil_usuario(request):
    usuario = request.user
    intentos = IntentoEvaluacion.objects.filter(usuario=usuario, completado=True)
    
    total_intentos = intentos.count()
    promedio_puntaje = intentos.aggregate(Avg('puntaje_obtenido'))['puntaje_obtenido__avg']
    evaluaciones_completadas = intentos.values('evaluacion').distinct().count()
    
    ultimos_intentos = intentos.order_by('-fecha_fin')[:5]
    
    return Response({
        'username': usuario.username,
        'email': usuario.email,
        'total_intentos': total_intentos,
        'promedio_puntaje': promedio_puntaje,
        'evaluaciones_completadas': evaluaciones_completadas,
        'ultimos_intentos': IntentoEvaluacionSerializer(ultimos_intentos, many=True).data
    })

class EvaluacionesPendientesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        evaluaciones = Evaluacion.objects.filter(
            usuarios_permitidos__id=user_id
        ).exclude(
            intento_evaluacion__usuario__id=user_id,
            intento_evaluacion__completado=True
        )
        serializer = EvaluacionSerializer(evaluaciones, many=True)
        return Response(serializer.data)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def iniciar_nuevo_intento(request, evaluacion_id):
    evaluacion = get_object_or_404(Evaluacion, pk=evaluacion_id)
    usuario = request.user

    # Verificar si el usuario tiene permiso para esta evaluación
    if not evaluacion.usuarios_permitidos.filter(id=usuario.id).exists():
        return Response({'error': 'No tienes permiso para iniciar esta evaluación.'}, status=status.HTTP_403_FORBIDDEN)

    # Verificar si el usuario ya ha alcanzado el límite de intentos
    intentos_previos = IntentoEvaluacion.objects.filter(evaluacion=evaluacion, usuario=usuario).count()
    if intentos_previos >= evaluacion.intentos_permitidos:
        return Response({'error': 'Has alcanzado el número máximo de intentos permitidos.'}, status=status.HTTP_403_FORBIDDEN)

    # Crear nuevo intento
    intento = IntentoEvaluacion.objects.create(
        evaluacion=evaluacion,
        usuario=usuario,
        estado='iniciado'
    )

    serializer = IntentoEvaluacionSerializer(intento)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finalizar_intento(request, intento_id):
    intento = get_object_or_404(IntentoEvaluacion, pk=intento_id)
    
    # Verificar que el intento pertenece al usuario actual
    if intento.usuario != request.user:
        return Response({'error': 'No tienes permiso para finalizar este intento.'}, status=status.HTTP_403_FORBIDDEN)

    # Verificar que el intento no haya sido finalizado ya
    if intento.estado == 'finalizado':
        return Response({'error': 'Este intento ya ha sido finalizado.'}, status=status.HTTP_400_BAD_REQUEST)

    # Procesar las respuestas
    respuestas = request.data.get('respuestas', {})
    puntaje_total = 0

    for pregunta_id, respuesta in respuestas.items():
        pregunta = get_object_or_404(Pregunta, id=pregunta_id)
        es_correcta, puntos_obtenidos = evaluar_respuesta(pregunta, respuesta)
        RespuestaPregunta.objects.create(
            intento=intento,
            pregunta=pregunta,
            respuesta=respuesta,
            es_correcta=es_correcta,
            puntos_obtenidos=puntos_obtenidos
        )
        puntaje_total += puntos_obtenidos

    # Actualizar el intento
    intento.puntaje_obtenido = puntaje_total
    intento.completado = True
    intento.estado = 'finalizado'
    intento.fecha_fin = timezone.now()
    intento.save()

    # Actualizar estadísticas y resultados
    actualizar_estadisticas_y_resultados(intento)

    serializer = IntentoEvaluacionSerializer(intento)
    return Response(serializer.data)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def guardar_respuestas_temporales(request, intento_id):
    import logging
    logger = logging.getLogger(__name__)

    logger.debug(f"Datos de la solicitud: {request.data}")

    intento = get_object_or_404(IntentoEvaluacion, pk=intento_id, usuario=request.user)

    
    # Verificar que el intento pertenece al usuario actual
    if intento.usuario != request.user:
        logger.warning("Permiso denegado para modificar el intento.")
        return Response({'error': 'No tienes permiso para modificar este intento.'}, status=status.HTTP_403_FORBIDDEN)

    # Verificar que el intento esté en curso
    if intento.estado != 'en_curso':
        logger.warning("El intento no está en curso.")
        return Response({'error': 'No se pueden guardar respuestas para un intento que no está en curso.'}, status=status.HTTP_400_BAD_REQUEST)

    # Guardar las respuestas temporales
    respuestas = request.data.get('respuestas', {})
    if not respuestas:
        logger.warning("Datos de respuesta faltantes en la solicitud.")
        return Response({'error': 'Datos de respuesta faltantes'}, status=status.HTTP_400_BAD_REQUEST)

    intento.respuestas = respuestas
    intento.save()

    logger.info("Respuestas guardadas temporalmente con éxito.")
    return Response({'message': 'Respuestas guardadas temporalmente con éxito.'})




def actualizar_estadisticas_y_resultados(intento):
    # Implementa la lógica para actualizar las estadísticas de la evaluación
    # y los resultados del usuario
    pass