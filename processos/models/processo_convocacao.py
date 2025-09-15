from django.db import models
from django.utils import timezone
from .base import BaseModel
from .constants import (
    PROCESSO_STATUS_CHOICES,
    PROCESSO_TIPOS_CHOICES
)
from auditlog.registry import auditlog


class ProcessoConvocacao(BaseModel):
    """
    Modelo para representar processos de convocação.
    """

    concurso_uuid = models.UUIDField(verbose_name="UUID do Concurso")
    concurso_nome = models.CharField(max_length=200, verbose_name="Nome do Concurso")
    descricao = models.CharField(verbose_name="Descrição", max_length=255)
    tipo_processo = models.CharField(
        max_length=20,
        choices=PROCESSO_TIPOS_CHOICES,
        default='CONVOCACAO',
        verbose_name="Tipo de Processo"
    )
    status = models.CharField(
        max_length=20,
        choices=PROCESSO_STATUS_CHOICES,
        default='EM_ANDAMENTO',
        verbose_name="Status"
    )
    data_publicacao = models.DateTimeField(verbose_name="Data de Publicação", default=timezone.now)
    data_convocacao = models.DateTimeField(verbose_name="Data de Convocação", default=timezone.now)
    numero_convocados = models.IntegerField(verbose_name="Número de Convocação", default=1)

    class Meta:
        verbose_name = "Processo de Convocação"
        verbose_name_plural = "Processos de Convocação"
        ordering = ['-criado_em']
        db_table = 'processos_convocacao'

    def __str__(self):
        return f"{self.concurso_nome} - {self.numero_convocados}"


auditlog.register(ProcessoConvocacao)
