from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'articulos', ArticuloViewSet)
router.register(r'usuario-articulos', UsuarioArticuloViewSet)
router.register(r'comentarios', ComentarioViewSet)
router.register(r'categorias-articulos', CategoriaArticuloViewSet)
router.register(r'temas-articulos', TemaArticuloViewSet)
router.register(r'areas', AreaViewSet)


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/articulos/', ArticuloListView.as_view(), name='articulo-list'),
    path('api/articulos/<int:articulo_id>/related/', RelatedArticlesView.as_view(), name='related-articles'),
    path('api/articulos/<int:articulo_id>/comentarios/', ArticuloComentariosView.as_view(), name='articulo-comentarios'),
    path('api/articulos/<int:articulo_id>/calificar/', CalificarArticuloView.as_view(), name='calificar-articulo'),
    path('api/articulos/<int:articulo_id>/incrementar-vistas/', IncrementarVistasArticuloView.as_view(), name='incrementar-vistas'),
    path('api/articulos/<slug:slug>/', ArticuloDetailView.as_view(), name='articulo-detail'),
    path('api/articulos/<int:articulo_id>/matriculado/', CheckEnrollmentView.as_view(), name='check-enrollment'),
    path('api/articulos/<int:articulo_id>/matricular/', MatricularArticuloView.as_view(), name='matricular-articulo'),
    path('api/articulos/<int:articulo_id>/like-status/', LikeStatusView.as_view(), name='like-status'),
    path('api/articulos/<int:articulo_id>/update-like/', UpdateLikeStatusView.as_view(), name='update-like'),

    path('api/usuarios/<int:user_id>/articulos-matriculados/', ArticulosMatriculadosUsuarioView.as_view(), name='articulos-matriculados-usuario'),
    path('api/usuarios/<int:user_id>/comentarios/', ComentariosUsuarioView.as_view(), name='comentarios-usuario'),
    path('api/usuarios/<int:user_id>/articulos-favoritos/', ArticulosFavoritosUsuarioView.as_view(), name='articulos-favoritos-usuario'),
    path('api/usuarios/<int:user_id>/articulos-vistos/', ArticulosVistosUsuarioView.as_view(), name='articulos-vistos-usuario'),
    
]
