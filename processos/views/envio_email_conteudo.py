"""
View para templates de conteúdo de e-mail por tipo (somente leitura e edição).
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets

from processos.models import EnvioEmailConteudo
from processos.serializers import (
    EnvioEmailConteudoSerializer,
    EnvioEmailConteudoUpdateSerializer,
)


class EnvioEmailConteudoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """
    GET   /api/v1/envio-email-conteudo/?tipo=CONVOCACAO -> lista (filtro
    opcional
    por tipo)
    GET   /api/v1/envio-email-conteudo/<uuid>/            -> detalhe
    PATCH /api/v1/envio-email-conteudo/<uuid>/            -> atualiza apenas o
    conteudo HTML

    Valores de tipo: CONVOCACAO, VAGAS, RESULTADO
    """

    queryset = EnvioEmailConteudo.objects.all().order_by("tipo")
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo"]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    http_method_names = ["get", "patch", "head", "options"]
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ("update", "partial_update"):
            return EnvioEmailConteudoUpdateSerializer
        return EnvioEmailConteudoSerializer
