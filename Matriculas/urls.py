from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'inscripciones', InscripcionViewSet)
router.register(r'solicitudes', SolicitudInscripcionViewSet, basename='solicitud')



urlpatterns = [
    path('api/', include(router.urls)),
]
