from django.urls import path, include
from rest_framework import routers
from .views import (
    EvaluacionViewSet, PreguntaViewSet, RespuestaPreguntaViewSet, IntentoEvaluacionViewSet,
    ResultadoEvaluacionViewSet, TagViewSet, EvaluacionDetail, SubmitEvaluacionView,
    ResultadosEvaluacionView, EvaluacionList, PreguntaList, iniciar_evaluacion,
    enviar_evaluacion, obtener_intento, upload_image
)
from django.conf import settings
from django.conf.urls.static import static

router = routers.DefaultRouter()
router.register(r'evaluaciones', EvaluacionViewSet)
router.register(r'preguntas', PreguntaViewSet)
router.register(r'respuestas', RespuestaPreguntaViewSet)
router.register(r'intentos', IntentoEvaluacionViewSet)
router.register(r'resultados', ResultadoEvaluacionViewSet)
router.register(r'tags', TagViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('api/evaluaciones/<int:pk>/', EvaluacionDetail.as_view(), name='evaluacion-detail'),
    path('api/evaluaciones/<int:pk>/submit/', SubmitEvaluacionView.as_view(), name='evaluacion-submit'),
    path('api/evaluaciones/<int:pk>/resultados/', ResultadosEvaluacionView.as_view(), name='evaluacion-resultados'),
    path('api/evaluaciones/', EvaluacionList.as_view(), name='evaluacion-list'),
    path('api/preguntas/', PreguntaList.as_view(), name='pregunta-list'),
    path('api/evaluaciones/<int:evaluacion_id>/iniciar/', iniciar_evaluacion, name='iniciar-evaluacion'),
    path('api/evaluaciones/<int:evaluacion_id>/enviar/', enviar_evaluacion, name='enviar-evaluacion'),
    path('api/evaluaciones/<int:evaluacion_id>/intento/', obtener_intento, name='obtener-intento'),
    path('upload_image/', upload_image, name='upload_image'),
    path("ckeditor5/", include('django_ckeditor_5.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
