from django.db import models
from django.contrib.postgres.fields import ArrayField
from .base import BaseModel
from auditlog.registry import auditlog


class CargoProcesso(BaseModel):
    """
    Modelo para representar os cargos selecionados para um processo de convocação específico.
    """
    processo = models.ForeignKey(
        'ProcessoConvocacao',
        on_delete=models.CASCADE,
        verbose_name="Processo de Convocação",
        related_name='cargos_processo'
    )
    cargo_nome = models.CharField(max_length=200, verbose_name="Nome do Cargo")
    cargo_uuid = models.UUIDField(verbose_name="UUID do Cargo")
    cargo_codigo = models.CharField(max_length=20, verbose_name="Código do Cargo", default="")

    vagas = models.IntegerField(
        verbose_name="Quantidade de Vagas",
        default=0,
        help_text="Total de vagas disponíveis para este cargo no processo"
    )
    candidatos_geral = models.IntegerField(
        verbose_name="Candidatos Gerais",
        default=0,
        help_text="Quantidade de candidatos habilitados geral"
    )
    candidatos_pcd = models.IntegerField(
        verbose_name="Candidatos PCD",
        default=0,
        help_text="Quantidade de candidatos habilitados pessoas com deficiência"
    )
    candidatos_nna = models.IntegerField(
        verbose_name="Candidatos NNA",
        default=0,
        help_text="Quantidade de candidatos habilitados nna"
    )
    total_candidatos = models.IntegerField(
        verbose_name="Total de Candidatos",
        default=0,
        help_text="Total de candidatos classificados para este cargo"
    )
    candidatos_uuids = ArrayField(
        base_field=models.UUIDField(),
        default=list,
        blank=True,
        verbose_name="UUIDs de Candidatos"
    )

    class Meta:
        verbose_name = "Cargo do Processo"
        verbose_name_plural = "Cargos do Processo"
        unique_together = ['processo', 'cargo_nome']
        ordering = ['cargo_nome']
        db_table = 'processos_cargos'

    def __str__(self):
        return f"{self.processo.concurso_nome} - {self.cargo_nome}"


auditlog.register(CargoProcesso)
