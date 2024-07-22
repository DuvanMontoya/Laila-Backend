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

    class Meta:
        model = Leccion
        fields = '__all__'




class LeccionDetallesSerializer(serializers.ModelSerializer):
    tema = TemaSerializer()
    evaluacion_asociada = EvaluacionSerializer()
    completada_por = UserSerializer(many=True)
    tareas = TareaSerializer(many=True)

    class Meta:
        model = Leccion
        fields = '__all__'



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