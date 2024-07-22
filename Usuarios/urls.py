from django.urls import path
from .views import PerfilView

urlpatterns = [
    path('api/perfil/', PerfilView.as_view(), name='perfil_base'),
    path('api/perfil/<int:user_id>/', PerfilView.as_view(), name='perfil_detail'),
]
