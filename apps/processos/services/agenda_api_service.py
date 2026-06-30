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

    def __init__(
        self,
    ) -> None:
        """Inicializa cliente HTTP do MS-Agenda."""
        self.base_url = settings.AGENDA_API_URL.rstrip("/")
        self.timeout_seconds = self.TIMEOUT_SEGUNDOS
        self.headers: dict[str, str] = {
            "Accept": "application/json",
            settings.API_KEY_HEADER: settings.AGENDA_API_KEY,
        }

    def excluir_agendas_por_processo(self, processo_uuid: str) -> dict:
        """DELETE /api/v1/agendas/por-processo/?processo_uuid=<uuid>."""
        url = f"{self.base_url}/api/v1/agendas/por-processo/"
        parametros = {"processo_uuid": processo_uuid}
        logger.info(
            "Excluindo agendas no MS-Agenda",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "DELETE",
                "url": url,
                "params": parametros,
                "headers": self.headers.keys(),
                "processo_uuid": processo_uuid,
            },
        )
        try:
            resposta = http_client.delete(
                url,
                params=parametros,
                headers=self.headers,
                timeout=self.timeout_seconds,
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
