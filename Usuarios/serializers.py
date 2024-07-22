# Usuarios/serializers.py

from rest_framework import serializers
from .models import *
from Cursos.models import Curso

class PerfilSerializer(serializers.ModelSerializer):
    universidad = serializers.SerializerMethodField()
    cursos_inscritos = serializers.PrimaryKeyRelatedField(many=True, queryset=Curso.objects.all())

    def get_universidad(self, obj):
        from Articulos.serializers import UniversidadSerializer  # Importación diferida
        return UniversidadSerializer(obj.universidad).data

    class Meta:
        model = Perfil
        fields = '__all__'
