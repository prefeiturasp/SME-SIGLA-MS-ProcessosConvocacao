"""
Serviço para comunicação com o microserviço de Escolhas (MS-Escolha).
Usado na finalização do processo para validar se todos os convocados fizeram escolha.
"""
import logging
from typing import List
from urllib.parse import urlencode

from django.conf import settings
from processos.api_client import http_client
from processos.middlewares import get_correlation_id
from processos.services.exceptions import EscolhasServiceError

logger = logging.getLogger(__name__)


class EscolhasApiService:
    DEFAULT_TIMEOUT = 30
    TIMEOUT_SEGUNDOS = 30
    PATH_ESCOLHAS = '/api/v1/escolhas/'
    # Qualquer situação (escolha, reconvocação, nao-escolha) = candidato respondeu. Só pendente = sem registro.
    SITUACOES_COM_ESCOLHA = 'escolha,reconvocacao,nao-escolha'
    PAGE_SIZE = 10000

    def _get_base_url(self) -> str:
        """Obtém a URL base do MS-Escolha a partir das configurações."""
        base_url = getattr(settings, 'ESCOLHAS_API_URL', '') or ''
        if not base_url.strip():
            logger.warning('ESCOLHAS_API_URL não configurada; chamadas ao MS-Escolha podem falhar.')
            return ''
        return base_url.rstrip('/')

    def buscar_candidatos_com_escolha(self, concurso_uuid: str) -> List[str]:
        """
        Busca no MS-Escolha os candidato_uuid que já têm registro de resposta (escolha, reconvocação ou não escolha).
        Pendente = candidato sem nenhum registro; qualquer situação conta como "respondeu".

        Args:
            concurso_uuid: UUID do concurso (o ProcessoConvocacao tem concurso_uuid).

        Returns:
            Lista de candidato_uuid (strings) que possuem registro no concurso (qualquer situação).
            Lista vazia se ESCOLHAS_API_URL não estiver configurada ou em caso de erro (logado).
        """
        base_url = self._get_base_url()
        if not base_url:
            return []
        params = {
            'concurso_uuid': concurso_uuid,
            'situacao__in': self.SITUACOES_COM_ESCOLHA,
            'page_size': self.PAGE_SIZE,
        }
        query = urlencode(params)
        url = f"{base_url}{self.PATH_ESCOLHAS.rstrip('/')}/?{query}"

        logger.info(
            'Buscando candidatos com escolha',
            extra={
                "concurso_uuid": concurso_uuid,
                "correlation_id": get_correlation_id(),
                "url": url,
                "params": params,
                "method": "GET",
            }
        )
        try:
            response = http_client.get(url, timeout=self.DEFAULT_TIMEOUT, headers={'Accept': 'application/json'})
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            logger.exception(
                'Erro ao buscar escolhas no MS-Escolha (concurso_uuid=%s): %s',
                concurso_uuid,
                exc,
            )
            raise

        # Suportar listagem paginada (results) ou lista direta
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict) and 'results' in data:
            items = data['results']
            # Se houver paginação, considerar apenas a primeira página (page_size grande reduz isso)
            next_page = data.get('next')
            if next_page:
                logger.warning(
                    'MS-Escolha retornou paginação; apenas primeira página considerada (concurso_uuid=%s)',
                    concurso_uuid,
                )
        else:
            items = []

        candidato_uuids = []
        for item in items:
            uid = item.get('candidato_uuid')
            if uid is not None:
                candidato_uuids.append(str(uid))
        logger.info(
            'Candidatos com escolha encontrados',
            extra={
                "concurso_uuid": concurso_uuid,
                "correlation_id": get_correlation_id(),
                "url": url,
                "params": params,
                "method": "GET",
            }
        )
        return candidato_uuids

    def excluir_lotes_vagas_por_processo(self, processo_uuid: str) -> dict:
        """
        Remove lotes de vagas (e vagas em cascata) do processo no MS-Escolha.

        Endpoint:
          DELETE /api/v1/vagas-escolas/por-processo/?processo_uuid=<uuid>
        """
        base_url = self._get_base_url()
        if not base_url:
            raise ValueError('ESCOLHAS_API_URL não configurada')

        url = f"{base_url}/api/v1/vagas-escolas/por-processo/"
        params = {'processo_uuid': processo_uuid}
        headers = {'Accept': 'application/json'}
        logger.info(
            'Excluindo lotes de vagas no MS-Escolha',
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
            raise EscolhasServiceError(f'Falha ao conectar no MS-Escolha: {str(exc)}') from exc

        if response.status_code != 200:
            raise EscolhasServiceError(
                f'MS-Escolha retornou status {response.status_code} ao excluir lotes de vagas: {response.text}'
            )
        logger.info(
            'Lotes de vagas excluídos por processo',
            extra={
                "correlation_id": get_correlation_id(),
                "processo_uuid": processo_uuid,
                "status_code": response.status_code,
                "response": response.json(),
                "method": "DELETE",
                "url": url,
                "params": params,
                "headers": headers,
            },
        )
        return response.json() if response.content else {}
