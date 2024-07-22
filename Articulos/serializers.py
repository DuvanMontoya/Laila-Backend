# Articulos/serializers.py

from rest_framework import serializers
from .models import *
from Autenticacion.serializers import UserSerializer

class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = '__all__'

class CategoriaArticuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaArticulo
        fields = '__all__'

class TemaArticuloSerializer(serializers.ModelSerializer):
    categoria = CategoriaArticuloSerializer(read_only=True)
    
    class Meta:
        model = TemaArticulo
        fields = '__all__'

class ComentarioSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)
    
    class Meta:
        model = Comentario
        fields = '__all__'

class ArticuloSerializer(serializers.ModelSerializer):
    usuario_articulos = serializers.SerializerMethodField()
    area = AreaSerializer(read_only=True)
    categoria_articulo = CategoriaArticuloSerializer(read_only=True)
    tema = TemaArticuloSerializer(read_only=True)
    autor = serializers.SerializerMethodField()
    comentarios = ComentarioSerializer(many=True, read_only=True)
    vistas = serializers.IntegerField(source='num_vistas', read_only=True)
    favoritos = serializers.IntegerField(source='num_favoritos', read_only=True)
    is_liked = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            usuario_articulo = UsuarioArticulo.objects.filter(articulo=obj, usuario=request.user).first()
            return usuario_articulo.like if usuario_articulo else False
        return False
    
    def get_usuario_articulos(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            usuario_articulos = UsuarioArticulo.objects.filter(articulo=obj, usuario=request.user)
            from .serializers import UsuarioArticuloSerializer  # Importación diferida
            return UsuarioArticuloSerializer(usuario_articulos, many=True, context={'request': request}).data
        return []

    def get_autor(self, obj):
        from Usuarios.serializers import PerfilSerializer  # Importación diferida
        return PerfilSerializer(obj.autor, context=self.context).data
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    class Meta:
        model = Articulo
        fields = '__all__'

class UsuarioArticuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioArticulo
        fields = '__all__'


class ArticuloComentarioSerializer(serializers.ModelSerializer):
    articulo = serializers.PrimaryKeyRelatedField(queryset=Articulo.objects.all())
    usuario = UserSerializer(read_only=True)

    class Meta:
        model = Comentario
        fields = '__all__'


class ArticuloViewSerializer(serializers.ModelSerializer):
    articulo = ArticuloSerializer(read_only=True)
    usuario = UserSerializer(read_only=True)

    class Meta:
        model = ArticuloView
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'
        ref_name = 'ArticuloTag'  # Nombre de referencia único para Swagger


class UniversidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Universidad
        fields = '__all__'
