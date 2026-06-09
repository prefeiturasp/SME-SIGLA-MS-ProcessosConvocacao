"""Requisições ao MS-Agenda (exclusão de agendas por processo de convocação)."""

import logging

from django.conf import settings
from sigla_sdk.context import get_correlation_id
from sigla_sdk.http.api_client import http_client

from processos.services.exceptions import AgendaServiceError

logger = logging.getLogger(__name__)


class AgendaApiService:
    """Define AgendaApiService."""
    TIMEOUT_SEGUNDOS = 30

    def excluir_agendas_por_processo(self, processo_uuid: str) -> dict:
        """DELETE /api/v1/agendas/por-processo/?processo_uuid=<uuid>.
        
        Args:
            self: Instância do objeto.
            processo_uuid: UUID do processo de convocação.
        
        Returns:
            Dicionário com os dados processados.
        
        Raises:
            AgendaServiceError: Se a integração com o MS-Agenda falhar.
        """
        url = f"{settings.AGENDA_API_URL}/api/v1/agendas/por-processo/"
        params = {"processo_uuid": processo_uuid}
        headers = {"Accept": "application/json"}
        logger.info(
            "Excluindo agendas no MS-Agenda",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "DELETE",
                "url": url,
                "params": params,
                "headers": headers,
                "processo_uuid": processo_uuid,
            },
        )
        try:
            response = http_client.delete(
                url,
                params=params,
                headers=headers,
                timeout=self.TIMEOUT_SEGUNDOS,
            )
        except Exception as exc:
            raise AgendaServiceError(
                f"Falha ao conectar no MS-Agenda: {str(exc)}"
            ) from exc

        if response.status_code != 200:
            raise AgendaServiceError(
                f"MS-Agenda retornou status {response.status_code} ao excluir agendas: {response.text}"  # noqa: E501
            )
        logger.info(
            "Agendas excluídas por processo",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "DELETE",
                "url": url,
                "params": params,
                "processo_uuid": processo_uuid,
                "status_code": response.status_code,
                "response": response.json(),
            },
        )
        return response.json() if response.content else {}
