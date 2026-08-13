"""Repositório de acesso a dados de ProcessoConvocacao."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import UUID

from django.db.models import QuerySet
from processos.models import ProcessoConvocacao
from processos.serializers import (
    ProcessoConvocacaoListSerializer,
    ProcessoConvocacaoSerializer,
)


class ProcessoConvocacaoRepository:
    """Consultas e persistência de processos de convocação."""

    @staticmethod
    def serializar(processo: ProcessoConvocacao) -> dict[str, Any]:
        """Serialize a process to a dictionary."""
        return ProcessoConvocacaoSerializer(processo).data

    @classmethod
    def serializar_lista(
        cls, processos: list[ProcessoConvocacao]
    ) -> list[dict[str, Any]]:
        """Serialize a list of processes to dictionaries."""
        return ProcessoConvocacaoListSerializer(processos, many=True).data

    @classmethod
    def aplicar_filtro_data_convocacao_gte(
        cls,
        queryset: QuerySet[ProcessoConvocacao],
        data: date,
    ) -> QuerySet[ProcessoConvocacao]:
        return queryset.filter(data_convocacao__date__gte=data)

    @classmethod
    def aplicar_filtro_data_convocacao_lte(
        cls,
        queryset: QuerySet[ProcessoConvocacao],
        data: date,
    ) -> QuerySet[ProcessoConvocacao]:
        return queryset.filter(data_convocacao__date__lte=data)

    @classmethod
    def aplicar_filtro_cargo_uuid(
        cls,
        queryset: QuerySet[ProcessoConvocacao],
        cargo_uuid: UUID,
    ) -> QuerySet[ProcessoConvocacao]:
        return queryset.filter(
            cargos_processo__cargo_uuid=cargo_uuid
        ).distinct()

    @classmethod
    def serializar_queryset(
        cls, queryset: QuerySet[ProcessoConvocacao]
    ) -> list[dict[str, Any]]:
        """Serialize a queryset of processes to dictionaries."""
        return cls.serializar_lista(list(queryset))

    @classmethod
    def listar_opcoes_concurso(cls) -> list[dict[str, Any]]:
        """Lista concursos distintos para opções de filtro."""
        processos = list(ProcessoConvocacao.objects.all())
        return ProcessoConvocacaoSerializer(processos, many=True).data

    @classmethod
    def carregar_instancia_por_pk(
        cls, pk: str | UUID
    ) -> ProcessoConvocacao | None:
        """Carrega instância do processo para operações de escrita."""
        try:
            return ProcessoConvocacao.objects.prefetch_related(
                "cargos_processo"
            ).get(pk=pk)
        except ProcessoConvocacao.DoesNotExist:
            return None

    @classmethod
    def obter_por_pk(cls, pk: str | UUID) -> dict[str, Any] | None:
        """Retorna o processo pela PK ou None."""
        processo = cls.carregar_instancia_por_pk(pk)
        if processo is None:
            return None
        return cls.serializar(processo)

    @classmethod
    def existe_por_uuid(cls, uuid: UUID) -> bool:
        return ProcessoConvocacao.objects.filter(uuid=uuid).exists()

    @classmethod
    def atualizar_status(
        cls, processo: ProcessoConvocacao, status: str
    ) -> None:
        processo.status = status
        cls.salvar(processo, campos_atualizacao=["status"])

    @classmethod
    def salvar(
        cls,
        processo: ProcessoConvocacao,
        *,
        campos_atualizacao: list[str] | None = None,
    ) -> None:
        if campos_atualizacao:
            processo.save(update_fields=campos_atualizacao)
        else:
            processo.save()

    @classmethod
    def criar(cls, **dados: Any) -> dict[str, Any]:
        """Cria um processo de convocação."""
        processo = ProcessoConvocacao.objects.create(**dados)
        return cls.serializar(processo)

    @classmethod
    def contar(cls) -> int:
        return ProcessoConvocacao.objects.count()

    @classmethod
    def excluir_todos(cls) -> None:
        ProcessoConvocacao.objects.all().delete()

    @classmethod
    def inativar(cls, processo: ProcessoConvocacao) -> None:
        from cargos.repository import CargoProcessoRepository

        CargoProcessoRepository.excluir_por_processo(processo)
        processo.esta_ativo = False
        cls.salvar(processo, campos_atualizacao=["esta_ativo"])

    @classmethod
    def contar_ativos_por_concurso(cls, concurso_uuid: str | UUID) -> int:
        """Conta convocações ativas restantes para um concurso."""
        return ProcessoConvocacao.objects.filter(
            concurso_uuid=concurso_uuid, esta_ativo=True
        ).count()
