"""View para templates de conteúdo de e-mail por tipo."""

from __future__ import annotations

from uuid import UUID

from rest_framework import mixins, viewsets
from rest_framework.exceptions import NotFound
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from envio_email.models import EnvioEmailConteudo
from envio_email.repository import EnvioEmailConteudoRepository
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

    lookup_field = "uuid"
    lookup_url_kwarg = "uuid"
    http_method_names = ["get", "patch", "head", "options"]
    pagination_class = None

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action in ("update", "partial_update"):
            return EnvioEmailConteudoUpdateSerializer
        return EnvioEmailConteudoSerializer

    def get_object(self) -> EnvioEmailConteudo:
        conteudo = EnvioEmailConteudoRepository.carregar_instancia_por_uuid(
            UUID(self.kwargs[self.lookup_url_kwarg])
        )
        if conteudo is None:
            raise NotFound()
        return conteudo

    def list(self, request: Request, *args, **kwargs) -> Response:
        return Response(
            EnvioEmailConteudoRepository.listar(
                tipo=request.query_params.get("tipo")
            )
        )

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        conteudo = EnvioEmailConteudoRepository.obter_por_uuid(
            UUID(self.kwargs[self.lookup_url_kwarg])
        )
        if conteudo is None:
            raise NotFound()
        return Response(conteudo)
