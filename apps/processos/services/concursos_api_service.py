"""Requisições ao MS-Concursos para atualização de situação do concurso."""

import logging

from django.conf import settings
from processos.services.exceptions import ConcursoServiceError
from sigla_sdk.context import get_correlation_id
from sigla_sdk.http.api_client import http_client

logger = logging.getLogger(__name__)


class ConcursosApiService:
    """Define ConcursosApiService."""

    TIMEOUT_SEGUNDOS = 30

    def __init__(self) -> None:
        """Inicializa cliente HTTP do MS-Concursos."""
        self.base_url = settings.CONCURSOS_API_URL.rstrip("/")
        self.timeout_seconds = self.TIMEOUT_SEGUNDOS
        self.headers: dict[str, str] = {
            "Accept": "application/json",
            settings.API_KEY_HEADER: settings.CONCURSOS_API_KEY,
        }

    def atualizar_situacao(self, concurso_uuid: str, situacao: str) -> dict:
        """PATCH /api/v1/concursos/<uuid>/atualizar-situacao/."""
        url = (
            f"{self.base_url}/api/v1/concursos/"
            f"{concurso_uuid}/atualizar-situacao/"
        )
        payload = {"situacao": situacao}
        logger.info(
            "Atualizando situação do concurso no MS-Concursos",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "PATCH",
                "url": url,
                "concurso_uuid": concurso_uuid,
                "situacao": situacao,
            },
        )
        try:
            resposta = http_client.patch(
                url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout_seconds,
            )
        except Exception as exc:
            raise ConcursoServiceError(
                f"Falha ao conectar no MS-Concursos: {str(exc)}"
            ) from exc

        if resposta.status_code != 200:
            raise ConcursoServiceError(
                f"MS-Concursos retornou status {resposta.status_code} "
                f"ao atualizar situação: {resposta.text}"
            )
        logger.info(
            "Situação do concurso atualizada",
            extra={
                "correlation_id": get_correlation_id(),
                "concurso_uuid": concurso_uuid,
                "situacao": situacao,
                "status_code": resposta.status_code,
            },
        )
        return resposta.json() if resposta.content else {}
