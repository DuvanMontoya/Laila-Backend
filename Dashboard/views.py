from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from Cursos.models import Curso, Tema
from Lecciones.models import Leccion
from Evaluaciones.models import Evaluacion
from Articulos.models import Articulo, UsuarioArticulo
from django.db.models import Count, Q
from django.utils import timezone

class DashboardDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user
        
        # Cursos matriculados
        cursos_matriculados = Curso.objects.filter(inscritos=usuario)
        
        # Temas y lecciones
        temas = Tema.objects.filter(curso__in=cursos_matriculados)
        lecciones = Leccion.objects.filter(tema__curso__in=cursos_matriculados)
        
        temas_completados = sum(1 for tema in temas if all(leccion.esta_completada_por(usuario) for leccion in tema.lecciones.all()))
        lecciones_completadas = sum(1 for leccion in lecciones if leccion.esta_completada_por(usuario))
        
        # Evaluaciones pendientes
        evaluaciones_pendientes = Evaluacion.objects.filter(
            usuarios_permitidos=usuario,
            fecha_limite__gt=timezone.now()
        ).exclude(
            intento_evaluacion__usuario=usuario,
            intento_evaluacion__completado=True
        ).count()
        
        # Artículos
        articulos_guardados = UsuarioArticulo.objects.filter(usuario=usuario, favorito=True).count()
        total_articulos = Articulo.objects.count()
        
        data = {
            'cursos_matriculados': cursos_matriculados.count(),
            'temas_completados': temas_completados,
            'total_temas': temas.count(),
            'lecciones_completadas': lecciones_completadas,
            'total_lecciones': lecciones.count(),
            'evaluaciones_pendientes': evaluaciones_pendientes,
            'articulos_guardados': articulos_guardados,
            'total_articulos': total_articulos,
        }
        
        return Response(data)