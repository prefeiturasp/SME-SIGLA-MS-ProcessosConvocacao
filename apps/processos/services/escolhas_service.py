"""Serviço para comunicação com o microserviço de Escolhas (MS-Escolha).

Usado na finalização do processo para validar se todos os convocados fizeram
escolha.
"""

import logging
from urllib.parse import urlencode

from django.conf import settings
from sigla_sdk.context import get_correlation_id
from sigla_sdk.http.api_client import http_client

from processos.services.exceptions import EscolhasServiceError

logger = logging.getLogger(__name__)


class EscolhasApiService:
    """Define EscolhasApiService."""

    TIMEOUT_SEGUNDOS = 30
    CAMINHO_ESCOLHAS = "/api/v1/escolhas/"
    # Qualquer situação (escolha, reconvocação, nao-escolha) = candidato respondeu. Só pendente = sem registro.  # noqa: E501
    SITUACOES_COM_ESCOLHA = "escolha,reconvocacao,nao-escolha"
    TAMANHO_PAGINA = 10000

    def _obter_url_base(self) -> str:
        """Obtém a URL base do MS-Escolha a partir das configurações."""
        url_base = getattr(settings, "ESCOLHAS_API_URL", "") or ""
        if not url_base.strip():
            logger.warning(
                "ESCOLHAS_API_URL não configurada; chamadas ao MS-Escolha podem falhar."  # noqa: E501
            )
            return ""
        return url_base.rstrip("/")

    def buscar_candidatos_com_escolha(self, concurso_uuid: str) -> list[str]:
        """Lista candidatos com escolha registrada no MS-Escolha."""
        url_base = self._obter_url_base()
        if not url_base:
            return []
        parametros = {
            "concurso_uuid": concurso_uuid,
            "situacao__in": self.SITUACOES_COM_ESCOLHA,
            "page_size": self.TAMANHO_PAGINA,
        }
        consulta = urlencode(parametros)
        url = f"{url_base}{self.CAMINHO_ESCOLHAS.rstrip('/')}/?{consulta}"

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
                timeout=self.TIMEOUT_SEGUNDOS,
                headers={"Accept": "application/json"},
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
        url_base = self._obter_url_base()
        if not url_base:
            raise ValueError("ESCOLHAS_API_URL não configurada")

        url = f"{url_base}/api/v1/vagas-escolas/por-processo/"
        parametros = {"processo_uuid": processo_uuid}
        cabecalhos = {"Accept": "application/json"}
        logger.info(
            "Excluindo lotes de vagas no MS-Escolha",
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
                "headers": cabecalhos,
            },
        )
        return resposta.json() if resposta.content else {}
