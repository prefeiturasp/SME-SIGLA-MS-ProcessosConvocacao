from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from processos.services.cargos_service import CargosProcessoService

from processos.models import CargoProcesso, ProcessoConvocacao
from processos.models.constants import ERROR_PROCESSO_NAO_PODE_EDITAR
from processos.serializers import (
    CargoProcessoSerializer,
    ProcessoCargosPayloadSerializer,
)

STATUS_FINALIZADO = 'FINALIZADO'


class CargoProcessoViewSet(viewsets.ModelViewSet):
    """
    ViewSet dedicado para listar e substituir cargos de um processo de convocação.

    - GET /processos-convocacao/{processo_pk}/cargos/ -> lista cargos do processo
    - POST /processos-convocacao/{processo_pk}/cargos/ -> substitui todos os cargos do processo
    """

    queryset = CargoProcesso.objects.all()
    serializer_class = CargoProcessoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['cargo_uuid']
    search_fields = ['cargo_nome']
    ordering_fields = ['cargo_nome', 'cargo_codigo', 'vagas']
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

        payload_serializer = ProcessoCargosPayloadSerializer(data=request.data)
        payload_serializer.is_valid(raise_exception=True)
        payload = payload_serializer.validated_data
        cargos_data = payload["cargos"]

        # Persistir porcentagens no processo (se vierem no payload)
        update_fields = []
        if "porcentagem_nna" in payload and payload["porcentagem_nna"] != processo.porcentagem_nna:
            processo.porcentagem_nna = payload["porcentagem_nna"]
            update_fields.append("porcentagem_nna")
        if "porcentagem_pcd" in payload and payload["porcentagem_pcd"] != processo.porcentagem_pcd:
            processo.porcentagem_pcd = payload["porcentagem_pcd"]
            update_fields.append("porcentagem_pcd")
        if update_fields:
            processo.save(update_fields=update_fields)

        result = CargosProcessoService.salvar_cargos(processo=processo, cargos_data=cargos_data)

        if result.erros:
            return Response(
                {
                    "success": True,
                    "cargos_criados": len(result.cargos_criados),
                    "cargos_atualizados": len(result.cargos_atualizados),
                    "cargos_removidos": result.cargos_removidos,
                    "erros": result.erros,
                    "cargos": result.cargos,
                },
                status=status.HTTP_207_MULTI_STATUS,
            )

        return Response(
            {
                "success": True,
                "cargos_criados": len(result.cargos_criados),
                "cargos_atualizados": len(result.cargos_atualizados),
                "cargos_removidos": result.cargos_removidos,
                "cargos": result.cargos,
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
