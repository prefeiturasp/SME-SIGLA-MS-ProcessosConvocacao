from auditlog.registry import auditlog
from django.db import models

from .base import BaseModel

ENVIO_STATUS_PENDENTE = "PENDENTE"
ENVIO_STATUS_SUCESSO = "SUCESSO"
ENVIO_STATUS_ERRO = "ERRO"

ENVIO_STATUS_CHOICES = [
    (ENVIO_STATUS_PENDENTE, "Pendente"),
    (ENVIO_STATUS_SUCESSO, "Sucesso"),
    (ENVIO_STATUS_ERRO, "Erro"),
]


class EnvioEmailCandidato(BaseModel):
    """
    Registro do envio de e-mail para cada candidato.
    """

    envio_email = models.ForeignKey(
        "EnvioEmail",
        on_delete=models.CASCADE,
        verbose_name="Envio de e-mail",
        related_name="candidatos",
    )
    nome = models.CharField(max_length=200, verbose_name="Nome")
    rf = models.CharField(max_length=20, verbose_name="RF", blank=True)
    email = models.EmailField(verbose_name="Email")
    status = models.CharField(
        max_length=20,
        choices=ENVIO_STATUS_CHOICES,
        verbose_name="Status do envio",
    )
    status_detalhe = models.TextField(
        verbose_name="Detalhe do status",
        blank=True,
        help_text="Mensagem de erro ou detalhe do envio",
    )
    conteudo = models.TextField(
        verbose_name="Conteúdo do email enviado",
        blank=True,
    )

    class Meta:
        verbose_name = "Envio de e-mail - Candidato"
        verbose_name_plural = "Envio de e-mail - Candidatos"
        ordering = ["-criado_em"]
        db_table = "processos_envio_email_candidato"

    def __str__(self):
        return f"{self.nome} ({self.email}) - {self.get_status_display()}"


auditlog.register(EnvioEmailCandidato)
