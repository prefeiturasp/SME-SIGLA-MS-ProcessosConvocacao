"""Cliente HTTP do MS-Candidatos (habilitados por processo)."""

import logging
from typing import Any
from urllib.parse import urlencode

from django.conf import settings
from processos.services.exceptions import CandidatosServiceError
from sigla_sdk.context import get_correlation_id
from sigla_sdk.http.api_client import http_client

logger = logging.getLogger(__name__)


class CandidatosApiService:
    """Define CandidatosApiService."""

    CAMINHO_HABILITADOS = "/api/v1/habilitados/"
    CAMPOS_HABILITADOS = (
        "candidato__nome,candidato__registro_funcional,"
        "candidato__email,candidato__uuid,"
        "descricao_cargo,codigo_cargo,classificacao,classificacao_pcd,"
        "classificacao_nna,categoria_efetiva,candidato",
    )
    TIMEOUT_SEGUNDOS = 30

    def __init__(
        self,
    ) -> None:
        """Inicializa cliente HTTP do MS-Candidatos."""
        self.base_url = settings.CANDIDATOS_API_URL.rstrip("/")
        self.timeout_seconds = self.TIMEOUT_SEGUNDOS
        self.headers: dict[str, str] = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            settings.API_KEY_HEADER: settings.CANDIDATOS_API_KEY,
        }

    def _url_habilitados_por_processo(self, processo_uuid: str) -> str:
        """Monta a URL para buscar habilitados do processo no MS-Candidatos."""
        parametros = {
            "processo_uuid": processo_uuid,
            "foi_convocado": "true",
        }
        caminho = self.CAMINHO_HABILITADOS.rstrip("/")
        consulta = urlencode(parametros)
        return f"{self.base_url}{caminho}/?{consulta}"

    def buscar_habilitados_por_processo(
        self, processo_uuid: str
    ) -> list[dict[str, Any]]:
        """Busca habilitados do processo no MS-Candidatos."""
        if not self.base_url:
            logger.warning(
                "CANDIDATOS_API_URL não configurado; retornando lista vazia."
            )
            return []

        url = self._url_habilitados_por_processo(processo_uuid)
        logger.info(
            "Buscando habilitados por processo",
            extra={
                "processo_uuid": processo_uuid,
                "correlation_id": get_correlation_id(),
                "url": url,
                "headers": self.headers.keys(),
                "method": "GET",
            },
        )
        try:
            resposta = http_client.get(
                url,
                headers=self.headers,
                timeout=self.timeout_seconds,
            )
            resposta.raise_for_status()
        except Exception as exc:
            logger.exception(
                "Erro ao buscar habilitados no MS-Candidatos (processo_uuid=%s): %s",  # noqa: E501
                processo_uuid,
                exc,
            )
            raise
        dados = resposta.json()
        logger.info(
            "Habilitados encontrados",
            extra={
                "processo_uuid": processo_uuid,
                "correlation_id": get_correlation_id(),
                "url": url,
                "headers": self.headers.keys(),
                "method": "GET",
                "data": str(dados)[:200],
            },
        )
        if isinstance(dados, list):
            return dados
        if isinstance(dados, dict) and "results" in dados:
            return dados["results"]
        if isinstance(dados, dict):
            return []
        return []

    def desconvocar_por_processo(self, processo_uuid: str) -> dict:
        """PATCH /api/v1/habilitados/desconvocar."""
        if not self.base_url:
            raise ValueError("CANDIDATOS_API_URL não configurada")

        url = f"{self.base_url}/api/v1/habilitados/desconvocar/"
        corpo_requisicao = {"processo_uuid": str(processo_uuid)}
        logger.info(
            "Desconvocando candidatos no MS-Candidatos",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "PATCH",
                "url": url,
                "payload": corpo_requisicao,
                "headers": self.headers.keys(),
                "processo_uuid": str(processo_uuid),
            },
        )
        try:
            resposta = http_client.patch(
                url,
                json=corpo_requisicao,
                headers=self.headers,
                timeout=self.timeout_seconds,
            )
        except Exception as exc:
            raise CandidatosServiceError(
                f"Falha ao conectar no MS-Candidatos: {str(exc)}"
            ) from exc

        if resposta.status_code != 200:
            raise CandidatosServiceError(
                f"MS-Candidatos retornou status {resposta.status_code} ao desconvocar: {resposta.text}"  # noqa: E501
            )
        logger.info(
            "Candidatos desconvocados",
            extra={
                "correlation_id": get_correlation_id(),
                "method": "PATCH",
                "url": url,
                "payload": corpo_requisicao,
                "headers": self.headers.keys(),
                "processo_uuid": str(processo_uuid),
                "status_code": resposta.status_code,
                "response": resposta.json(),
            },
        )
        return resposta.json() if resposta.content else {}
