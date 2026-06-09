"""Módulo models/envio_email."""
from auditlog.registry import auditlog
from django.db import models

from .base import BaseModel

TIPO_CONVOCACAO = "CONVOCACAO"
TIPO_VAGAS = "VAGAS"
TIPO_RESULTADOS = "RESULTADOS"

ENVIO_EMAIL_TIPO_CHOICES = [
    (TIPO_CONVOCACAO, "Convocação"),
    (TIPO_VAGAS, "Vagas"),
    (TIPO_RESULTADOS, "Resultados"),
]


class EnvioEmail(BaseModel):
    """Registro de um lote de envio de e-mails (histórico)."""

    processo_uuid = models.UUIDField(verbose_name="UUID do Processo")
    processo_nome = models.CharField(
        max_length=200, verbose_name="Nome do Processo"
    )
    tipo = models.CharField(
        max_length=20,
        choices=ENVIO_EMAIL_TIPO_CHOICES,
        verbose_name="Tipo de envio",
    )
    quantidade_candidatos = models.IntegerField(
        verbose_name="Quantidade de candidatos",
        default=0,
    )

    class Meta:
        """Configuração do serializer."""
        verbose_name = "Envio de e-mail"
        verbose_name_plural = "Envios de e-mail"
        ordering = ["-criado_em"]
        db_table = "processos_envio_email"

    def __str__(self) -> str:
        """Executa   str  .
        
        Args:
            self: Instância do objeto.
        
        Returns:
            Texto resultante da operação.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        return (
            f"{self.processo_nome} - {self.get_tipo_display()} "
            f"({self.quantidade_candidatos} candidatos)"
        )


auditlog.register(EnvioEmail)
