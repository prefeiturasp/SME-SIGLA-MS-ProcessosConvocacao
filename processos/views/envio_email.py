"""
View para envio genérico de e-mails e listagem/detalhe do histórico.
"""

import logging

from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from sigla_sdk.context import get_correlation_id

from processos.models import EnvioEmail
from processos.serializers import (
    EnvioEmailDetalheSerializer,
    EnvioEmailEnvioSerializer,
    EnvioEmailSerializer,
)
from processos.services.envio_email_service import iniciar_processamento_envio

logger = logging.getLogger(__name__)


class EnvioEmailViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET  /api/v1/envio-email/         -> listagem do histórico
    GET  /api/v1/envio-email/<uuid>/  -> detalhe com candidatos
    POST /api/v1/envio-email/         -> inicia processamento de envio
    """

    queryset = EnvioEmail.objects.prefetch_related("candidatos").order_by(
        "-criado_em"
    )
    pagination_class = None
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"

    def get_serializer_class(self):
        if self.action == "retrieve":
            return EnvioEmailDetalheSerializer
        return EnvioEmailSerializer

    def create(self, request):
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

        data = serializer.validated_data
        try:
            envio = iniciar_processamento_envio(
                processo_uuid=data["processo_uuid"],
                processo_nome=data["processo_nome"],
                tipo=data["tipo"],
                conteudo=data.get("conteudo"),
            )
            return Response(
                {
                    "detail": "Processamento de envio iniciado com sucesso.",
                    "envio_email_uuid": str(envio.uuid),
                    "processo_uuid": str(data["processo_uuid"]),
                    "processo_nome": data["processo_nome"],
                    "tipo": data["tipo"],
                    "quantidade_candidatos": envio.quantidade_candidatos,
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
