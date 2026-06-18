"""Serviços de gestão de cargos do processo de convocação."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import transaction

from cargos.serializers import (
    CargoProcessoCreateSerializer,
    CargoProcessoSerializer,
)
from processos.models import ProcessoConvocacao


@dataclass(frozen=True)
class SubstituirCargosResultado:
    """Resultado da substituição de cargos de um processo."""

    cargos_criados: list[dict[str, Any]]
    cargos_atualizados: list[dict[str, Any]]
    cargos_removidos: int
    erros: list[dict[str, Any]]
    cargos: list[dict[str, Any]]


class CargosProcessoService:
    """Operações de persistência de cargos vinculados ao processo."""

    @staticmethod
    def salvar_cargos(
        *, processo: ProcessoConvocacao, dados_cargos: list[dict[str, Any]]
    ) -> SubstituirCargosResultado:
        """Cria, atualiza e remove cargos conforme o corpo recebido."""
        cargos_criados: list[dict[str, Any]] = []
        cargos_atualizados: list[dict[str, Any]] = []
        erros: list[dict[str, Any]] = []

        cargos_existentes_qs = processo.cargos_processo.all()
        cargos_por_uuid = {
            str(cargo.uuid): cargo for cargo in cargos_existentes_qs
        }
        uuids_processados: set[str] = set()

        with transaction.atomic():
            for dados_cargo in dados_cargos:
                uuid_cargo = dados_cargo.get("uuid")

                if uuid_cargo:
                    uuid_cargo_str = str(uuid_cargo)
                    cargo_existente = cargos_por_uuid.get(uuid_cargo_str)
                    if not cargo_existente:
                        erros.append(
                            {
                                "uuid": uuid_cargo_str,
                                "erros": "Cargo não encontrado para este processo",
                            }
                        )
                        continue

                    serializador = CargoProcessoCreateSerializer(
                        cargo_existente, data=dados_cargo, partial=True
                    )
                    if serializador.is_valid():
                        cargo = serializador.save()
                        cargos_atualizados.append(
                            CargoProcessoSerializer(cargo).data
                        )
                        uuids_processados.add(uuid_cargo_str)
                    else:
                        erros.append(
                            {
                                "uuid": uuid_cargo_str,
                                "erros": serializador.errors,
                            }
                        )
                else:
                    serializador = CargoProcessoCreateSerializer(
                        data=dados_cargo
                    )
                    if serializador.is_valid():
                        cargo = serializador.save(processo=processo)
                        cargos_criados.append(
                            CargoProcessoSerializer(cargo).data
                        )
                        uuids_processados.add(str(cargo.uuid))
                    else:
                        erros.append(
                            {
                                "cargo": dados_cargo.get("cargo_nome", "N/A"),
                                "erros": serializador.errors,
                            }
                        )

            cargos_a_remover_qs = cargos_existentes_qs.exclude(
                uuid__in=uuids_processados
            )
            cargos_removidos = cargos_a_remover_qs.count()
            cargos_a_remover_qs.delete()

        resultado_atual = CargoProcessoSerializer(
            processo.cargos_processo.all(), many=True
        ).data
        return SubstituirCargosResultado(
            cargos_criados=cargos_criados,
            cargos_atualizados=cargos_atualizados,
            cargos_removidos=cargos_removidos,
            erros=erros,
            cargos=resultado_atual,
        )
