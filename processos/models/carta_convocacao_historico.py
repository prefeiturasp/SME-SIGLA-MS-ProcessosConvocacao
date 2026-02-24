from django.db import models
from .base import BaseModel
from auditlog.registry import auditlog


class CartaConvocacaoHistorico(BaseModel):
    """
    Registro de envio de carta de convocação (histórico).
    """
    processo_uuid = models.UUIDField(verbose_name="UUID do Processo")
    processo_nome = models.CharField(max_length=200, verbose_name="Nome do Processo")
    data = models.DateField(verbose_name="Data")
    quantidade_candidatos = models.IntegerField(
        verbose_name="Quantidade de Candidatos",
        default=0,
    )

    class Meta:
        verbose_name = "Histórico de Carta de Convocação"
        verbose_name_plural = "Históricos de Carta de Convocação"
        ordering = ['-criado_em']
        db_table = 'processos_carta_convocacao_historico'

    def __str__(self):
        return f"{self.processo_nome} - {self.data} ({self.quantidade_candidatos} candidatos)"


auditlog.register(CartaConvocacaoHistorico)
