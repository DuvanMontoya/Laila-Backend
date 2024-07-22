from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, UserView, LogoutView, CustomAuthToken

urlpatterns = [
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/user/', UserView.as_view(), name='user'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('api/auth/login/', CustomAuthToken.as_view(), name='api_login'),

]
