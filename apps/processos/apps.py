"""Configuração do app Django ``processos``."""

from django.apps import AppConfig


class ProcessosConfig(AppConfig):
    """App de processos de convocação."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "processos"

    def ready(self) -> None:
        """Importa Celery e signals na inicialização do Django."""
        try:  # noqa: SIM105
            from config import celery_app 
        except Exception:
            pass
        import processos.signals
