"""ViewSet de cargos vinculados a um processo de convocação."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.request import Request
from rest_framework.response import Response

from processos.models import CargoProcesso, ProcessoConvocacao
from processos.models.constants import ERROR_PROCESSO_NAO_PODE_EDITAR
from processos.serializers import (
    CargoProcessoSerializer,
    ProcessoCargosPayloadSerializer,
)
from processos.services.cargos_service import CargosProcessoService

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
        """Busca processo pelo UUID da URL ou retorna None.

        Args:
            self: Instância do objeto.
            pk: Chave primária do recurso.

        Returns:
            Instância do processo de convocação.

        Raises:
            Nenhuma exceção específica documentada.
        """
        try:
            return ProcessoConvocacao.objects.get(pk=pk)
        except ProcessoConvocacao.DoesNotExist:
            return None

    def list(
        self,
        request: Request,
        processo_pk: str | None = None,
    ) -> Response:
        """Lista cargos do processo.

        Args:
            self: Instância do objeto.
            request: Requisição HTTP recebida.
            processo_pk: Parâmetro processo pk da operação.

        Returns:
            Resposta HTTP com o resultado da operação.

        Raises:
            Nenhuma exceção específica documentada.
        """
        processo = self._get_processo(processo_pk)
        if not processo:
            return Response(
                {"error": "Processo de convocação não encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )

        cargos = processo.cargos_processo.all()
        serializer = CargoProcessoSerializer(cargos, many=True)
        return Response(serializer.data)

    def create(
        self,
        request: Request,
        processo_pk: str | None = None,
    ) -> Response:
        """Substitui todos os cargos e porcentagens do processo.

        Args:
            self: Instância do objeto.
            request: Requisição HTTP recebida.
            processo_pk: Parâmetro processo pk da operação.

        Returns:
            Resposta HTTP com o resultado da operação.

        Raises:
            Nenhuma exceção específica documentada.
        """
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

        update_fields: list[str] = []
        if (
            "porcentagem_nna" in payload
            and payload["porcentagem_nna"] != processo.porcentagem_nna
        ):
            processo.porcentagem_nna = payload["porcentagem_nna"]
            update_fields.append("porcentagem_nna")
        if (
            "porcentagem_pcd" in payload
            and payload["porcentagem_pcd"] != processo.porcentagem_pcd
        ):
            processo.porcentagem_pcd = payload["porcentagem_pcd"]
            update_fields.append("porcentagem_pcd")
        if update_fields:
            processo.save(update_fields=update_fields)

        result = CargosProcessoService.salvar_cargos(
            processo=processo, cargos_data=cargos_data
        )

        body: dict[str, Any] = {
            "success": True,
            "cargos_criados": len(result.cargos_criados),
            "cargos_atualizados": len(result.cargos_atualizados),
            "cargos_removidos": result.cargos_removidos,
            "cargos": result.cargos,
        }
        if result.erros:
            body["erros"] = result.erros
            return Response(body, status=status.HTTP_207_MULTI_STATUS)

        return Response(body, status=status.HTTP_200_OK)

    def destroy(
        self,
        request: Request,
        processo_pk: str | None = None,
        cargo_uuid: str | None = None,
    ) -> Response:
        """Remove um cargo do processo.

        Args:
            self: Instância do objeto.
            request: Requisição HTTP recebida.
            processo_pk: Parâmetro processo pk da operação.
            cargo_uuid: Parâmetro cargo uuid da operação.

        Returns:
            Resposta HTTP com o resultado da operação.

        Raises:
            Nenhuma exceção específica documentada.
        """
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
