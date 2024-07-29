from rest_framework import serializers
from .models import Evaluacion, Pregunta, Opcion, RespuestaPregunta, IntentoEvaluacion, ResultadoEvaluacion, Tag, Competencia, ContenidoMatematico, EstadisticasEvaluacion
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class CompetenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competencia
        fields = '__all__'

class ContenidoMatematicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContenidoMatematico
        fields = '__all__'

class OpcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Opcion
        fields = ['id', 'texto_opcion', 'es_correcta', 'puntos']






class PreguntaSerializer(serializers.ModelSerializer):
    opciones = OpcionSerializer(many=True, read_only=True)
    competencia = CompetenciaSerializer(read_only=True)
    contenido_matematico = ContenidoMatematicoSerializer(read_only=True)
    # imagen_svg = serializers.SerializerMethodField()

    class Meta:
        model = Pregunta
        fields = ['id', 'texto_pregunta', 'tipo_pregunta', 'imagen_svg', 'puntos', 'opciones', 'dificultad', 'categoria', 'tiempo_estimado', 'marcar_respuesta', 'competencia', 'contenido_matematico', 'situacion']

class RespuestaPreguntaSerializer(serializers.ModelSerializer):
    pregunta = PreguntaSerializer(read_only=True)
    usuario = UserSerializer(read_only=True)
    opcion_seleccionada = serializers.SerializerMethodField()
    opcion_correcta = serializers.SerializerMethodField()

    class Meta:
        model = RespuestaPregunta
        fields = ['id', 'pregunta', 'usuario', 'intento', 'respuesta', 'es_correcta', 'puntos_obtenidos', 'opcion_seleccionada', 'opcion_correcta']

    def get_opcion_seleccionada(self, obj):
        return obj.respuesta

    def get_opcion_correcta(self, obj):
        return next((opcion.id for opcion in obj.pregunta.opciones.all() if opcion.es_correcta), None)



class IntentoEvaluacionSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)
    respuestas = serializers.SerializerMethodField()
    tiempo_tomado = serializers.SerializerMethodField()
    porcentaje_puntaje = serializers.FloatField(read_only=True)
    aprobacion = serializers.BooleanField(read_only=True)
    preguntas = PreguntaSerializer(many=True, read_only=True, source='evaluacion.preguntas')


    class Meta:
        model = IntentoEvaluacion
        fields = ['id', 'evaluacion', 'usuario', 'fecha_inicio', 'fecha_fin', 'puntaje_obtenido', 
                  'respuestas', 'completado', 'estado', 'preguntas', 'porcentaje_puntaje', 
                  'aprobacion', 'tiempo_tomado']

    

    def get_tiempo_tomado(self, obj):
        if obj.fecha_inicio and obj.fecha_fin:
            return (obj.fecha_fin - obj.fecha_inicio).total_seconds()
        return None

    def get_respuestas(self, obj):
        respuestas = RespuestaPregunta.objects.filter(intento=obj).prefetch_related('pregunta', 'pregunta__opciones')
        serializer = RespuestaPreguntaSerializer(respuestas, many=True)
        return serializer.data






class ResultadoEvaluacionSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)
    intentos = IntentoEvaluacionSerializer(many=True, read_only=True)
    mejor_intento = IntentoEvaluacionSerializer(read_only=True)

    class Meta:
        model = ResultadoEvaluacion
        fields = '__all__'

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'

class EstadisticasEvaluacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadisticasEvaluacion
        fields = '__all__'

class EvaluacionSerializer(serializers.ModelSerializer):
    intentos_realizados = serializers.SerializerMethodField()
    preguntas = PreguntaSerializer(many=True, read_only=True)
    resultados = ResultadoEvaluacionSerializer(many=True, read_only=True)
    usuarios_permitidos = UserSerializer(many=True, read_only=True)
    puntaje_maximo = serializers.SerializerMethodField()
    estadisticas = EstadisticasEvaluacionSerializer(read_only=True)

    class Meta:
        model = Evaluacion
        fields = '__all__'

    def get_intentos_realizados(self, obj):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            return IntentoEvaluacion.objects.filter(evaluacion=obj, usuario=request.user).count()
        return 0

    def get_puntaje_maximo(self, obj):
        return sum(pregunta.puntos for pregunta in obj.preguntas.all())