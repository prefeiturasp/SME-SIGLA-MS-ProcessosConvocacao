"""
View para envio da carta de convocação por email e listagem/detalhe do histórico.
"""
import logging
from rest_framework import status, viewsets, mixins
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from processos.models import CartaConvocacaoHistorico
from processos.serializers import (
    CartaConvocacaoEnvioSerializer,
    CartaConvocacaoHistoricoSerializer,
    CartaConvocacaoHistoricoDetalheSerializer,
)
from processos.services.carta_convocacao_service import iniciar_processamento_envio
from processos.utils import CustomPagination
from processos.middlewares import get_correlation_id


logger = logging.getLogger(__name__)


class CartaConvocacaoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET  /api/v1/carta-convocacao/         -> listagem do histórico (processo_nome, processo_uuid, criado_em, quantidade_convocados).
    GET  /api/v1/carta-convocacao/<uuid>/  -> detalhe do histórico + candidatos (nome, rf, email, status, conteudo).
    POST /api/v1/carta-convocacao/         -> inicia o processamento (envio).
    """
    #permission_classes = [AllowAny]
    queryset = CartaConvocacaoHistorico.objects.prefetch_related('candidatos').order_by('-criado_em')
    pagination_class = CustomPagination
    lookup_field = 'uuid'
    lookup_url_kwarg = 'uuid'

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CartaConvocacaoHistoricoDetalheSerializer
        return CartaConvocacaoHistoricoSerializer

    def create(self, request):
        logger.info(
        'Iniciando processamento de envio da carta de convocação',
        extra={
            "processo_uuid": request.data.get('processo_uuid'),
            "processo_nome": request.data.get('processo_nome'),
            "data": request.data.get('data'),
            "correlation_id": get_correlation_id(),
            "user": request.user,
            "path": request.path,
            "method": request.method,
        }
    )
        serializer = CartaConvocacaoEnvioSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            historico = iniciar_processamento_envio(
                processo_uuid=data['processo_uuid'],
                processo_nome=data['processo_nome'],
                data=data['data'],
            )
            return Response(
                {
                    'detail': 'Processamento de envio iniciado com sucesso.',
                    'historico_uuid': str(historico.uuid),
                    'processo_uuid': str(data['processo_uuid']),
                    'processo_nome': data['processo_nome'],
                    'data': data['data'].strftime('%d-%m-%Y'),
                    'quantidade_candidatos': historico.quantidade_candidatos,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            logger.exception(
                'Erro ao iniciar processamento de envio da carta de convocação: %s',
                exc,
            )
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
