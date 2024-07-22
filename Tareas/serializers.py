from rest_framework import serializers
from .models import *
from Lecciones.models import Leccion
from Autenticacion.serializers import UserSerializer
from django.utils import timezone




class TareaSerializer(serializers.ModelSerializer):
    leccion = serializers.PrimaryKeyRelatedField(queryset=Leccion.objects.all())

    class Meta:
        model = Tarea
        fields = '__all__'


class EntregaTareaSerializer(serializers.ModelSerializer):
    tarea = TareaSerializer(read_only=True)
    usuario = UserSerializer(read_only=True)

    class Meta:
        model = EntregaTarea
        fields = '__all__'
        read_only_fields = ['tarea', 'usuario']
        extra_kwargs = {
            'archivo': {'write_only': True}
        }

    def create(self, validated_data):
        return EntregaTarea.objects.create(usuario=self.context['request'].user, **validated_data)
    
    def update(self, instance, validated_data):
        instance.calificacion = validated_data.get('calificacion', instance.calificacion)
        instance.comentario = validated_data.get('comentario', instance.comentario)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['archivo'] = instance.archivo.url
        return data
    
    def validate(self, data):
        if data.get('calificacion') and (data['calificacion'] < 0 or data['calificacion'] > 100):
            raise serializers.ValidationError('La calificación debe estar entre 0 y 100')
        return data
    
    def validate_tarea(self, value):
        if value.fecha_entrega < timezone.now():
            raise serializers.ValidationError('La tarea ya no está disponible')
        return value
    
    def validate_usuario(self, value):
        if value != self.context['request'].user:
            raise serializers.ValidationError('No puedes entregar tareas para otros usuarios')
        return value
    
    class Meta:
        model = EntregaTarea
        fields = '__all__'
        read_only_fields = ['tarea', 'usuario']
        extra_kwargs = {
            'archivo': {'write_only': True}
        }

