"""Requisições ao MS-Agenda para exclusão de agendas por processo."""

import logging

from django.conf import settings
from processos.services.exceptions import AgendaServiceError
from sigla_sdk.context import get_correlation_id
from sigla_sdk.http.api_client import http_client

logger = logging.getLogger(__name__)


class AgendaApiService:
    """Define AgendaApiService."""

    TIMEOUT_SEGUNDOS = 30

    def excluir_agendas_por_processo(self, processo_uuid: str) -> dict:
        """DELETE /api/v1/agendas/por-processo/?processo_uuid=<uuid>."""
        url = f"{settings.AGENDA_API_URL}/api/v1/agendas/por-processo/"
        parametros = {"processo_uuid": processo_uuid}
        cabecalhos = {"Accept": "application/json"}
        logger.info(
            "Excluindo agendas no MS-Agenda",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "DELETE",
                "url": url,
                "params": parametros,
                "headers": cabecalhos,
                "processo_uuid": processo_uuid,
            },
        )
        try:
            resposta = http_client.delete(
                url,
                params=parametros,
                headers=cabecalhos,
                timeout=self.TIMEOUT_SEGUNDOS,
            )
        except Exception as exc:
            raise AgendaServiceError(
                f"Falha ao conectar no MS-Agenda: {str(exc)}"
            ) from exc

        if resposta.status_code != 200:
            raise AgendaServiceError(
                f"MS-Agenda retornou status {resposta.status_code} ao excluir agendas: {resposta.text}"  # noqa: E501
            )
        logger.info(
            "Agendas excluídas por processo",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "DELETE",
                "url": url,
                "params": parametros,
                "processo_uuid": processo_uuid,
                "status_code": resposta.status_code,
                "response": resposta.json(),
            },
        )
        return resposta.json() if resposta.content else {}
