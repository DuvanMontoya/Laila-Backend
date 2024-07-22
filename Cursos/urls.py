from django.urls import path
from .views import (
    CategoriaViewSet, CursoViewSet, TemaViewSet, 
    TemaCompletadoList, CalificarCursoView, 
    CalcularProgresoCursoView, InscribirCursoView, 
    InscripcionesUsuarioView, InstructorViewSet, 
    CursoRecomendacionView, CursoDetallesView, 
    VerificarInscripcionView, CursoEstadisticasView, 
    CursoProgresoView
)

urlpatterns = [
    # Rutas para los cursos
    path('api/cursos/', CursoViewSet.as_view({'get': 'list'}), name='curso-list'),
    path('api/cursos/<int:pk>/', CursoViewSet.as_view({'get': 'retrieve'}), name='curso-detail'),
    path('api/cursos/<int:pk>/detalles/', CursoDetallesView.as_view(), name='curso-detalles'),
    path('api/cursos/<int:pk>/verificar_inscripcion/', VerificarInscripcionView.as_view(), name='verificar-inscripcion'),
    path('api/cursos/<int:pk>/estadisticas/', CursoEstadisticasView.as_view(), name='curso-estadisticas'),
    path('api/cursos/<int:pk>/progreso/', CursoProgresoView.as_view(), name='curso-progreso'),
    path('api/cursos/recomendaciones/', CursoRecomendacionView.as_view(), name='curso-recomendaciones'),
    path('api/cursos/<int:curso_id>/calificar/', CalificarCursoView.as_view(), name='calificar-curso'),
    path('api/cursos/<int:curso_id>/inscribir/', InscribirCursoView.as_view(), name='inscribir-curso'),

    # Rutas para otros modelos
    path('api/usuarios/<int:user_id>/inscripciones/', InscripcionesUsuarioView.as_view(), name='inscripciones-usuario'),
    path('api/temas-completados/', TemaCompletadoList.as_view(), name='tema-completado-list'),
    # path('api/cursos/<int:pk>/solicitar_inscripcion/', InscripcionesUsuarioView.as_view(), name='solicitar-inscripcion'),
    path('api/cursos/<int:pk>/solicitar_inscripcion/', CursoViewSet.as_view({'post': 'solicitar_inscripcion'}), name='solicitar-inscripcion'),
    
    # Rutas para categorías, temas e instructores (aquí asumiendo que usarás vistas basadas en clases o ViewSets)
    path('api/categorias/', CategoriaViewSet.as_view({'get': 'list'}), name='categoria-list'),
    path('api/categorias/<int:pk>/', CategoriaViewSet.as_view({'get': 'retrieve'}), name='categoria-detail'),
    path('api/temas/', TemaViewSet.as_view({'get': 'list'}), name='tema-list'),
    path('api/temas/<int:pk>/', TemaViewSet.as_view({'get': 'retrieve'}), name='tema-detail'),
    path('api/instructores/', InstructorViewSet.as_view({'get': 'list'}), name='instructor-list'),
    path('api/instructores/<int:pk>/', InstructorViewSet.as_view({'get': 'retrieve'}), name='instructor-detail'),
]
