from rest_framework import serializers
from .models import *
from Autenticacion.serializers import UserSerializer

def get_leccion_serializer():
    from Lecciones.serializers import LeccionSerializer
    return LeccionSerializer

class CategoriaSerializer(serializers.ModelSerializer):
    cursos_count = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = '__all__'

    def get_cursos_count(self, obj):
        return obj.cursos.count()

class CursoListSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)

    class Meta:
        model = Curso
        fields = ['id', 'titulo', 'descripcion_corta', 'imagen_principal_url', 'categoria', 'calificacion_promedio']

class CursoSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = ['id', 'titulo']

class InstructorSerializer(serializers.ModelSerializer):
    usuario = serializers.StringRelatedField()
    cursos_creados = serializers.SerializerMethodField()
    especialidades = CategoriaSerializer(many=True, read_only=True)

    class Meta:
        model = Instructor
        fields = '__all__'

    def get_cursos_creados(self, obj):
        return CursoSimpleSerializer(obj.cursos_creados.all(), many=True, context=self.context).data

class TemaSerializer(serializers.ModelSerializer):
    curso = serializers.PrimaryKeyRelatedField(queryset=Curso.objects.all())
    lecciones = serializers.SerializerMethodField()
    contribuyentes = UserSerializer(many=True, read_only=True)
    progreso = serializers.SerializerMethodField()

    class Meta:
        model = Tema
        fields = '__all__'

    def get_lecciones(self, obj):
        LeccionSerializer = get_leccion_serializer()
        return LeccionSerializer(obj.lecciones.all(), many=True, context=self.context).data

    def get_progreso(self, obj):
        usuario = self.context['request'].user if 'request' in self.context else None
        return obj.calcular_progreso(usuario) if usuario and usuario.is_authenticated else 0

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'
        ref_name = 'CursoTag'

class ReseñaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reseña
        fields = ['id', 'curso', 'usuario', 'calificacion', 'comentario']
        read_only_fields = ['id', 'curso', 'usuario']

    def validate_calificacion(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("La calificación debe estar entre 1 y 5.")
        return value

class CursoDetailSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    profesor = InstructorSerializer(read_only=True)
    temas = TemaSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reseñas = ReseñaSerializer(many=True, read_only=True)
    progreso_usuario = serializers.SerializerMethodField()
    esta_inscrito = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = '__all__'

    def get_progreso_usuario(self, obj):
        usuario = self.context['request'].user if 'request' in self.context else None
        return obj.calcular_progreso(usuario) if usuario and usuario.is_authenticated else 0

    def get_esta_inscrito(self, obj):
        usuario = self.context['request'].user if 'request' in self.context else None
        return obj.esta_inscrito(usuario) if usuario and usuario.is_authenticated else False

class TemaCompletadoSerializer(serializers.ModelSerializer):
    usuario = UserSerializer(read_only=True)
    tema = TemaSerializer(read_only=True)

    class Meta:
        model = TemaCompletado
        fields = '__all__'
        unique_together = ['usuario', 'tema']

class CursoSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    profesor = InstructorSerializer(read_only=True)
    temas = TemaSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reseñas = ReseñaSerializer(many=True, read_only=True)
    inscritos = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    portada_curso = serializers.ImageField()
    
    calificacion_promedio = serializers.SerializerMethodField()
    progreso_promedio = serializers.SerializerMethodField()
    tasa_finalizacion = serializers.SerializerMethodField()
    nivel_satisfaccion = serializers.SerializerMethodField()
    esta_inscrito = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = '__all__'

    def get_calificacion_promedio(self, obj):
        return float(obj.calificacion_promedio) if obj.calificacion_promedio is not None else 0.0

    def get_tasa_finalizacion(self, obj):
        return obj.calcular_tasa_finalizacion()

    def get_nivel_satisfaccion(self, obj):
        return obj.nivel_satisfaccion

    def get_esta_inscrito(self, obj):
        usuario = self.context['request'].user
        return obj.esta_inscrito(usuario)

    def get_progreso_promedio(self, obj):
        return obj.calcular_progreso_promedio()

class ProgresoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progreso
        fields = '__all__'
