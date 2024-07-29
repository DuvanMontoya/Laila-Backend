import os
import django

# Asegúrate de que el nombre del proyecto aquí sea correcto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Laila_Backend.settings')
django.setup()


import random
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned



from Evaluaciones.models import (
    Competencia, ContenidoMatematico, Evaluacion, Pregunta, Opcion, 
    IntentoEvaluacion, RespuestaPregunta, Tag, ResultadoEvaluacion,
    EstadisticasEvaluacion
)

def get_or_create_resource(model, **kwargs):
    """
    Obtiene o crea un recurso, manejando posibles errores de integridad y múltiples objetos.
    """
    try:
        instance, created = model.objects.get_or_create(**kwargs)
        if created:
            print(f'Creado {model.__name__}: {instance}')
        else:
            print(f'{model.__name__} ya existe: {instance}')
        return instance
    except IntegrityError:
        print(f'Error de integridad al crear {model.__name__}. Intentando recuperar...')
        try:
            return model.objects.filter(**kwargs).first()
        except Exception as e:
            print(f'Error al recuperar {model.__name__}: {str(e)}')
            return None
    except MultipleObjectsReturned:
        print(f'Múltiples {model.__name__} encontrados. Retornando el primero.')
        return model.objects.filter(**kwargs).first()
    except Exception as e:
        print(f'Error inesperado al crear/obtener {model.__name__}: {str(e)}')
        return None

def create_users(num_users=10):
    users = []
    for i in range(num_users):
        username = f'user{i}'
        user = get_or_create_resource(User, username=username)
        if user and not user.password:
            user.set_password('password')
            user.save()
        if user:
            users.append(user)
    return users

def create_competencias(num_competencias=10):
    return [get_or_create_resource(Competencia, 
        nombre=f'Competencia {i}',
        descripcion=f'Descripción de la competencia {i}'
    ) for i in range(num_competencias) if get_or_create_resource(Competencia, nombre=f'Competencia {i}') is not None]

def create_contenidos_matematicos(num_contenidos=10):
    categorias = ['EST', 'GEO', 'ALG']
    return [get_or_create_resource(ContenidoMatematico,
        categoria=random.choice(categorias),
        nombre=f'Contenido {i}'
    ) for i in range(num_contenidos) if get_or_create_resource(ContenidoMatematico, nombre=f'Contenido {i}') is not None]

def create_tags(num_tags=10):
    return [get_or_create_resource(Tag, nombre=f'Tag {i}') for i in range(num_tags) if get_or_create_resource(Tag, nombre=f'Tag {i}') is not None]

def create_evaluaciones(num_evaluaciones=10):
    evaluaciones = []
    for i in range(num_evaluaciones):
        try:
            evaluacion = get_or_create_resource(Evaluacion,
                titulo=f'Evaluación {i}',
                tipo=random.choice([choice[0] for choice in Evaluacion.TipoEvaluacionChoices.choices]),
                descripcion=f'Descripción de la evaluación {i}',
                fecha_inicio=timezone.now(),
                fecha_fin=timezone.now() + timezone.timedelta(days=7),
                intentos_permitidos=random.randint(1, 5),
                ponderacion=random.uniform(0, 100),
                criterios_aprobacion=random.uniform(0, 100),
                tiempo_limite=random.randint(30, 120),
                resultados_visibles=random.choice([True, False]),
                mostrar_resultados=random.choice([True, False]),
                mostrar_opciones_correctas=random.choice([True, False])
            )
            if evaluacion:
                evaluaciones.append(evaluacion)
        except Exception as e:
            print(f"Error al crear evaluación {i}: {str(e)}")
    return evaluaciones

def create_preguntas(num_preguntas=10, competencias=None, contenidos=None, tags=None):
    preguntas = []
    for i in range(num_preguntas):
        pregunta = get_or_create_resource(Pregunta,
            texto_pregunta=f'Pregunta {i}',
            tipo_pregunta=random.choice([choice[0] for choice in Pregunta.TipoPreguntaChoices.choices]),
            dificultad=random.choice([choice[0] for choice in Pregunta.DificultadChoices.choices]),
            puntos=random.uniform(1, 10),
            competencia=random.choice(competencias) if competencias else None,
            contenido_matematico=random.choice(contenidos) if contenidos else None,
            situacion=random.choice([choice[0] for choice in Pregunta.SituacionChoices.choices])
        )
        if pregunta:
            if tags:
                pregunta.tags.set(random.sample(tags, min(random.randint(1, 3), len(tags))))
            preguntas.append(pregunta)
    return preguntas

def create_opciones(preguntas):
    for pregunta in preguntas:
        for i in range(4):
            get_or_create_resource(Opcion,
                pregunta=pregunta,
                texto_opcion=f'Opción {i} para {pregunta.texto_pregunta}',
                es_correcta=random.choice([True, False]),
                puntos=random.uniform(1, 10)
            )

def create_intentos_y_respuestas(users, evaluaciones, num_intentos=10):
    if not users or not evaluaciones:
        print("No hay usuarios o evaluaciones disponibles para crear intentos y respuestas.")
        return

    for _ in range(num_intentos):
        usuario = random.choice(users)
        evaluacion = random.choice(evaluaciones)
        
        try:
            with transaction.atomic():
                intento = get_or_create_resource(IntentoEvaluacion,
                    evaluacion=evaluacion,
                    usuario=usuario,
                    completado=True,
                    puntaje_obtenido=random.uniform(1, evaluacion.ponderacion)
                )
                
                if intento and evaluacion.preguntas.exists():
                    for pregunta in evaluacion.preguntas.all():
                        if pregunta.opciones.exists():
                            opcion = random.choice(pregunta.opciones.all())
                            get_or_create_resource(RespuestaPregunta,
                                intento=intento,
                                pregunta=pregunta,
                                respuesta={'opcion_seleccionada': opcion.id},
                                usuario=usuario,
                                es_correcta=opcion.es_correcta,
                                puntos_obtenidos=opcion.puntos if opcion.es_correcta else 0
                            )
                    
                    # Actualizar ResultadoEvaluacion
                    resultado, _ = ResultadoEvaluacion.objects.get_or_create(
                        evaluacion=evaluacion,
                        usuario=usuario
                    )
                    resultado.intentos.add(intento)
                    resultado.actualizar_mejor_intento()
                    
                    # Actualizar EstadisticasEvaluacion
                    estadisticas, _ = EstadisticasEvaluacion.objects.get_or_create(
                        evaluacion=evaluacion
                    )
                    estadisticas.actualizar_estadisticas()
        except Exception as e:
            print(f"Error al crear intento y respuestas: {str(e)}")

def main():
    try:
        with transaction.atomic():
            users = create_users()
            competencias = create_competencias()
            contenidos = create_contenidos_matematicos()
            tags = create_tags()
            evaluaciones = create_evaluaciones()
            preguntas = create_preguntas(competencias=competencias, contenidos=contenidos, tags=tags)
            create_opciones(preguntas)
            
            # Asociar preguntas a evaluaciones
            for evaluacion in evaluaciones:
                evaluacion.preguntas.set(random.sample(preguntas, min(random.randint(1, len(preguntas)), len(preguntas))))
            
            create_intentos_y_respuestas(users, evaluaciones)
        
        print("Base de datos poblada exitosamente.")
    except Exception as e:
        print(f"Error al poblar la base de datos: {str(e)}")

if __name__ == "__main__":
    main()