from django.db import models
from django.utils import timezone
from .base import BaseModel
from .constants import (
    PROCESSO_STATUS_CHOICES,
    TIPO_ESCOLHA_CHOICES
)
from auditlog.registry import auditlog


class ProcessoConvocacao(BaseModel):
    """
    Modelo para representar processos de convocação.
    """

    concurso_uuid = models.UUIDField(verbose_name="UUID do Concurso")
    concurso_nome = models.CharField(max_length=200, verbose_name="Nome do Concurso")
    descricao = models.CharField(verbose_name="Descrição", max_length=255)
    tipo_escolha = models.CharField(
        max_length=20,
        choices=TIPO_ESCOLHA_CHOICES,
        default='NOVA_AUTORIZACAO',
        verbose_name="Tipo de Escolha"
    )
    status = models.CharField(
        max_length=20,
        choices=PROCESSO_STATUS_CHOICES,
        default='EM_ANDAMENTO',
        verbose_name="Status"
    )
    passo = models.PositiveSmallIntegerField(
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4')],
        default=1,
        verbose_name="Passo"
    )

    esta_ativo = models.BooleanField(
        verbose_name="Está ativo",
        default=True,
    )

    data_convocacao = models.DateTimeField(verbose_name="Data de Convocação", default=timezone.now)
    data_corte_vagas = models.DateTimeField(verbose_name="Data de Corte de Vagas", default=timezone.now)


    class Meta:
        verbose_name = "Processo de Convocação"
        verbose_name_plural = "Processos de Convocação"
        ordering = ['-criado_em']
        db_table = 'processos_convocacao'

    def __str__(self):
        return f"{self.concurso_nome} - {self.tipo_escolha}"

    def pode_deletar(self):
        return self.status not in ('FINALIZADO', 'EM_ANDAMENTO')
    
    def inativar(self):
        # Remove cargos associados (não faz sentido manter cargos em processo inativo)
        self.cargos_processo.all().delete()
        self.esta_ativo = False
        self.save(update_fields=['esta_ativo'])

auditlog.register(ProcessoConvocacao)
