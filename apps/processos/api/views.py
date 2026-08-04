"""Views de processos de convocação."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from cargos.repository import CargoProcessoRepository
from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from processos.constants import (
    CONCURSO_SITUACAO_EM_ANDAMENTO,
    ERROR_CANDIDATOS_PENDENTES_ESCOLHA,
    ERROR_PROCESSO_JA_CANCELADO,
    ERROR_PROCESSO_JA_FINALIZADO,
    ERROR_PROCESSO_NAO_PODE_EDITAR,
    TIPO_ESCOLHA_CHOICES,
)
from processos.models import ProcessoConvocacao
from processos.repository import ProcessoConvocacaoRepository
from processos.serializers import (
    ProcessoConvocacaoCreateSerializer,
    ProcessoConvocacaoListSerializer,
    ProcessoConvocacaoPassoSerializer,
    ProcessoConvocacaoSelectSerializer,
    ProcessoConvocacaoSerializer,
    ProcessoConvocacaoUpdateSerializer,
)
from processos.services import ConcursosApiService, EscolhasApiService
from processos.services.exceptions import ConcursoServiceError
from processos.services.processo_service import (
    ProcessoConvocacaoService,
    ProcessoServiceError,
)
from processos.utils import CustomPagination
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from sigla_sdk.context import get_correlation_id

logger = logging.getLogger(__name__)

STATUS_EM_ANDAMENTO = "EM_ANDAMENTO"
STATUS_FINALIZADO = "FINALIZADO"
STATUS_CANCELADO = "CANCELADO"


class ProcessoConvocacaoViewSet(viewsets.ModelViewSet):
    """ViewSet para gerenciar processos de convocação."""

    queryset = ProcessoConvocacao.objects.filter(
        esta_ativo=True
    ).prefetch_related("cargos_processo")
    serializer_class = ProcessoConvocacaoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["concurso_uuid", "status"]
    search_fields = ["concurso_nome", "descricao"]
    ordering_fields = ["data_convocacao", "data_corte_vagas", "criado_em"]
    ordering = ["-criado_em"]
    pagination_class = CustomPagination

    def get_queryset(self) -> QuerySet[ProcessoConvocacao]:
        """Aplica filtros por data de convocação e cargo."""
        repo = ProcessoConvocacaoRepository
        queryset = ProcessoConvocacao.objects.filter(
            esta_ativo=True
        ).prefetch_related("cargos_processo")

        data_inicio = self.request.query_params.get("data_convocacao_inicio")
        data_fim = self.request.query_params.get("data_convocacao_fim")

        if data_inicio:
            try:
                data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
                queryset = repo.aplicar_filtro_data_convocacao_gte(
                    queryset, data_inicio
                )
            except ValueError:
                pass

        if data_fim:
            try:
                data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
                queryset = repo.aplicar_filtro_data_convocacao_lte(
                    queryset, data_fim
                )
            except ValueError:
                pass

        cargo_uuid = self.request.query_params.get("cargo_uuid")
        if cargo_uuid:
            try:
                uuid.UUID(cargo_uuid)
                queryset = repo.aplicar_filtro_cargo_uuid(
                    queryset, uuid.UUID(cargo_uuid)
                )
            except ValueError:
                pass

        return queryset

    def get_serializer_class(self) -> type[BaseSerializer]:
        """Retorna a classe de serializer conforme a action."""
        if self.action == "create":
            return ProcessoConvocacaoCreateSerializer
        elif self.action == "list":
            if self.request.query_params.get("formato") == "select":
                return ProcessoConvocacaoSelectSerializer
            return ProcessoConvocacaoListSerializer
        elif self.action in ["update", "partial_update"]:
            return ProcessoConvocacaoUpdateSerializer
        return ProcessoConvocacaoSerializer

    def perform_create(self, serializer: BaseSerializer) -> None:
        """Salva o processo e sinaliza EM_ANDAMENTO para o concurso."""
        processo = serializer.save()
        try:
            ConcursosApiService().atualizar_situacao(
                concurso_uuid=str(processo.concurso_uuid),
                situacao=CONCURSO_SITUACAO_EM_ANDAMENTO,
            )
        except ConcursoServiceError:
            logger.exception(
                "Falha ao atualizar situação do concurso para EM_ANDAMENTO",
                extra={
                    "concurso_uuid": str(processo.concurso_uuid),
                    "processo_uuid": str(processo.uuid),
                    "correlation_id": get_correlation_id(),
                },
            )

    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Lista processos paginados ou em formato select."""
        logger.info(
            "Iniciando lista de processos de convocação",
            extra={
                "params": request.query_params,
                "correlation_id": get_correlation_id(),
                "user": request.user,
                "path": request.path,
                "method": request.method,
            },
        )
        queryset = self.filter_queryset(self.get_queryset())
        if request.query_params.get("formato") == "select":
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        processos = ProcessoConvocacaoRepository.serializar_queryset(queryset)
        page = self.paginate_queryset(processos)
        if page is not None:
            return self.get_paginated_response(page)

        return Response(processos)

    @action(detail=False, methods=["get"], url_path="filtros")
    def filtros(self, request: Request) -> Response:
        """Retorna opções de filtro (concursos, cargos, tipos de escolha)."""
        todos_processos = ProcessoConvocacaoRepository.listar_opcoes_concurso()
        concursos_unicos = {}
        for processo in todos_processos:
            concurso_uuid = processo["concurso_uuid"]
            if concurso_uuid not in concursos_unicos:
                concursos_unicos[concurso_uuid] = {
                    "value": concurso_uuid,
                    "label": processo["concurso_nome"],
                }

        todos_cargos = CargoProcessoRepository.listar_opcoes_filtro()
        cargos_unicos = {}
        for cargo in todos_cargos:
            if cargo["cargo_nome"] not in cargos_unicos:
                cargos_unicos[cargo["cargo_nome"]] = cargo

        tipos_escolha = [
            {"value": choice[0], "label": choice[1]}
            for choice in TIPO_ESCOLHA_CHOICES
        ]

        resultado = {
            "concursos": list(concursos_unicos.values()),
            "cargos": [
                {"value": cargo["cargo_uuid"], "label": cargo["cargo_nome"]}
                for cargo in cargos_unicos.values()
            ],
            "tipos_escolha": tipos_escolha,
        }

        return Response(resultado)

    @action(detail=True, methods=["post"], url_path="finalizar")
    def finalizar(self, request: Request, pk: str | None = None) -> Response:
        """Finaliza processo após validar escolhas no MS-Escolhas."""
        processo = self.get_object()
        logger.info(
            "Iniciando finalização de processo de convocação",
            extra={
                "processo_uuid": processo.uuid,
                "processo_status": processo.status,
                "correlation_id": get_correlation_id(),
                "user": request.user,
                "path": request.path,
                "method": request.method,
            },
        )

        if processo.status == STATUS_FINALIZADO:
            return Response(
                {"detail": ERROR_PROCESSO_JA_FINALIZADO},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if processo.status == STATUS_CANCELADO:
            return Response(
                {"detail": ERROR_PROCESSO_JA_CANCELADO},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if processo.status != STATUS_EM_ANDAMENTO:
            return Response(
                {
                    "detail": "Apenas processos em andamento podem ser finalizados."  # noqa: E501
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Candidatos do processo = união dos candidatos_uuids de todos os
        # cargos (mesma lista da tela e do banco)
        habilitados_uuids = {
            str(uuid)
            for cargo in CargoProcessoRepository.listar_por_processo(processo)
            for uuid in (cargo.get("candidatos_uuids") or [])
        }

        # Quem fez escolha no concurso (MS-Escolha: escolha, reconvocação ou não escolha)  # noqa: E501
        try:
            com_escolha = set(
                EscolhasApiService().buscar_candidatos_com_escolha(
                    str(processo.concurso_uuid)
                )
            )
        except Exception as exc:
            logger.exception(
                "Erro ao buscar escolhas para finalização: %s", exc
            )
            return Response(
                {"detail": "Erro ao consultar escolhas dos candidatos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pendentes = habilitados_uuids - com_escolha
        if pendentes:
            logger.info(
                "Candidatos pendentes de escolha",
                extra={
                    "processo_uuid": processo.uuid,
                    "correlation_id": get_correlation_id(),
                    "pendentes": len(pendentes),
                    "habilitados_uuids": len(habilitados_uuids),
                    "com_escolha": len(com_escolha),
                },
            )
            return Response(
                {"detail": ERROR_CANDIDATOS_PENDENTES_ESCOLHA},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ProcessoConvocacaoRepository.atualizar_status(
            processo, STATUS_FINALIZADO
        )
        serializer = ProcessoConvocacaoSerializer(processo)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Atualiza o processo e bloqueia alterações se estiver finalizado."""
        instance = self.get_object()
        if instance.status == STATUS_FINALIZADO:
            return Response(
                {"detail": ERROR_PROCESSO_NAO_PODE_EDITAR},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().update(request, *args, **kwargs)

    def partial_update(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Response:
        """Bloqueia alteração parcial quando processo está finalizado."""
        instance = self.get_object()
        if instance.status == STATUS_FINALIZADO:
            return Response(
                {"detail": ERROR_PROCESSO_NAO_PODE_EDITAR},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=["patch"], url_path="passo")
    def atualizar_passo(
        self, request: Request, pk: str | None = None
    ) -> Response:
        """Executa a atualização do passo da convocação."""
        processo = self.get_object()
        serializer = ProcessoConvocacaoPassoSerializer(
            processo,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            ProcessoConvocacaoSerializer(processo).data,
            status=status.HTTP_200_OK,
        )

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Exclui processo e limpa dependências nos microsserviços."""
        processo = self.get_object()
        str(processo.uuid)

        if not processo.pode_deletar():
            return Response(
                {"detail": "Processo não pode ser deletado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            ProcessoConvocacaoService().excluir_processo_e_dependencias(
                processo=processo,
            )
        except ProcessoServiceError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
