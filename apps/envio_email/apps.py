"""Configuração do app Django ``envio_email``."""

from django.apps import AppConfig


class EnvioEmailConfig(AppConfig):
    """App de envio de e-mails e templates de convocação."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "envio_email"
