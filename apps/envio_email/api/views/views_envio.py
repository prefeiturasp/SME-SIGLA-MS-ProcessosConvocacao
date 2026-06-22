"""View para envio genérico de e-mails e histórico."""

from __future__ import annotations

import logging
from uuid import UUID

from rest_framework import mixins, status, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from sigla_sdk.context import get_correlation_id

from envio_email.repository import EnvioEmailRepository
from envio_email.serializers import EnvioEmailEnvioSerializer
from envio_email.services.envio_email_service import iniciar_processamento_envio

logger = logging.getLogger(__name__)


class EnvioEmailViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Listagem, detalhe e disparo de envio de e-mails por processo."""

    pagination_class = None
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def list(self, request: Request, *args, **kwargs) -> Response:
        return Response(EnvioEmailRepository.listar_todos())

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        envio = EnvioEmailRepository.obter_por_uuid(
            UUID(self.kwargs[self.lookup_url_kwarg])
        )
        if envio is None:
            raise NotFound()
        return Response(envio)

    def create(self, request: Request) -> Response:
        logger.info(
            "Iniciando processamento de envio de e-mail",
            extra={
                "processo_uuid": request.data.get("processo_uuid"),
                "processo_nome": request.data.get("processo_nome"),
                "tipo": request.data.get("tipo"),
                "correlation_id": get_correlation_id(),
                "user": request.user,
                "path": request.path,
                "method": request.method,
            },
        )
        serializer = EnvioEmailEnvioSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        dados_validados = serializer.validated_data
        try:
            envio = iniciar_processamento_envio(
                processo_uuid=dados_validados["processo_uuid"],
                processo_nome=dados_validados["processo_nome"],
                tipo=dados_validados["tipo"],
                conteudo=dados_validados.get("conteudo"),
                assunto=dados_validados.get("assunto"),
            )
            return Response(
                {
                    "detail": "Processamento de envio iniciado com sucesso.",
                    "envio_email_uuid": str(envio["uuid"]),
                    "processo_uuid": str(dados_validados["processo_uuid"]),
                    "processo_nome": dados_validados["processo_nome"],
                    "tipo": dados_validados["tipo"],
                    "quantidade_candidatos": envio["quantidade_candidatos"],
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            logger.exception(
                "Erro ao iniciar processamento de envio de e-mail: %s", exc
            )
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
