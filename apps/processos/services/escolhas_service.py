"""Serviço para comunicação com o microserviço de Escolhas (MS-Escolha).

Usado na finalização do processo para validar se todos os convocados fizeram
escolha.
"""

import logging
from urllib.parse import urlencode

from django.conf import settings
from processos.services.exceptions import EscolhasServiceError
from sigla_sdk.context import get_correlation_id
from sigla_sdk.http.api_client import http_client

logger = logging.getLogger(__name__)


class EscolhasApiService:
    """Define EscolhasApiService."""

    TIMEOUT_SEGUNDOS = 30
    CAMINHO_ESCOLHAS = "/api/v1/escolhas/"
    # Qualquer situação (escolha, reconvocação, nao-escolha) = candidato
    # respondeu. Só pendente = sem registro.
    SITUACOES_COM_ESCOLHA = "escolha,reconvocacao,nao-escolha"
    TAMANHO_PAGINA = 10000

    def __init__(
        self,
    ) -> None:
        """Inicializa cliente HTTP do MS-Escolha."""
        self.base_url = settings.ESCOLHAS_API_URL.rstrip("/")
        self.timeout_seconds = self.TIMEOUT_SEGUNDOS
        self.headers: dict[str, str] = {
            "Accept": "application/json",
            settings.API_KEY_HEADER: settings.ESCOLHAS_API_KEY,
        }

    def buscar_candidatos_com_escolha(self, concurso_uuid: str) -> list[str]:
        """Lista candidatos com escolha registrada no MS-Escolha."""
        if not self.base_url:
            logger.warning(
                "ESCOLHAS_API_URL não configurada; retornando lista vazia."
            )
            return []
        parametros = {
            "concurso_uuid": concurso_uuid,
            "situacao__in": self.SITUACOES_COM_ESCOLHA,
            "page_size": self.TAMANHO_PAGINA,
        }
        consulta = urlencode(parametros)
        url = f"{self.base_url}{self.CAMINHO_ESCOLHAS.rstrip('/')}/?{consulta}"

        logger.info(
            "Buscando candidatos com escolha",
            extra={
                "concurso_uuid": concurso_uuid,
                "correlation_id": get_correlation_id(),
                "url": url,
                "params": parametros,
                "method": "GET",
            },
        )
        try:
            resposta = http_client.get(
                url,
                timeout=self.timeout_seconds,
                headers=self.headers,
            )
            resposta.raise_for_status()
            dados = resposta.json()
        except Exception as exc:
            logger.exception(
                "Erro ao buscar escolhas no MS-Escolha (concurso_uuid=%s): %s",
                concurso_uuid,
                exc,
            )
            raise

        if isinstance(dados, list):
            registros = dados
        elif isinstance(dados, dict) and "results" in dados:
            registros = dados["results"]
            proxima_pagina = dados.get("next")
            if proxima_pagina:
                logger.warning(
                    "MS-Escolha retornou paginação; apenas primeira página considerada (concurso_uuid=%s)",  # noqa: E501
                    concurso_uuid,
                )
        else:
            registros = []

        candidato_uuids = []
        for registro in registros:
            candidato_uuid = registro.get("candidato_uuid")
            if candidato_uuid is not None:
                candidato_uuids.append(str(candidato_uuid))
        logger.info(
            "Candidatos com escolha encontrados",
            extra={
                "concurso_uuid": concurso_uuid,
                "correlation_id": get_correlation_id(),
                "url": url,
                "params": parametros,
                "method": "GET",
            },
        )
        return candidato_uuids

    def excluir_lotes_vagas_por_processo(self, processo_uuid: str) -> dict:
        """Remove lotes de vagas do processo no MS-Escolha."""
        if not self.base_url:
            raise ValueError("ESCOLHAS_API_URL não configurada")

        url = f"{self.base_url}/api/v1/vagas-escolas/por-processo/"
        parametros = {"processo_uuid": processo_uuid}
        logger.info(
            "Excluindo lotes de vagas no MS-Escolha",
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
            raise EscolhasServiceError(
                f"Falha ao conectar no MS-Escolha: {str(exc)}"
            ) from exc

        if resposta.status_code != 200:
            raise EscolhasServiceError(
                f"MS-Escolha retornou status {resposta.status_code} ao excluir lotes de vagas: {resposta.text}"  # noqa: E501
            )
        logger.info(
            "Lotes de vagas excluídos por processo",
            extra={
                "correlation_id": get_correlation_id(),
                "processo_uuid": processo_uuid,
                "status_code": resposta.status_code,
                "response": resposta.json(),
                "method": "DELETE",
                "url": url,
                "params": parametros,
                "headers": self.headers.keys(),
            },
        )
        return resposta.json() if resposta.content else {}
