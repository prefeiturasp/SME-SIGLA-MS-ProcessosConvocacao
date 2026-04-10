"""
Configuração e requisições à API do MS-Candidatos (habilitados por processo).
"""
import logging
from typing import Any
from urllib.parse import urlencode

from django.conf import settings

from processos.api_client import http_client
from processos.middlewares import get_correlation_id
from processos.services.exceptions import CandidatosServiceError


logger = logging.getLogger(__name__)


class CandidatosApiService:
    PATH_HABILITADOS = '/api/v1/habilitados/'
    FIELDS_HABILITADOS = (
        'candidato__nome,candidato__registro_funcional,candidato__email,candidato__uuid,'
        'descricao_cargo,codigo_cargo,classificacao,classificacao_pcd,classificacao_nna,categoria_efetiva', 
        'candidato'
    )
    TIMEOUT_SEGUNDOS = 30

    @property
    def _candidatos_api_url(self) -> str:
        return getattr(settings, 'CANDIDATOS_API_URL', '').rstrip('/')

    def _url_habilitados_por_processo(self, processo_uuid: str) -> str:
        """Monta a URL para buscar habilitados do processo no MS-Candidatos."""
        params = {
            'processo_uuid': processo_uuid,
            'foi_convocado': 'true',
            #'fields': self.FIELDS_HABILITADOS,
        }
        base = self._candidatos_api_url or ''
        path = self.PATH_HABILITADOS.rstrip('/')
        query = urlencode(params)
        return f"{base}{path}/?{query}"

    def buscar_habilitados_por_processo(self, processo_uuid: str) -> list[dict[str, Any]]:
        """
        Busca no MS-Candidatos os habilitados do processo (foi_convocado=true).

        URL: GET /api/v1/habilitados/?processo_uuid=<uuid>&foi_convocado=true
             &fields=candidato__nome,candidato__registro_funcional,candidato__email,
                     cargo_nome,classificacao

        Returns:
            Lista de registros retornados pela API (ex.: results ou lista direta).
        """
        if not self._candidatos_api_url:
            logger.warning('CANDIDATOS_API_URL não configurado; retornando lista vazia.')
            return []

        url = self._url_habilitados_por_processo(processo_uuid)
        headers = {'Accept': 'application/json'}
        logger.info(
            'Buscando habilitados por processo',
            extra={
                "processo_uuid": processo_uuid,
                "correlation_id": get_correlation_id(),
                "url": url,
                "headers": headers,
                "method": "GET",
            }
        )
        try:
            response = http_client.get(
                url,
                headers=headers,
                timeout=self.TIMEOUT_SEGUNDOS,
            )
            response.raise_for_status()
        except Exception as exc:
            logger.exception(
                'Erro ao buscar habilitados no MS-Candidatos (processo_uuid=%s): %s',
                processo_uuid,
                exc,
            )
            raise
        data = response.json()
        logger.info(
            'Habilitados encontrados',
            extra={                
                "processo_uuid": processo_uuid,
                "correlation_id": get_correlation_id(),
                "url": url,
                "headers": headers,
                "method": "GET",
                "data": str(data)[:200],  # Limitar tamanho do log
            }
        )
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and 'results' in data:
            return data['results']
        if isinstance(data, dict):
            return []
        return []

    def desconvocar_por_processo(self, processo_uuid: str) -> dict:
        """
        PATCH /api/v1/habilitados/desconvocar

        Payload:
        { "processo_uuid": "<uuid>"}
        """
        if not settings.CANDIDATOS_API_URL:
            raise ValueError('CANDIDATOS_API_URL não configurada')

        url = f"{settings.CANDIDATOS_API_URL}/api/v1/habilitados/desconvocar/"
        payload = {"processo_uuid": str(processo_uuid)}
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        logger.info(
            'Desconvocando candidatos no MS-Candidatos',
            extra={
                "correlation_id": get_correlation_id(),
                "method": "PATCH",
                "url": url,
                "payload": payload,
                "headers": headers,
                "processo_uuid": str(processo_uuid),
            },
        )
        try:
            response = http_client.patch(
                url,
                json=payload,
                headers=headers,
                timeout=self.TIMEOUT_SEGUNDOS,
            )
        except Exception as exc:
            raise CandidatosServiceError(f'Falha ao conectar no MS-Candidatos: {str(exc)}') from exc

        if response.status_code != 200:
            raise CandidatosServiceError(
                f'MS-Candidatos retornou status {response.status_code} ao desconvocar: {response.text}'
            )
        logger.info(
            'Candidatos desconvocados',
            extra={
                "correlation_id": get_correlation_id(),
                "method": "PATCH",
                "url": url,
                "payload": payload,
                "headers": headers,
                "processo_uuid": str(processo_uuid),
                "status_code": response.status_code,
                "response": response.json(),
            },
        )
        return response.json() if response.content else {}
