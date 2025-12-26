# Configuración de Seguridad Mejorada para Backend360
# Agregar estas configuraciones a settings.py

# ============================================================
# MIDDLEWARE - Agregar después de AuthenticationMiddleware
# ============================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    
    # Middleware de seguridad personalizados
    'usuarios.middleware.AuditMiddleware',           # Auditoría de acciones
    'usuarios.middleware.SecurityHeadersMiddleware',  # Headers de seguridad
    'usuarios.middleware.RateLimitMiddleware',       # Limitación de requests
    
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

# ============================================================
# LOGGING - Configuración de logs de auditoría
# ============================================================

import os

# Crear directorio de logs si no existe
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'audit': {
            'format': '{asctime} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'audit.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'audit',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'security.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'general_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'general.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'audit': {
            'handlers': ['audit_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        '': {  # Root logger
            'handlers': ['general_file', 'console'],
            'level': 'INFO',
        },
    },
}

# ============================================================
# REST FRAMEWORK - Throttling y Permisos
# ============================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # Throttling - Limitación de requests
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',          # Usuarios anónimos: 100 requests por hora
        'user': '1000/hour',         # Usuarios autenticados: 1000 requests por hora
        'login': '5/minute',         # Login: 5 intentos por minuto
        'password_reset': '3/hour',  # Reset de contraseña: 3 por hora
        'sensitive': '10/minute',    # Operaciones sensibles: 10 por minuto
    },
    # Paginación
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    # Parser classes
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}

# ============================================================
# JWT - Configuración de Tokens
# ============================================================

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),   # Token de acceso válido por 30 minutos
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),      # Token de refresco válido por 7 días
    'ROTATE_REFRESH_TOKENS': True,                    # Rotar tokens al refrescar
    'BLACKLIST_AFTER_ROTATION': True,                 # Blacklist de tokens antiguos
    'UPDATE_LAST_LOGIN': True,                        # Actualizar last_login
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    
    'JTI_CLAIM': 'jti',
}

# ============================================================
# SEGURIDAD - Headers y Configuraciones
# ============================================================

# Solo en producción
if not DEBUG:
    # HTTPS obligatorio
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 año
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Protección adicional
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'

# ============================================================
# CORS - Configuración
# ============================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://10.168.0.5:3000",
    # Agregar dominios de producción aquí
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'content-type',
    'authorization',
    'x-csrftoken',
    'x-requested-with',
    'accept',
    'accept-encoding',
    'content-disposition',
]

CORS_EXPOSE_HEADERS = [
    'Content-Disposition',
]

# ============================================================
# CSRF - Configuración
# ============================================================

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://10.168.0.5:3000',
    # Agregar dominios de producción aquí
]

# Usar CSRF token en cookies
CSRF_USE_SESSIONS = False
CSRF_COOKIE_HTTPONLY = False  # Permite JavaScript acceder (necesario para frontend)
CSRF_COOKIE_SAMESITE = 'Lax'

# ============================================================
# VALIDACIÓN DE CONTRASEÑAS - Ya configurado pero reforzado
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ============================================================
# SESIONES - Configuración de seguridad
# ============================================================

SESSION_COOKIE_AGE = 3600  # 1 hora
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ============================================================
# ARCHIVOS SUBIDOS - Límites de seguridad
# ============================================================

# Tamaño máximo de archivo (10MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# Extensiones de archivo permitidas
ALLOWED_UPLOAD_EXTENSIONS = [
    'pdf', 'doc', 'docx', 'xls', 'xlsx',
    'jpg', 'jpeg', 'png', 'gif',
    'zip', 'rar'
]

# ============================================================
# RATE LIMITING - Configuración del Middleware
# ============================================================

# Para RateLimitMiddleware personalizado
RATE_LIMIT_MAX_REQUESTS = 100  # Máximo de requests
RATE_LIMIT_WINDOW_SECONDS = 60  # Ventana de tiempo en segundos

# En producción, considerar usar Redis para rate limiting:
# CACHES = {
#     'default': {
#         'BACKEND': 'django_redis.cache.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#         }
#     }
# }

# ============================================================
# ROLES Y PERMISOS
# ============================================================

# Ya configurado
ROLEPERMISSIONS_MODULE = 'usuarios.roles'

# Registrar roles personalizados (opcional, para referencia)
ROLEPERMISSIONS_REGISTER_ADMIN = True

# ============================================================
# CONFIGURACIÓN DE EMAIL - Reforzar seguridad
# ============================================================

# Asegurarse de que las credenciales de email estén en variables de entorno
# en producción, no en settings.py

# EMAIL_HOST_PASSWORD debería venir de una variable de entorno:
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')

# ============================================================
# VARIABLES DE ENTORNO - Ejemplo para producción
# ============================================================

# En producción, usar variables de entorno para:
# - SECRET_KEY
# - DATABASE_PASSWORD
# - EMAIL_HOST_PASSWORD
# - API_KEYS
# - etc.

# Ejemplo usando python-decouple:
# from decouple import config
# SECRET_KEY = config('SECRET_KEY')
# DEBUG = config('DEBUG', default=False, cast=bool)

# ============================================================
# NOTAS DE IMPLEMENTACIÓN
# ============================================================

"""
1. Crear directorio logs/ en la raíz del proyecto
2. Agregar logs/ al .gitignore
3. Configurar rotación de logs en producción
4. Revisar y ajustar límites de throttling según necesidades
5. En producción, usar Redis para rate limiting distribuido
6. Configurar monitoreo de logs de auditoría y seguridad
7. Implementar alertas para eventos críticos de seguridad
8. Hacer backup regular de logs antes de que se roten
9. Revisar periódicamente los logs de auditoría
10. Actualizar SECRET_KEY y credenciales sensibles regularmente
"""
