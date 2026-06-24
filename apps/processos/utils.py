"""Utilitários da API de processos."""

from __future__ import annotations

from typing import Any

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

PAGINA_PADRAO = 1
TAMANHO_PAGINA_PADRAO = 10


class CustomPagination(PageNumberPagination):
    """Paginação com ``count``, ``page``, ``page_size`` e ``results``."""

    page = PAGINA_PADRAO
    page_size = TAMANHO_PAGINA_PADRAO
    page_size_query_param = "page_size"

    def get_paginated_response(self, data: list[Any]) -> Response:
        """Monta resposta paginada no formato padrão SIGLA.

        Args:
            self: Instância do objeto.
            data: Dados de entrada.

        Returns:
            Resposta HTTP com o resultado da operação.
        """
        return Response(
            {
                "links": {
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
                "count": self.page.paginator.count,  # type: ignore[attr-defined]
                "page": int(self.request.GET.get("page", PAGINA_PADRAO)),
                "page_size": int(
                    self.request.GET.get("page_size", self.page_size)
                ),
                "results": data,
            }
        )
