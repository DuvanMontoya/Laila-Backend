from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from .models import Evaluacion, Pregunta, RespuestaPregunta, IntentoEvaluacion, ResultadoEvaluacion, Tag, Opcion
from .serializers import (
    EvaluacionSerializer, PreguntaSerializer, RespuestaPreguntaSerializer,
    IntentoEvaluacionSerializer, ResultadoEvaluacionSerializer, TagSerializer
)
import logging
from rest_framework.decorators import action, api_view
from django.core.cache import cache
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage

logger = logging.getLogger(__name__)

class BaseViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

class EvaluacionViewSet(BaseViewSet):
    queryset = Evaluacion.objects.all()
    serializer_class = EvaluacionSerializer

    def get_queryset(self):
        return Evaluacion.objects.filter(usuarios_permitidos=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        evaluacion = self.get_object()
        if not evaluacion.usuarios_permitidos.filter(id=request.user.id).exists():
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

class PreguntaViewSet(BaseViewSet):
    queryset = Pregunta.objects.all()
    serializer_class = PreguntaSerializer

class RespuestaPreguntaViewSet(BaseViewSet):
    queryset = RespuestaPregunta.objects.all()
    serializer_class = RespuestaPreguntaSerializer

class IntentoEvaluacionViewSet(BaseViewSet):
    queryset = IntentoEvaluacion.objects.select_related('evaluacion', 'usuario').all()
    serializer_class = IntentoEvaluacionSerializer

    def list(self, request, *args, **kwargs):
        user = request.user
        cache_key = f'intentos_usuario_{user.id}'
        intentos = cache.get_or_set(cache_key, IntentoEvaluacion.objects.filter(usuario=user), timeout=300)

        serializer = self.get_serializer(intentos, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        intento = self.get_object()
        if intento.usuario != request.user:
            return Response({'detail': _("No tienes permiso para acceder a este intento.")}, status=status.HTTP_403_FORBIDDEN)
        return Response(self.get_serializer(intento).data)

    def create_update_destroy(self, request, *args, **kwargs):
        instance = kwargs.pop('instance', None)
        user = request.user
        data = request.data
        partial = kwargs.pop('partial', False)

        if instance and instance.usuario != user:
            return Response({'detail': _("No tienes permiso para modificar este intento.")}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(instance or data, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save(usuario=user if not instance else None)

        cache_key = f'intentos_usuario_{user.id}'
        cache.delete(cache_key)

        return Response(serializer.data, status=status.HTTP_201_CREATED if not instance else status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        return self.create_update_destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return self.create_update_destroy(request, *args, **kwargs, instance=self.get_object())

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.usuario != request.user:
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

class ResultadoEvaluacionViewSet(BaseViewSet):
    queryset = ResultadoEvaluacion.objects.all()
    serializer_class = ResultadoEvaluacionSerializer

class TagViewSet(BaseViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class EvaluacionDetail(generics.RetrieveAPIView):
    queryset = Evaluacion.objects.all()
    serializer_class = EvaluacionSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj = super().get_object()
        if not obj.usuarios_permitidos.filter(id=self.request.user.id).exists():
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
    def post(self, request, *args, **kwargs):
        evaluacion = get_object_or_404(Evaluacion, pk=kwargs.get('pk'))
        usuario = request.user
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
        resultado.puntaje_total = puntaje_total
        resultado.save()

        return Response({'message': 'Evaluación enviada correctamente', 'puntaje_total': puntaje_total}, status=status.HTTP_200_OK)

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

class ResultadosEvaluacionView(EvaluacionDetail):
    def get(self, request, *args, **kwargs):
        evaluacion = self.get_object()
        if not evaluacion.resultados_visibles:
            return Response({'message': 'No tienes permiso para ver los resultados de esta evaluación.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            intentos_usuario = IntentoEvaluacion.objects.filter(evaluacion=evaluacion, usuario=request.user).order_by('-puntaje_obtenido')
            mejor_intento = intentos_usuario.first() if intentos_usuario.exists() else None

            resultados = {
            'intentos': IntentoEvaluacionSerializer(intentos_usuario, many=True).data,
            'mejor_intento': IntentoEvaluacionSerializer(mejor_intento).data if mejor_intento else None,
            'mostrar_opciones_correctas': evaluacion.mostrar_opciones_correctas
        }

            return Response(resultados, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error al obtener los resultados de la evaluación: {e}")
            return Response({'message': 'Ocurrió un error al cargar los resultados. Por favor, intenta nuevamente más tarde.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EvaluacionList(generics.ListCreateAPIView):
    queryset = Evaluacion.objects.all()
    serializer_class = EvaluacionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Evaluacion.objects.filter(usuarios_permitidos=self.request.user)

    def perform_create(self, serializer):
        serializer.save(creador=self.request.user)

    def create(self, request, *args, **kwargs):
        if request.user.is_staff:
            return super().create(request, *args, **kwargs)
        raise PermissionDenied(_("No tienes permiso para crear evaluaciones."))

    def list(self, request, *args, **kwargs):
        if request.user.is_staff:
            return super().list(request, *args, **kwargs)
        raise PermissionDenied(_("No tienes permiso para ver evaluaciones."))

class PreguntaList(EvaluacionList):
    queryset = Pregunta.objects.all()
    serializer_class = PreguntaSerializer

@api_view(['POST'])
def iniciar_evaluacion(request, evaluacion_id):
    evaluacion = get_object_or_404(Evaluacion, pk=evaluacion_id)
    if not evaluacion.usuarios_permitidos.filter(id=request.user.id).exists():
        raise PermissionDenied(_("No tienes permiso para iniciar esta evaluación."))
    intento = IntentoEvaluacion.objects.create(evaluacion=evaluacion, usuario=request.user, fecha_inicio=timezone.now())
    return Response({'id': intento.id, 'message': 'Evaluación iniciada correctamente'}, status=status.HTTP_200_OK)

@api_view(['POST'])
def enviar_evaluacion(request, evaluacion_id):
    evaluacion = get_object_or_404(Evaluacion, pk=evaluacion_id)
    usuario = request.user
    if not evaluacion.usuarios_permitidos.filter(id=usuario.id).exists():
        raise PermissionDenied(_("No tienes permiso para enviar esta evaluación."))

    respuestas_data = request.data.get('respuestas', {})
    intento = get_object_or_404(IntentoEvaluacion, evaluacion=evaluacion, usuario=usuario, completado=False)

    puntaje_total = 0
    for pregunta_id, respuesta in respuestas_data.items():
        pregunta = get_object_or_404(Pregunta, id=pregunta_id)
        es_correcta, puntos_obtenidos = evaluar_respuesta(pregunta, respuesta)
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
    resultado.puntaje_total = puntaje_total
    resultado.save()

    return Response({'message': 'Evaluación enviada correctamente', 'puntaje_total': puntaje_total}, status=status.HTTP_200_OK)

def evaluar_respuesta(pregunta, respuesta):
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

@api_view(['GET'])
def obtener_intento(request, evaluacion_id):
    evaluacion = get_object_or_404(Evaluacion, pk=evaluacion_id)
    usuario = request.user
    if not evaluacion.usuarios_permitidos.filter(id=usuario.id).exists():
        return Response({'message': 'No tienes permiso para acceder a esta evaluación.'}, status=status.HTTP_403_FORBIDDEN)

    intentos = IntentoEvaluacion.objects.filter(evaluacion=evaluacion, usuario=usuario).order_by('-fecha_inicio')
    mejor_intento = intentos.filter(completado=True).order_by('-puntaje_obtenido').first()
    intento_activo = intentos.filter(completado=False).first()
    if not intento_activo:
        intento_activo = IntentoEvaluacion.objects.create(evaluacion=evaluacion, usuario=usuario, fecha_inicio=timezone.now())

    preguntas = [{'id': p.id, 'texto_pregunta': p.texto_pregunta, 'imagen_svg': p.imagen_svg if p.imagen_svg else None} for p in intento_activo.evaluacion.preguntas.all()]

    return Response({
        'id': intento_activo.id,
        'evaluacion': {
            'id': intento_activo.evaluacion.id,
            'titulo': intento_activo.evaluacion.titulo,
            'preguntas': preguntas,
        },
        'respuestas': intento_activo.respuestas,
        'tiempo_restante': intento_activo.tiempo_restante,
        'mejor_intento': {
            'puntaje_obtenido': mejor_intento.puntaje_obtenido if mejor_intento else 0,
            'porcentaje_puntaje': mejor_intento.porcentaje_puntaje if mejor_intento else 0,
            'aprobacion': mejor_intento.aprobacion if mejor_intento else False,
        } if mejor_intento else None,
    }, status=status.HTTP_200_OK)

@csrf_exempt
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('upload'):
        image = request.FILES['upload']
        fs = FileSystemStorage()
        filename = fs.save(image.name, image)
        return JsonResponse({'url': fs.url(filename)})
    return JsonResponse({'error': 'Failed to upload image'}, status=400)
