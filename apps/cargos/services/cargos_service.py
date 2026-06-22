"""Serviços de gestão de cargos do processo de convocação."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.db import transaction

from cargos.repository import CargoProcessoRepository
from cargos.serializers import (
    CargoProcessoCreateSerializer,
    CargoProcessoSerializer,
)
from processos.models import ProcessoConvocacao
from processos.repository import ProcessoConvocacaoRepository


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
    def substituir_cargos_processo(
        *,
        processo: ProcessoConvocacao,
        dados_validados: dict[str, Any],
    ) -> dict[str, Any]:
        """Atualiza porcentagens do processo e substitui os cargos."""
        dados_cargos = dados_validados["cargos"]

        campos_atualizacao: list[str] = []
        if (
            "porcentagem_nna" in dados_validados
            and dados_validados["porcentagem_nna"] != processo.porcentagem_nna
        ):
            processo.porcentagem_nna = dados_validados["porcentagem_nna"]
            campos_atualizacao.append("porcentagem_nna")
        if (
            "porcentagem_pcd" in dados_validados
            and dados_validados["porcentagem_pcd"] != processo.porcentagem_pcd
        ):
            processo.porcentagem_pcd = dados_validados["porcentagem_pcd"]
            campos_atualizacao.append("porcentagem_pcd")
        if campos_atualizacao:
            ProcessoConvocacaoRepository.salvar(
                processo, campos_atualizacao=campos_atualizacao
            )

        resultado = CargosProcessoService.salvar_cargos(
            processo=processo, dados_cargos=dados_cargos
        )

        corpo_resposta: dict[str, Any] = {
            "success": True,
            "cargos_criados": len(resultado.cargos_criados),
            "cargos_atualizados": len(resultado.cargos_atualizados),
            "cargos_removidos": resultado.cargos_removidos,
            "cargos": resultado.cargos,
        }
        if resultado.erros:
            corpo_resposta["erros"] = resultado.erros

        return corpo_resposta

    @staticmethod
    def salvar_cargos(
        *, processo: ProcessoConvocacao, dados_cargos: list[dict[str, Any]]
    ) -> SubstituirCargosResultado:
        """Cria, atualiza e remove cargos conforme o corpo recebido."""
        cargos_criados: list[dict[str, Any]] = []
        cargos_atualizados: list[dict[str, Any]] = []
        erros: list[dict[str, Any]] = []

        uuids_processados: set[str] = set()

        with transaction.atomic():
            for dados_cargo in dados_cargos:
                uuid_cargo = dados_cargo.get("uuid")

                if uuid_cargo:
                    uuid_cargo_str = str(uuid_cargo)
                    cargo_existente = (
                        CargoProcessoRepository.carregar_instancia_por_processo_e_uuid(
                            processo, uuid_cargo_str
                        )
                    )
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

            cargos_removidos = CargoProcessoRepository.excluir_fora_de_uuids(
                processo, uuids_processados
            )

        resultado_atual = CargoProcessoRepository.listar_por_processo(processo)
        return SubstituirCargosResultado(
            cargos_criados=cargos_criados,
            cargos_atualizados=cargos_atualizados,
            cargos_removidos=cargos_removidos,
            erros=erros,
            cargos=resultado_atual,
        )
