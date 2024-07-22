from rest_framework import viewsets, permissions
from .models import *
from .serializers import *
from .permissions import IsOwnerOrReadOnly







class TareaViewSet(viewsets.ModelViewSet):
    queryset = Tarea.objects.all()
    serializer_class = TareaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]