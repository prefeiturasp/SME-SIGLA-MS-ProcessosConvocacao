"""Django settings for convocacao_processes project."""

import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DJANGO_ENVIRONMENT = os.environ.get("DJANGO_ENVIRONMENT", "local")
AMBIENTE_APLICACAO = os.environ.get("AMBIENTE_APLICACAO", DJANGO_ENVIRONMENT)
MS_PATH = os.environ.get("MS_PATH", "/ms-processos-convocacao")

BASE_DIR = Path(__file__).resolve().parent.parent
# Adiciona a pasta 'apps' ao sys.path do Python
sys.path.insert(0, os.path.join(BASE_DIR, "apps"))

SECRET_KEY = os.environ.get(
    "SECRET_KEY", "django-insecure-your-secret-key-here"
)
DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "qa-api-sigla.sme.prefeitura.sp.gov.br",
    "hom-api-sigla.sme.prefeitura.sp.gov.br",
]
CSRF_TRUSTED_ORIGINS = [
    "https://qa-api-sigla.sme.prefeitura.sp.gov.br",
    "https://hom-api-sigla.sme.prefeitura.sp.gov.br",
]

# Application definition
INSTALLED_APPS = [
    "elasticapm.contrib.django",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "auditlog",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "rest_framework",
    # Local
    "core",
    "processos",
    "cargos",
    "envio_email",
]

MIDDLEWARE = [
    "elasticapm.contrib.django.middleware.TracingMiddleware",
    "sigla_sdk.middlewares.CorrelationIdMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "sigla_sdk.middlewares.AuditlogJWTMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
DB_ENGINE = os.environ.get("DB_ENGINE", "django.db.backends.postgresql")

if DB_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": os.environ.get("DB_NAME", BASE_DIR / "db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": os.environ.get("DB_NAME", "db_sigla"),
            "USER": os.environ.get("DB_USER", "postgres"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "postgres"),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation." "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]

# Internationalization
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

_ms_path_segment = (MS_PATH or "/ms-processos-convocacao").strip("/")
if DJANGO_ENVIRONMENT != "local":
    STATIC_URL = f"/{_ms_path_segment}/django_static/"
    MEDIA_URL = f"/{_ms_path_segment}/media/"
