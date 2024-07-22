from django.urls import path
from .views import ConvertirLatex
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('api/convertir/', ConvertirLatex.as_view(), name='convertir_latex'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
