from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404



class PerfilView(APIView):
    def get(self, request, user_id=None):
        if user_id:
            perfil = get_object_or_404(Perfil, usuario__id=user_id)
        else:
            perfil = request.user.perfil  # Asumiendo que el usuario está autenticado y tiene un perfil
        serializer = PerfilSerializer(perfil)
        return Response(serializer.data)



class PerfilUpdateView(UpdateView):
    model = Perfil
    fields = ['nombre', 'apellido', 'profesion', 'edad', 'genero', 'fecha_nacimiento', 'pais', 'ciudad', 'whatsapp', 'correo', 'direccion', 'avatar', 'biografia', 'twitter', 'linkedin', 'github', 'website']
    template_name = 'perfil/perfil_form.html'
    success_url = reverse_lazy('home')

    def get_object(self):
        return self.request.user.perfil