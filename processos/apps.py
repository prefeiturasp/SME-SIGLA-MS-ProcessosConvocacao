from django.apps import AppConfig


class ProcessosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'processos'

    def ready(self):
        try:
            from config import celery_app  # noqa: F401
        except Exception:
            pass