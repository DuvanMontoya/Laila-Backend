from pathlib import Path
import os
import sys
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = 'django-insecure-pz1b6c!9qwas20++blaeqilayu@6o8fg$sly=^g9(n)zt&i_x5'

DEBUG = True

ALLOWED_HOSTS = ['http://localhost:4173','localhost']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'Articulos',
    'Autenticacion',
    'Cursos',
    'Evaluaciones',
    'Latex_Html',
    'Lecciones',
    'Matriculas',
    'Tareas',
    'Usuarios',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'corsheaders',
    'django_ckeditor_5',
]




CKEDITOR_5_CONFIGS = {
    'default': {
        'language': 'es',
        'toolbar': {
            'items': [
                'heading', '|', 'fontSize', 'fontFamily', '|',
                'fontColor', 'fontBackgroundColor', '|', 'bold', 'italic',
                'underline', 'strikethrough', 'subscript', 'superscript', 'code', '|',
                'alignment', '|', 'bulletedList', 'numberedList', '|', 'outdent',
                'indent', 'todoList', '|', 'link', 'blockQuote', 'insertTable',
                'mediaEmbed', 'codeBlock', 'htmlEmbed', '|', 'specialCharacters',
                'horizontalLine', 'pageBreak', '|', 'textPartLanguage', '|',
                'imageUpload', 'imageInsert', '|', 'findAndReplace', 'selectAll',
                'undo', 'redo', '|', 'latex'
            ],
            'shouldNotGroupWhenFull': True
        },
        'image': {
            'toolbar': [
                'imageTextAlternative', 'toggleImageCaption', 'imageStyle:inline',
                'imageStyle:block', 'imageStyle:side', 'linkImage'
            ],
            'upload': {
                'types': ['png', 'jpeg', 'jpg', 'gif', 'svg', 'webp', 'bmp', 'tiff', 'ico', 'heic', 'heif']
            }
        },
        'table': {
            'contentToolbar': [
                'tableColumn', 'tableRow', 'mergeTableCells', 'tableCellProperties',
                'tableProperties'
            ]
        },
        'htmlEmbed': {
            'showPreviews': True,
            'sanitizeHtml': 'inputHtml => { const outputHtml = DOMPurify.sanitize(inputHtml, {ALLOWED_TAGS: ["a", "span", "div", "br", "img", "h1", "h2", "p", "table", "tr", "td", "th", "tbody", "thead", "tfoot", "ul", "ol", "li"], ADD_ATTR: ["style", "class", "id", "name", "src"]}); return { html: outputHtml, hasChanged: inputHtml !== outputHtml }; }'
        },
        'latex': {
            'toolbar': [
                'insertLatex'
            ]
        },
        'link': {
            'decorators': {
                'openInNewTab': {
                    'mode': 'manual',
                    'label': 'Open in a new tab',
                    'defaultValue': True,
                    'attributes': {
                        'target': '_blank',
                        'rel': 'noopener noreferrer'
                    }
                },
                'downloadable': {
                    'mode': 'manual',
                    'label': 'Downloadable',
                    'attributes': {
                        'download': 'file'
                    }
                }
            },
            'addTargetToExternalLinks': True,
            'defaultProtocol': 'https://'
        },
        'removePlugins': [
            'CKBox', 'CKFinder', 'EasyImage', 'RealTimeCollaborativeComments',
            'RealTimeCollaborativeTrackChanges', 'RealTimeCollaborativeRevisionHistory',
            'PresenceList', 'Comments', 'TrackChanges', 'TrackChangesData',
            'RevisionHistory', 'Pagination', 'WProofreader', 'MathType'
        ]
    }
}



CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
CKEDITOR_5_UPLOAD_PATH = "uploads/"





# Configuración para subida de imágenes
# CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.default_storage"
CKEDITOR_5_UPLOAD_PATH = "uploads/"
CKEDITOR_5_CONFIGS['default']['simpleUpload'] = {
    "uploadUrl": "/ckeditor5/image_upload/",
}

# Configuración para MathJax
CKEDITOR_5_MATH_JAX_CONFIG = {
    'tex': {'inlineMath': [['$', '$'], ['\\(', '\\)']]},
    'svg': {'fontCache': 'global'}
}
CKEDITOR_5_MATH_JAX_URL = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'

# Configuración de medios
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
]
CORS_ALLOW_CREDENTIALS = True

ROOT_URLCONF = 'Laila_Backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Laila_Backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'laila',  # Nombre de la base de datos que hemos creado
#         'USER': 'montoyaduvan1',  # Nombre del usuario que hemos creado
#         'PASSWORD': 'Gaussiano1008.',  # Contraseña del usuario que hemos creado
#         'HOST': 'localhost',  # Asumiendo que PostgreSQL está corriendo en el mismo servidor
#         'PORT': '',  # Puerto por defecto para PostgreSQL
#     }
# }


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Bogota'  
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
# STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

LOG_DIR = BASE_DIR / 'logs'
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': LOG_DIR / 'laila.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

CACHE_TIMEOUT = 3600  # Tiempo de expiración de la caché en segundos (1 hora)

CSRF_TRUSTED_ORIGINS = ['http://localhost:5173']


CORS_ALLOW_CREDENTIALS = True