else:
    STATIC_URL = "/django_static/"
    MEDIA_URL = "/media/"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# DRF settings
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": (
        "rest_framework.pagination.PageNumberPagination"
    ),
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # "sigla_sdk.autenticacao.authentication.ApiKeyAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        # 'rest_framework.permissions.IsAuthenticated',
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# AuditLog settings
AUDITLOG_INCLUDE_ALL_MODELS = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "sigla_sdk.logging.json_formatter.CustomJsonFormatter",
            # Estes campos do logging padrão virarão chaves no JSON
            "format": (
                "%(levelname)s %(asctime)s %(module)s %(filename)s "
                "%(lineno)d %(funcName)s %(message)s"
            ),
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "elasticapm": {
            "level": "DEBUG",
            "class": "elasticapm.contrib.django.handlers.LoggingHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "elasticapm"],
            "level": "INFO",
            "propagate": False,
        },
        "processos": {
            "handlers": ["console", "elasticapm"],
            "level": "DEBUG",
            "propagate": False,
        },
        "envio_email": {
            "handlers": ["console", "elasticapm"],
            "level": "DEBUG",
            "propagate": False,
        },
        "cargos": {
            "handlers": ["console", "elasticapm"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["console", "elasticapm"],
            "level": "ERROR",
            "propagate": False,
        },
        "elasticapm.errors": {
            "level": "ERROR",
            "handlers": ["console"],
            "propagate": False,
        },
        "elasticapm.logging": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

ELASTIC_APM = {
    "SERVICE_NAME": os.environ.get(
        "ELASTIC_APM_SERVICE_NAME", "SME-SIGLA-MS-Processos-Convocacao"
    ),
    "SECRET_TOKEN": os.environ.get("ELASTIC_APM_SECRET_TOKEN", ""),
    "SERVER_URL": os.environ.get(
        "ELASTIC_APM_SERVER_URL", "http://localhost:8200"
    ),
    "SERVER_TIMEOUT": os.environ.get("ELASTIC_APM_SERVER_TIMEOUT", "35s"),
    "ENVIRONMENT": os.environ.get(
        "ELASTIC_APM_ENVIRONMENT", AMBIENTE_APLICACAO
    ),
    "ENABLED": os.environ.get("ELASTIC_APM_ENABLED", "0") == "1",
    "DEBUG": os.environ.get("ELASTIC_APM_DEBUG", "0") == "1",
    "TRANSACTION_SAMPLE_RATE": float(
        os.environ.get("ELASTIC_APM_TRANSACTION_SAMPLE_RATE", "0.3")
    ),
    "METRICS_INTERVAL": os.environ.get("ELASTIC_APM_METRICS_INTERVAL", "10s"),
    "FLUSH_INTERVAL": os.environ.get("ELASTIC_APM_FLUSH_INTERVAL", "10s"),
    "MAX_BATCH_EVENT_COUNT": int(
        os.environ.get("ELASTIC_APM_MAX_BATCH_EVENT_COUNT", "1000")
    ),
    "MAX_QUEUE_EVENT_COUNT": int(
        os.environ.get("ELASTIC_APM_MAX_QUEUE_EVENT_COUNT", "1000")
    ),
    "TRANSACTION_MAX_SPANS": int(
        os.environ.get("ELASTIC_APM_TRANSACTION_MAX_SPANS", "500")
    ),
    "DJANGO_TRANSACTION_NAME_FROM_ROUTE": True,
    "LOG_LEVEL": os.environ.get("ELASTIC_APM_LOG_LEVEL", "INFO"),
    "LOG_ECS_REFORMATTING": os.environ.get(
        "ELASTIC_APM_LOG_ECS_REFORMATTING", "off"
    ),
    "RECORDING": True,
    "TRANSACTIONS_ROOT_UNNAMED": True,
    "CAPTURE_BODY": "all",
    "CAPTURE_HEADERS": True,
    "CAPTURE_ERRORS": True,
    "CAPTURE_PERFORMANCE": True,
    "CAPTURE_TRANSACTIONS": True,
    "CAPTURE_SPANS": True,
    "CAPTURE_TRANSACTION_STACKTRACES": True,
    "CAPTURE_TRANSACTION_STACKTRACES_LIMIT": 10,
}

DESCRICAO_API = """
API do microsserviço de **processos de convocação** do SIGLA (SME-SP).
Mantém os processos de convocação de candidatos habilitados em concursos,
os cargos e quantitativos de cada processo e o envio de e-mails aos
convocados.

## Autenticação

Envie o token **JWT** emitido pelo microsserviço de usuários no header
`Authorization: Bearer <token>`. Também são aceitos HTTP Basic e a sessão
do Django Admin. As rotas atendem chamadas sem credencial, mas uma
credencial **inválida** é recusada com **403**: o serviço não responde 401.

## Erros

- **400** com `{"detail": "..."}`: regra de negócio violada.
- **400** com `{"<campo>": ["..."]}`: dados enviados inválidos.
- **403** com `{"detail": "...", "code": "..."}`: credencial recusada.
- **404** com `{"detail": "..."}`: registro não encontrado. Listar,
  substituir e excluir cargos respondem `{"error": "..."}` quando o
  processo ou o cargo não existe.
- **500**: erro inesperado, sem corpo JSON padronizado.

## Paginação

Só a listagem de processos é paginada, com `page` e `page_size` (padrão
10). A resposta traz `links`, `count`, `page`, `page_size` e `results`.
As demais listagens retornam um array simples.
"""

SPECTACULAR_SETTINGS = {
    "TITLE": "Processos Convocação Sigla API",
    "DESCRIPTION": DESCRICAO_API,
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "TAGS": [
        {
            "name": "Processos de convocação",
            "description": (
                "Criação, consulta e ciclo de vida dos processos de "
                "convocação."
            ),
        },
        {
            "name": "Cargos do processo",
            "description": (
                "Cargos, vagas e quantitativos de candidatos de um processo."
            ),
        },
        {
            "name": "Envio de e-mail",
            "description": (
                "Disparo de e-mails aos convocados e histórico dos envios."
            ),
        },
        {
            "name": "Conteúdo de e-mail",
            "description": (
                "Assunto e corpo padrão dos e-mails, por tipo de envio."
            ),
        },
    ],
    "ENUM_NAME_OVERRIDES": {
        "StatusProcessoEnum": "processos.constants.PROCESSO_STATUS_CHOICES",
        "TipoEscolhaEnum": "processos.constants.TIPO_ESCOLHA_CHOICES",
        "StatusEnvioEmailEnum": (
            "envio_email.models.envio_email_candidato.ENVIO_STATUS_CHOICES"
        ),
        "TipoEnvioEmailEnum": (
            "envio_email.models.envio_email.ENVIO_EMAIL_TIPO_CHOICES"
        ),
    },
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "jwtAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": (
                    "Token JWT emitido pelo microsserviço de usuários do "
                    "SIGLA, enviado em `Authorization: Bearer <token>`."
                ),
            },
            # "ApiKeyAuth": {
            #     "type": "apiKey",
            #     "in": "header",
            #     "name": "X-API-Key",
            # },
        }
    },
    # "SECURITY": [{"ApiKeyAuth": []}],
}

# E-mail config
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "noreply@localhost"
)

# Celery (broker e result backend)
_celery_redis_url = os.environ.get("CELERY_REDIS_URL", "").strip()
CELERY_BROKER_URL = _celery_redis_url
CELERY_RESULT_BACKEND = _celery_redis_url
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Sao_Paulo"
CELERY_TASK_TIME_LIMIT = 5 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 60
# Fila dedicada no Redis compartilhado (outros projetos usam a fila "celery")
CELERY_TASK_DEFAULT_QUEUE = "processos_convocacao"


# MS URLs e API Keys
API_KEY = os.environ.get("API_KEY", "api-key-processos-convocacao")
API_KEY_HEADER = os.environ.get("API_KEY_HEADER", "X-API-Key")

CANDIDATOS_API_URL = os.environ.get("CANDIDATOS_API_URL", "").rstrip("/")
CANDIDATOS_API_KEY = os.environ.get("CANDIDATOS_API_KEY", "api-key-candidatos")

AGENDA_API_URL = os.environ.get("AGENDAS_API_URL", "").rstrip("/")
AGENDA_API_KEY = os.environ.get("AGENDA_API_KEY", "api-key-agenda")

ESCOLHAS_API_URL = os.environ.get("ESCOLHAS_API_URL", "").rstrip("/")
ESCOLHAS_API_KEY = os.environ.get("ESCOLHAS_API_KEY", "api-key-escolhas")

CONCURSOS_API_URL = os.environ.get("CONCURSOS_API_URL", "").rstrip("/")
CONCURSOS_API_KEY = os.environ.get("CONCURSOS_API_KEY", "api-key-concursos")

MS_URL = os.environ.get("MS_URL", "").rstrip("/")

JWT_SIGNING_KEY = os.environ.get(
    "JWT_SIGNING_KEY",
    os.environ.get("SECRET_KEY", "fallback-só-dev"),
)

SIMPLE_JWT = {
    "SIGNING_KEY": JWT_SIGNING_KEY,
    "ALGORITHM": "HS256",
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=1440),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}
