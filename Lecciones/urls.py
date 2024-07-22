from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'lecciones', LeccionViewSet)


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/lecciones/<int:leccion_id>/completar/', CompletarLeccionView.as_view(), name='completar-leccion'),
    path('api/lecciones/<int:pk>/detalles/', LeccionDetallesView.as_view(), name='leccion-detalles'),
    path('api/lecciones/<int:pk>/registrar-progreso/', RegistrarProgresoLeccionView.as_view(), name='registrar-progreso-leccion'),
    path('api/lecciones/<int:pk>/agregar-feedback/', AgregarFeedbackLeccionView.as_view(), name='agregar-feedback-leccion'),
    path('api/lecciones-pendientes/', LeccionPendienteList.as_view(), name='leccion-pendiente-list'),
    path('api/lecciones-completadas/', LeccionCompletadaList.as_view(), name='leccion-completada-list'),
    path('api/lecciones-completadas/<int:pk>/', LeccionCompletadaDetail.as_view(), name='leccion-completada-detail'),
    path('api/cursos/<int:curso_id>/lecciones-completadas/', LeccionesCompletadasView.as_view(), name='lecciones-completadas'),


]
