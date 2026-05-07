from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from django.db import transaction

from processos.models import ProcessoConvocacao
from processos.serializers import CargoProcessoCreateSerializer, CargoProcessoSerializer


@dataclass(frozen=True)
class SubstituirCargosResult:
    cargos_criados: List[Dict[str, Any]]
    cargos_atualizados: List[Dict[str, Any]]
    cargos_removidos: int
    erros: List[Dict[str, Any]]
    cargos: List[Dict[str, Any]]


class CargosProcessoService:
    @staticmethod
    def salvar_cargos(*, processo: ProcessoConvocacao, cargos_data: List[Dict[str, Any]]) -> SubstituirCargosResult:
        cargos_criados: List[Dict[str, Any]] = []
        cargos_atualizados: List[Dict[str, Any]] = []
        erros: List[Dict[str, Any]] = []

        existing_qs = processo.cargos_processo.all()
        existing_by_uuid = {str(obj.uuid): obj for obj in existing_qs}
        processed_uuid_strings: set[str] = set()

        with transaction.atomic():
            for cargo_data in cargos_data:
                item_uuid = cargo_data.get("uuid")

                # Atualizar quando vier uuid
                if item_uuid:
                    item_uuid_str = str(item_uuid)
                    instance = existing_by_uuid.get(item_uuid_str)
                    if not instance:
                        erros.append(
                            {
                                "uuid": item_uuid_str,
                                "erros": "Cargo não encontrado para este processo",
                            }
                        )
                        continue

                    serializer = CargoProcessoCreateSerializer(instance, data=cargo_data, partial=True)
                    if serializer.is_valid():
                        cargo = serializer.save()
                        cargos_atualizados.append(CargoProcessoSerializer(cargo).data)
                        processed_uuid_strings.add(item_uuid_str)
                    else:
                        erros.append({"uuid": item_uuid_str, "erros": serializer.errors})

                else:
                    # Criar quando não vier uuid
                    serializer = CargoProcessoCreateSerializer(data=cargo_data)
                    if serializer.is_valid():
                        cargo = serializer.save(processo=processo)
                        cargos_criados.append(CargoProcessoSerializer(cargo).data)
                        processed_uuid_strings.add(str(cargo.uuid))
                    else:
                        erros.append(
                            {
                                "cargo": cargo_data.get("cargo_nome", "N/A"),
                                "erros": serializer.errors,
                            }
                        )

            # Remover registros que não estão no payload
            to_delete_qs = existing_qs.exclude(uuid__in=processed_uuid_strings)
            cargos_removidos = to_delete_qs.count()
            to_delete_qs.delete()

        resultado_atual = CargoProcessoSerializer(processo.cargos_processo.all(), many=True).data
        return SubstituirCargosResult(
            cargos_criados=cargos_criados,
            cargos_atualizados=cargos_atualizados,
            cargos_removidos=cargos_removidos,
            erros=erros,
            cargos=resultado_atual,
        )

