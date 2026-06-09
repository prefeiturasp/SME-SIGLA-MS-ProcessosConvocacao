"""Configuração do app Django ``processos``."""

from django.apps import AppConfig


class ProcessosConfig(AppConfig):
    """App de processos de convocação e envio de e-mails."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "processos"

    def ready(self) -> None:
        """Importa Celery na inicialização do Django.

        Args:
            self: Instância do objeto.

        Returns:
            Não retorna valor.

        Raises:
            Nenhuma exceção específica documentada.
        """
        try:  # noqa: SIM105
            from config import celery_app  # noqa: F401
        except Exception:
            pass
