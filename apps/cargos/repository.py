"""Repositório de acesso a dados de CargoProcesso."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from cargos.models import CargoProcesso
from cargos.serializers import CargoProcessoSerializer
from processos.models import ProcessoConvocacao


class CargoProcessoRepository:
    """Consultas e persistência de cargos vinculados ao processo."""

    @staticmethod
    def _serializar(cargo: CargoProcesso) -> dict[str, Any]:
        """Converte um cargo em dicionário."""
        return CargoProcessoSerializer(cargo).data

    @classmethod
    def _serializar_lista(cls, cargos: list[CargoProcesso]) -> list[dict[str, Any]]:
        """Converte uma lista de cargos em dicionários."""
        return CargoProcessoSerializer(cargos, many=True).data

    @classmethod
    def listar_por_processo(
        cls, processo: ProcessoConvocacao
    ) -> list[dict[str, Any]]:
        """Lista os cargos filtrados por processo."""
        cargos = list(CargoProcesso.objects.filter(processo=processo))
        return cls._serializar_lista(cargos)

    @classmethod
    def obter_por_processo_e_uuid(
        cls,
        processo: ProcessoConvocacao,
        cargo_uuid: str | UUID,
    ) -> dict[str, Any] | None:
        """Retorna o cargo do processo pelo UUID ou None."""
        cargo = CargoProcesso.objects.filter(
            processo=processo, uuid=cargo_uuid
        ).first()
        if cargo is None:
            return None
        return cls._serializar(cargo)

    @classmethod
    def carregar_instancia_por_processo_e_uuid(
        cls,
        processo: ProcessoConvocacao,
        cargo_uuid: str | UUID,
    ) -> CargoProcesso | None:
        """Carrega instância do cargo para operações de escrita."""
        return CargoProcesso.objects.filter(
            processo=processo, uuid=cargo_uuid
        ).first()

    @classmethod
    def listar_opcoes_filtro(cls) -> list[dict[str, Any]]:
        """Lista cargos distintos para opções de filtro."""
        return list(
            CargoProcesso.objects.values("cargo_uuid", "cargo_nome").order_by(
                "cargo_nome", "cargo_uuid"
            )
        )

    @classmethod
    def contar_por_processo(cls, processo: ProcessoConvocacao) -> int:
        """Conta os cargos vinculados ao processo."""
        return CargoProcesso.objects.filter(processo=processo).count()

    @classmethod
    def excluir_fora_de_uuids(
        cls,
        processo: ProcessoConvocacao,
        uuids: set[str],
    ) -> int:
        """Exclui cargos do processo cujo UUID não está no conjunto informado."""
        queryset = CargoProcesso.objects.filter(processo=processo).exclude(
            uuid__in=uuids
        )
        quantidade = queryset.count()
        queryset.delete()
        return quantidade

    @classmethod
    def excluir_por_processo_e_uuid(
        cls,
        processo: ProcessoConvocacao,
        cargo_uuid: str | UUID,
    ) -> None:
        """Exclui um cargo do processo pelo UUID."""
        CargoProcesso.objects.filter(
            processo=processo, uuid=cargo_uuid
        ).delete()

    @classmethod
    def excluir_por_processo(cls, processo: ProcessoConvocacao) -> None:
        """Exclui todos os cargos do processo."""
        CargoProcesso.objects.filter(processo=processo).delete()

    @classmethod
    def criar(cls, **dados: Any) -> dict[str, Any]:
        """Cria um cargo."""
        cargo = CargoProcesso.objects.create(**dados)
        return cls._serializar(cargo)

    @classmethod
    def contar(cls) -> int:
        """Conta todos os cargos."""
        return CargoProcesso.objects.count()

    @classmethod
    def excluir_todos(cls) -> None:
        """Exclui todos os cargos."""
        CargoProcesso.objects.all().delete()
