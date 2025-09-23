from django.db import models
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
    nome = models.CharField(max_length=200, verbose_name="Nome do Cargo")
    cargo_uuid = models.UUIDField(verbose_name="UUID do Cargo")

    class Meta:
        verbose_name = "Cargo do Processo"
        verbose_name_plural = "Cargos do Processo"
        unique_together = ['processo', 'nome']
        ordering = ['nome']
        db_table = 'processos_cargos'

    def __str__(self):
        return f"{self.processo.concurso_nome} - {self.nome}"


auditlog.register(CargoProcesso)
