"""Modelo de template de conteúdo de e-mail por tipo."""

from auditlog.registry import auditlog
from django.db import models

from core.models import BaseModel

from .envio_email import (
    ASSUNTO_POR_TIPO,
    ENVIO_EMAIL_TIPO_CHOICES,
    TIPO_CONVOCACAO,
)


class EnvioEmailConteudo(BaseModel):
    """Template de conteúdo HTML por tipo de envio de e-mail."""

    tipo = models.CharField(
        max_length=20,
        choices=ENVIO_EMAIL_TIPO_CHOICES,
        unique=True,
        verbose_name="Tipo de envio",
    )
    assunto = models.CharField(
        max_length=255,
        verbose_name="Assunto do e-mail",
        default="",
        blank=True,
    )
    conteudo = models.TextField(
        verbose_name="Corpo do e-mail (HTML)",
        help_text=(
            "Fragmento HTML do corpo (sem cabeçalho PMSP). "
            "Variáveis Django: {{ cargo }}, {{ classificacao }}, "
            "{{ data_publicacao }}, etc. "
            "O layout base vem de templates/email/envio_email.html."
        ),
    )
    conteudo_gabarito = models.TextField(
        verbose_name="Corpo do e-mail (HTML)",
        help_text=(
            "Fragmento HTML do corpo (sem cabeçalho PMSP). "
            "Variáveis Django: {{ cargo }}, {{ classificacao }}, "
            "{{ data_publicacao }}, etc. "
            "O layout base vem de templates/email/envio_email.html."
        ),
    )

    class Meta:
        verbose_name = "Conteúdo de e-mail por tipo"
        verbose_name_plural = "Conteúdos de e-mail por tipo"
        ordering = ["tipo"]
        db_table = "processos_envio_email_conteudo"

    def assunto_efetivo(self) -> str:
        if self.assunto and self.assunto.strip():
            return self.assunto.strip()
        return ASSUNTO_POR_TIPO.get(self.tipo, ASSUNTO_POR_TIPO[TIPO_CONVOCACAO])

    def __str__(self) -> str:
        return f"{self.get_tipo_display()}"


auditlog.register(EnvioEmailConteudo)
