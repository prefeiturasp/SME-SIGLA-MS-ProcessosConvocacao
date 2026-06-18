"""ViewSet de cargos vinculados a um processo de convocação."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.request import Request
from rest_framework.response import Response

from cargos.models import CargoProcesso
from cargos.serializers import (
    CargoProcessoSerializer,
    ProcessoCargosDadosSerializer,
)
from cargos.services.cargos_service import CargosProcessoService
from processos.models import ProcessoConvocacao
from processos.models.constants import ERROR_PROCESSO_NAO_PODE_EDITAR

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
        try:
            return ProcessoConvocacao.objects.get(pk=pk)
        except ProcessoConvocacao.DoesNotExist:
            return None

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

        cargos = processo.cargos_processo.all()
        serializador = CargoProcessoSerializer(cargos, many=True)
        return Response(serializador.data)

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
        dados_validados = serializador_corpo.validated_data
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
            processo.save(update_fields=campos_atualizacao)

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
            return Response(corpo_resposta, status=status.HTTP_207_MULTI_STATUS)

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

        cargo = processo.cargos_processo.filter(uuid=cargo_uuid).first()
        if not cargo:
            return Response(
                {"error": "Cargo não encontrado para este processo"},
                status=status.HTTP_404_NOT_FOUND,
            )

        cargo.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
