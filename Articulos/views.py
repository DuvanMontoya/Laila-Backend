from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *
from .permissions import *




class UsuarioArticuloViewSet(viewsets.ModelViewSet):
    queryset = UsuarioArticulo.objects.all()
    serializer_class = UsuarioArticuloSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UsuarioArticulo.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)

    def perform_update(self, serializer):
        serializer.save(usuario=self.request.user)

    def perform_destroy(self, instance):
        instance.delete()

        



class AreaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [permissions.AllowAny]

class CategoriaArticuloViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CategoriaArticulo.objects.all()
    serializer_class = CategoriaArticuloSerializer
    permission_classes = [permissions.AllowAny]

class TemaArticuloViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TemaArticulo.objects.all()
    serializer_class = TemaArticuloSerializer
    permission_classes = [permissions.AllowAny]

class ArticuloViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Articulo.objects.all()
    serializer_class = ArticuloSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['post'])
    def incrementar_vistas(self, request, pk=None):
        articulo = self.get_object()
        articulo.num_vistas += 1
        articulo.save()
        return Response({'status': 'Vistas incrementadas'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def marcar_favorito(self, request, pk=None):
        articulo = self.get_object()
        usuario_articulo, created = UsuarioArticulo.objects.get_or_create(usuario=request.user, articulo=articulo)
        usuario_articulo.favorito = not usuario_articulo.favorito
        usuario_articulo.save()
        return Response({'status': 'Favorito actualizado'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def calificar(self, request, pk=None):
        articulo = self.get_object()
        calificacion = request.data.get('calificacion')
        usuario_articulo, created = UsuarioArticulo.objects.get_or_create(usuario=request.user, articulo=articulo)
        usuario_articulo.calificacion = calificacion
        usuario_articulo.save()
        articulo.calcular_calificacion_promedio()
        return Response({'status': 'Calificación registrada'})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None):
        articulo = self.get_object()
        usuario = request.user
        if usuario in articulo.likes.all():
            articulo.likes.remove(usuario)
        else:
            articulo.likes.add(usuario)
        return Response({'status': 'Like actualizado'})

class ComentarioViewSet(viewsets.ModelViewSet):
    queryset = Comentario.objects.all()
    serializer_class = ComentarioSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)





class ArticuloComentariosView(generics.ListCreateAPIView):
    serializer_class = ComentarioSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        articulo_id = self.kwargs['articulo_id']
        return Comentario.objects.filter(articulo_id=articulo_id)

    def perform_create(self, serializer):
        articulo_id = self.kwargs['articulo_id']
        articulo = Articulo.objects.get(id=articulo_id)
        serializer.save(articulo=articulo, usuario=self.request.user)


class RelatedArticlesView(generics.ListAPIView):
    serializer_class = ArticuloSerializer

    def get_queryset(self):
        articulo_id = self.kwargs['articulo_id']
        articulo = Articulo.objects.get(id=articulo_id)
        return Articulo.objects.filter(categoria_articulo=articulo.categoria_articulo).exclude(id=articulo_id)

class IncrementarVistasArticuloView(generics.UpdateAPIView):
    serializer_class = ArticuloSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        articulo_id = self.kwargs['articulo_id']
        articulo = Articulo.objects.get(id=articulo_id)
        return articulo

    def perform_update(self, serializer):
        articulo = self.get_object()
        articulo.incrementar_vistas()
        serializer.save()

class MarcarFavoritoArticuloView(generics.UpdateAPIView):
    serializer_class = UsuarioArticuloSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        articulo_id = self.kwargs['articulo_id']
        usuario_articulo, created = UsuarioArticulo.objects.get_or_create(usuario=self.request.user, articulo_id=articulo_id)
        return usuario_articulo

    def perform_update(self, serializer):
        usuario_articulo = self.get_object()
        usuario_articulo.favorito = not usuario_articulo.favorito
        serializer.save()

class CalificarArticuloView(generics.UpdateAPIView):
    serializer_class = UsuarioArticuloSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        articulo_id = self.kwargs['articulo_id']
        usuario_articulo, created = UsuarioArticulo.objects.get_or_create(usuario=self.request.user, articulo_id=articulo_id)
        return usuario_articulo

    def perform_update(self, serializer):
        usuario_articulo = self.get_object()
        calificacion = self.request.data.get('calificacion')
        usuario_articulo.calificacion = calificacion
        serializer.save()
        articulo = usuario_articulo.articulo
        articulo.calcular_calificacion_promedio()


class ArticulosFavoritosUsuarioView(generics.ListAPIView):
    serializer_class = UsuarioArticuloSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return UsuarioArticulo.objects.filter(usuario_id=user_id, favorito=True)

class ArticulosVistosUsuarioView(generics.ListAPIView):
    serializer_class = ArticuloViewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user_id = self.kwargs['user_id']
        return ArticuloView.objects.filter(usuario_id=user_id)

class ArticuloDetailView(APIView):
    def get(self, request, articulo_id):
        articulo = get_object_or_404(Articulo, id=articulo_id)
        serializer = ArticuloSerializer(articulo)
        return JsonResponse(serializer.data)

class ArticuloListView(APIView):
    def get(self, request):
        articulos = Articulo.objects.all()
        serializer = ArticuloSerializer(articulos, many=True)
        return JsonResponse(serializer.data, safe=False)

class CheckEnrollmentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        articulo_id = kwargs['articulo_id']
        articulo = get_object_or_404(Articulo, id=articulo_id)
        usuario = request.user

        matriculado = UsuarioArticulo.objects.filter(usuario=usuario, articulo=articulo).exists()
        return Response({'matriculado': matriculado})


class RelatedArticlesView(generics.ListAPIView):
    serializer_class = ArticuloSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        articulo_id = self.kwargs['articulo_id']
        articulo = get_object_or_404(Articulo, id=articulo_id)
        return Articulo.objects.filter(categoria_articulo=articulo.categoria_articulo).exclude(id=articulo_id)


class MatricularArticuloView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        articulo_id = self.kwargs['articulo_id']
        articulo = get_object_or_404(Articulo, id=articulo_id)
        usuario = request.user

        if UsuarioArticulo.objects.filter(usuario=usuario, articulo=articulo).exists():
            return Response({'detail': 'Ya estás matriculado en este artículo.'}, status=status.HTTP_400_BAD_REQUEST)

        UsuarioArticulo.objects.create(usuario=usuario, articulo=articulo)
        return Response({'detail': 'Te has matriculado en el artículo exitosamente.'}, status=status.HTTP_201_CREATED)


class ArticuloComentariosView(generics.ListCreateAPIView):
    serializer_class = ComentarioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        articulo_id = self.kwargs['articulo_id']
        return Comentario.objects.filter(articulo_id=articulo_id)

    def perform_create(self, serializer):
        articulo_id = self.kwargs['articulo_id']
        articulo = get_object_or_404(Articulo, id=articulo_id)
        serializer.save(articulo=articulo, usuario=self.request.user)


class ComentariosUsuarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        comentarios_usuario = Comentario.objects.filter(usuario_id=user_id)
        serializer = ComentarioSerializer(comentarios_usuario, many=True)
        return Response(serializer.data)


class LikeStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, articulo_id):
        articulo = get_object_or_404(Articulo, id=articulo_id)
        usuario_articulo = UsuarioArticulo.objects.filter(usuario=request.user, articulo=articulo).first()
        is_liked = usuario_articulo.like if usuario_articulo else False
        total_likes = articulo.likes.count()
        return JsonResponse({'is_liked': is_liked, 'total_likes': total_likes})


class UpdateLikeStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, articulo_id):
        articulo = get_object_or_404(Articulo, id=articulo_id)
        usuario = request.user
        is_liked = request.data.get('is_liked', False)

        if is_liked:
            articulo.likes.add(usuario)
        else:
            articulo.likes.remove(usuario)

        total_likes = articulo.likes.count()
        return JsonResponse({'is_liked': is_liked, 'total_likes': total_likes})


class ArticulosFavoritosUsuarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        articulos_favoritos = Articulo.objects.filter(likes__id=user_id)
        serializer = ArticuloSerializer(articulos_favoritos, many=True)
        return Response(serializer.data)
    

class ArticulosMatriculadosUsuarioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        articulos_matriculados = Articulo.objects.filter(usuario_articulos__usuario_id=user_id)
        serializer = ArticuloSerializer(articulos_matriculados, many=True)
        return Response(serializer.data)


