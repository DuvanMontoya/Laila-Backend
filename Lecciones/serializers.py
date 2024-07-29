from rest_framework import serializers
from .models import *
from Cursos.serializers import TemaSerializer
from Autenticacion.serializers import UserSerializer
from Evaluaciones.serializers import EvaluacionSerializer
from Evaluaciones.models import Evaluacion
from Cursos.models import Tema
from Tareas.serializers import TareaSerializer
from Tareas.models import Tarea




class LeccionSerializer(serializers.ModelSerializer):
    tema = serializers.PrimaryKeyRelatedField(queryset=Tema.objects.all())
    evaluacion_asociada = serializers.PrimaryKeyRelatedField(queryset=Evaluacion.objects.all(), allow_null=True)
    completada_por = UserSerializer(many=True, read_only=True)
    tareas = serializers.PrimaryKeyRelatedField(many=True, queryset=Tarea.objects.all())
    esta_completada = serializers.SerializerMethodField()
    tiempo_estimado_display = serializers.SerializerMethodField()

    class Meta:
        model = Leccion
        fields = '__all__'

    def get_esta_completada(self, obj):
        user = self.context['request'].user
        return obj.esta_completada_por(user)
    
    def get_tiempo_estimado_display(self, obj):
        return f"{obj.tiempo_estimado} min"

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['tiempo_estimado_display'] = self.get_tiempo_estimado_display(instance)
        return ret




class LeccionDetallesSerializer(serializers.ModelSerializer):
    tema = TemaSerializer()
    evaluacion_asociada = EvaluacionSerializer()
    completada_por = UserSerializer(many=True)
    tareas = TareaSerializer(many=True)
    esta_completada = serializers.SerializerMethodField()

    class Meta:
        model = Leccion
        fields = '__all__'

    def get_esta_completada(self, obj):
        user = self.context['request'].user
        return obj.esta_completada_por(user)



class LeccionPendienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeccionPendiente
        fields = '__all__'



class LeccionCompletadaSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeccionCompletada
        fields = ['id', 'leccion', 'fecha_completado']


class LeccionEstadoSerializer(serializers.ModelSerializer):
    completada = serializers.BooleanField()

    class Meta:
        model = Leccion
        fields = ['id', 'completada']