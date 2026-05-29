from auditlog.registry import auditlog
from django.db import models

from .base import BaseModel
from .envio_email import ENVIO_EMAIL_TIPO_CHOICES


class EnvioEmailConteudo(BaseModel):
    """
    Template de conteúdo HTML por tipo de envio de e-mail.
    Registros criados via migration; edição apenas do campo conteudo (API
    PATCH).
    """

    tipo = models.CharField(
        max_length=20,
        choices=ENVIO_EMAIL_TIPO_CHOICES,
        unique=True,
        verbose_name="Tipo de envio",
    )
    conteudo = models.TextField(
        verbose_name="Corpo do e-mail (HTML)",
        help_text=(
            "Fragmento HTML do corpo (sem cabeçalho PMSP). "
            "Variáveis Django: {{ cargo }}, {{ classificacao }}, {{ data_publicacao }}, etc. "  # noqa: E501
            "O layout base vem de templates/email/envio_email.html."
        ),
    )

    class Meta:
        verbose_name = "Conteúdo de e-mail por tipo"
        verbose_name_plural = "Conteúdos de e-mail por tipo"
        ordering = ["tipo"]
        db_table = "processos_envio_email_conteudo"

    def __str__(self):
        return f"{self.get_tipo_display()}"


auditlog.register(EnvioEmailConteudo)
