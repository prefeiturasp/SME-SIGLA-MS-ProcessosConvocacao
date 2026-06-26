"""ViewSet de cargos vinculados a um processo de convocação."""

from __future__ import annotations

from uuid import UUID

from cargos.models import CargoProcesso
from cargos.repository import CargoProcessoRepository
from cargos.serializers import (
    CargoProcessoSerializer,
    ProcessoCargosDadosSerializer,
)
from cargos.services import CargosProcessoService
from django_filters.rest_framework import DjangoFilterBackend
from processos.constants import ERROR_PROCESSO_NAO_PODE_EDITAR
from processos.models import ProcessoConvocacao
from processos.repository import ProcessoConvocacaoRepository
from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.request import Request
from rest_framework.response import Response

STATUS_FINALIZADO = "FINALIZADO"


class CargoProcessoViewSet(viewsets.ModelViewSet):
    """Lista, substitui e remove cargos de um processo de convocação."""

    queryset = CargoProcesso.objects.all()
    serializer_class = CargoProcessoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["cargo_uuid"]
    search_fields = ["cargo_nome"]
    ordering_fields = ["cargo_nome", "cargo_codigo", "vagas"]
    lookup_url_kwarg = "cargo_uuid"

    def _get_processo(
        self, pk: str | UUID | None
    ) -> ProcessoConvocacao | None:
        """Retorna processo de convocação pela PK."""
        if pk is None:
            return None
        return ProcessoConvocacaoRepository.carregar_instancia_por_pk(pk)

    def list(
        self,
        request: Request,
        processo_pk: str | None = None,
    ) -> Response:
        processo = self._get_processo(processo_pk)
        if not processo:
            return Response(
                {"error": "Processo de convocação não encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(CargoProcessoRepository.listar_por_processo(processo))

    def create(
        self,
        request: Request,
        processo_pk: str | None = None,
    ) -> Response:
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

        serializador_corpo = ProcessoCargosDadosSerializer(data=request.data)
        serializador_corpo.is_valid(raise_exception=True)
        corpo_resposta = CargosProcessoService.substituir_cargos_processo(
            processo=processo,
            dados_validados=serializador_corpo.validated_data,
        )
        if "erros" in corpo_resposta:
            return Response(
                corpo_resposta, status=status.HTTP_207_MULTI_STATUS
            )

        return Response(corpo_resposta, status=status.HTTP_200_OK)

    def destroy(
        self,
        request: Request,
        processo_pk: str | None = None,
        cargo_uuid: str | None = None,
    ) -> Response:
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

        if not CargoProcessoRepository.obter_por_processo_e_uuid(
            processo, cargo_uuid
        ):
            return Response(
                {"error": "Cargo não encontrado para este processo"},
                status=status.HTTP_404_NOT_FOUND,
            )

        CargoProcessoRepository.excluir_por_processo_e_uuid(
            processo, cargo_uuid
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
