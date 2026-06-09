"""Módulo models/processo_convocacao."""

from auditlog.registry import auditlog
from django.db import models
from django.utils import timezone

from .base import BaseModel
from .constants import PROCESSO_STATUS_CHOICES, TIPO_ESCOLHA_CHOICES


class ProcessoConvocacao(BaseModel):
    """Modelo para representar processos de convocação."""

    concurso_uuid = models.UUIDField(verbose_name="UUID do Concurso")
    concurso_nome = models.CharField(
        max_length=200, verbose_name="Nome do Concurso"
    )
    descricao = models.CharField(verbose_name="Descrição", max_length=255)
    tipo_escolha = models.CharField(
        max_length=20,
        choices=TIPO_ESCOLHA_CHOICES,
        default="NOVA_AUTORIZACAO",
        verbose_name="Tipo de Escolha",
    )
    status = models.CharField(
        max_length=20,
        choices=PROCESSO_STATUS_CHOICES,
        default="PENDENTE",
        verbose_name="Status",
    )
    passo = models.PositiveSmallIntegerField(
        choices=[(1, "1"), (2, "2"), (3, "3"), (4, "4")],
        default=1,
        verbose_name="Passo",
    )

    esta_ativo = models.BooleanField(
        verbose_name="Está ativo",
        default=True,
    )

    data_convocacao = models.DateTimeField(
        verbose_name="Data de Convocação", default=timezone.now
    )
    data_corte_vagas = models.DateTimeField(
        verbose_name="Data de Corte de Vagas", default=timezone.now
    )
    porcentagem_nna = models.FloatField(
        verbose_name="Porcentagem de NNA", default=0.2
    )
    porcentagem_pcd = models.FloatField(
        verbose_name="Porcentagem de PCD", default=0.05
    )

    class Meta:
        """Configuração do serializer."""

        verbose_name = "Processo de Convocação"
        verbose_name_plural = "Processos de Convocação"
        ordering = ["-criado_em"]
        db_table = "processos_convocacao"

    def __str__(self) -> str:
        """Executa   str  .

        Args:
            self: Instância do objeto.

        Returns:
            Texto resultante da operação.

        Raises:
            Nenhuma exceção específica documentada.
        """
        return f"{self.concurso_nome} - {self.tipo_escolha}"

    def pode_deletar(self) -> bool:
        """Indica se o processo pode ser excluído.

        Args:
            self: Instância do objeto.

        Returns:
            Verdadeiro se a condição for satisfeita.

        Raises:
            Nenhuma exceção específica documentada.
        """
        return self.status not in ("FINALIZADO", "EM_ANDAMENTO")

    def inativar(self) -> None:
        """Inativa o processo e remove cargos vinculados.

        Args:
            self: Instância do objeto.

        Returns:
            Não retorna valor.

        Raises:
            Nenhuma exceção específica documentada.
        """
        self.cargos_processo.all().delete()
        self.esta_ativo = False
        self.save(update_fields=["esta_ativo"])


auditlog.register(ProcessoConvocacao)
