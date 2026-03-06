"""
Serviço para comunicação com o microserviço de Escolhas (MS-Escolha).
Usado na finalização do processo para validar se todos os convocados fizeram escolha.
"""
import logging
from typing import List
from urllib.parse import urlencode

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30
PATH_ESCOLHAS = '/api/v1/escolhas/'
# Qualquer situação (escolha, reconvocação, nao-escolha) = candidato respondeu. Só pendente = sem registro.
SITUACOES_COM_ESCOLHA = 'escolha,reconvocacao,nao-escolha'
PAGE_SIZE = 10000


def _get_base_url() -> str:
    """Obtém a URL base do MS-Escolha a partir das configurações."""
    base_url = getattr(settings, 'ESCOLHAS_API_URL', None) or ''
    return base_url.rstrip('/')


def buscar_candidatos_com_escolha(concurso_uuid: str) -> List[str]:
    """
    Busca no MS-Escolha os candidato_uuid que já têm registro de resposta (escolha, reconvocação ou não escolha).
    Pendente = candidato sem nenhum registro; qualquer situação conta como "respondeu".

    Args:
        concurso_uuid: UUID do concurso (o ProcessoConvocacao tem concurso_uuid).

    Returns:
        Lista de candidato_uuid (strings) que possuem registro no concurso (qualquer situação).
        Lista vazia se ESCOLHAS_API_URL não estiver configurada ou em caso de erro (logado).
    """
    base_url = _get_base_url()
    if not base_url:
        logger.warning('ESCOLHAS_API_URL não configurada; retornando lista vazia de escolhas.')
        return []

    params = {
        'concurso_uuid': concurso_uuid,
        'situacao__in': SITUACOES_COM_ESCOLHA,
        'page_size': PAGE_SIZE,
    }
    query = urlencode(params)
    url = f"{base_url}{PATH_ESCOLHAS.rstrip('/')}/?{query}"

    try:
        response = requests.get(url, timeout=DEFAULT_TIMEOUT, headers={'Accept': 'application/json'})
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
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
    return candidato_uuids
