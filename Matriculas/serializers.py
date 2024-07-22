from rest_framework import serializers
from .models import *
from Autenticacion.serializers import UserSerializer
from Cursos.models import Curso



class InscripcionSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)
    curso = serializers.PrimaryKeyRelatedField(queryset=Curso.objects.all())

    class Meta:
        model = Inscripcion
        fields = '__all__'


class SolicitudInscripcionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitudInscripcion
        fields = '__all__'