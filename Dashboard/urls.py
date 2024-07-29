from django.urls import path
from .views import DashboardDataView

urlpatterns = [
    path('api/dashboard-data/', DashboardDataView.as_view(), name='dashboard-data'),
]