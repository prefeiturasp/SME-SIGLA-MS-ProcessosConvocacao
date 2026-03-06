from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction

from processos.models import ProcessoConvocacao
from processos.models.constants import ERROR_PROCESSO_NAO_PODE_EDITAR
from processos.serializers import (
    CargoProcessoSerializer,
    CargoProcessoCreateSerializer,
)

STATUS_FINALIZADO = 'FINALIZADO'


class CargoProcessoViewSet(viewsets.ViewSet):
    """
    ViewSet dedicado para listar e substituir cargos de um processo de convocação.

    - GET /processos-convocacao/{processo_pk}/cargos/ -> lista cargos do processo
    - POST /processos-convocacao/{processo_pk}/cargos/ -> substitui todos os cargos do processo
    """

    permission_classes = [AllowAny]
    lookup_url_kwarg = 'cargo_uuid'

    def _get_processo(self, pk):
        try:
            return ProcessoConvocacao.objects.get(pk=pk)
        except ProcessoConvocacao.DoesNotExist:
            return None

    def list(self, request, processo_pk=None):
        processo = self._get_processo(processo_pk)
        if not processo:
            return Response(
                {"error": "Processo de convocação não encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        cargos = processo.cargos_processo.all()
        serializer = CargoProcessoSerializer(cargos, many=True)
        return Response(serializer.data)

    def create(self, request, processo_pk=None):
        processo = self._get_processo(processo_pk)
        if not processo:
            return Response(
                {"error": "Processo de convocação não encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if processo.status == STATUS_FINALIZADO:
            return Response(
                {"detail": ERROR_PROCESSO_NAO_PODE_EDITAR},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cargos_data = request.data

        if not isinstance(cargos_data, list):
            return Response(
                {"error": "Dados devem ser uma lista de cargos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cargos_criados = []
        cargos_atualizados = []
        erros = []

        existing_qs = processo.cargos_processo.all()
        existing_by_uuid = {str(obj.uuid): obj for obj in existing_qs}
        processed_uuid_strings = set()

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
                    serializer = CargoProcessoCreateSerializer(
                        instance, data=cargo_data, partial=True
                    )
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

        resultado_atual = CargoProcessoSerializer(
            processo.cargos_processo.all(), many=True
        ).data

        if erros:
            return Response(
                {
                    "success": True,
                    "cargos_criados": len(cargos_criados),
                    "cargos_atualizados": len(cargos_atualizados),
                    "cargos_removidos": cargos_removidos,
                    "erros": erros,
                    "cargos": resultado_atual,
                },
                status=status.HTTP_207_MULTI_STATUS,
            )

        return Response(
            {
                "success": True,
                "cargos_criados": len(cargos_criados),
                "cargos_atualizados": len(cargos_atualizados),
                "cargos_removidos": cargos_removidos,
                "cargos": resultado_atual,
            },
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, processo_pk=None, cargo_uuid=None):
        processo = self._get_processo(processo_pk)
        if not processo:
            return Response(
                {"error": "Processo de convocação não encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if processo.status == STATUS_FINALIZADO:
            return Response(
                {"detail": ERROR_PROCESSO_NAO_PODE_EDITAR},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not cargo_uuid:
            return Response(
                {"error": "UUID do cargo não informado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        instance = processo.cargos_processo.filter(uuid=cargo_uuid).first()
        if not instance:
            return Response(
                {"error": "Cargo não encontrado para este processo"},
                status=status.HTTP_404_NOT_FOUND,
            )

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
