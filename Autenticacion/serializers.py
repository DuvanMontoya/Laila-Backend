# serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *
from rest_framework_simplejwt.tokens import RefreshToken




class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'




class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    refresh = serializers.SerializerMethodField()
    access = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'refresh', 'access', 'profile')
        extra_kwargs = {'password': {'write_only': True}}

    def get_refresh(self, obj):
        refresh = RefreshToken.for_user(obj)
        return str(refresh)

    def get_access(self, obj):
        refresh = RefreshToken.for_user(obj)
        return str(refresh.access_token)

    def get_profile(self, obj):
        profile, created = UserProfile.objects.get_or_create(user=obj)
        return UserProfileSerializer(profile).data

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        if User.objects.filter(username=validated_data['username']).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ('id', 'username', 'password')
#         extra_kwargs = {'password': {'write_only': True}}

#     def create(self, validated_data):
#         user = User.objects.create_user(**validated_data)
#         return user


# class UserSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ('username', 'email', 'password')
#         extra_kwargs = {
#             'password': {'write_only': True}
#         }

#     def create(self, validated_data):
#         user = User.objects.create_user(**validated_data)
#         return user







class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'



class UsuarioRolSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioRol
        fields = '__all__'



class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = '__all__'


class SolicitudSerializer(serializers.ModelSerializer):
    class Meta:
        model = Solicitud
        fields = '__all__'





# class MensajeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Mensaje
#         fields = '__all__'


# class PublicacionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Publicacion
#         fields = '__all__'

# class ComentarioSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Comentario
#         fields = '__all__'

# class LikeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Like
#         fields = '__all__'


# class NotificacionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Notificacion
#         fields = '__all__'