"""View para templates de conteúdo de e-mail por tipo."""

from __future__ import annotations

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.serializers import BaseSerializer

from envio_email.models import EnvioEmailConteudo
from envio_email.serializers import (
    EnvioEmailConteudoSerializer,
    EnvioEmailConteudoUpdateSerializer,
)


class EnvioEmailConteudoViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """CRUD parcial de templates HTML por tipo."""

    queryset = EnvioEmailConteudo.objects.all().order_by("tipo")
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["tipo"]
    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    http_method_names = ["get", "patch", "head", "options"]
    pagination_class = None

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action in ("update", "partial_update"):
            return EnvioEmailConteudoUpdateSerializer
        return EnvioEmailConteudoSerializer
