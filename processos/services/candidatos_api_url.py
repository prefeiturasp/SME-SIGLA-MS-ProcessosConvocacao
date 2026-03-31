"""
Configuração e requisições à API do MS-Candidatos (habilitados por processo).
"""
import logging
from typing import Any
from urllib.parse import urlencode

import requests
from django.conf import settings

from processos.middlewares import get_correlation_id


logger = logging.getLogger(__name__)

# URL base do MS-Candidatos (ex.: http://localhost:8002)
CANDIDATOS_API_URL = getattr(settings, 'CANDIDATOS_API_URL', '').rstrip('/')

PATH_HABILITADOS = '/api/v1/habilitados/'

FIELDS_HABILITADOS = (
    'candidato__nome,candidato__registro_funcional,candidato__email,candidato__uuid,'
    'descricao_cargo,codigo_cargo,classificacao,classificacao_pcd,classificacao_nna,categoria_efetiva'
)
TIMEOUT_SEGUNDOS = 30


def _url_habilitados_por_processo(processo_uuid: str) -> str:
    """Monta a URL para buscar habilitados do processo no MS-Candidatos."""
    params = {
        'processo_uuid': processo_uuid,
        'foi_convocado': 'true',
        'fields': FIELDS_HABILITADOS,
    }
    base = CANDIDATOS_API_URL or ''
    path = PATH_HABILITADOS.rstrip('/')
    query = urlencode(params)
    return f"{base}{path}/?{query}"


def buscar_habilitados_por_processo(processo_uuid: str) -> list[dict[str, Any]]:
    """
    Busca no MS-Candidatos os habilitados do processo (foi_convocado=true).

    URL: GET /api/v1/habilitados/?processo_uuid=<uuid>&foi_convocado=true
         &fields=candidato__nome,candidato__registro_funcional,candidato__email,
                 cargo_nome,classificacao

    Returns:
        Lista de registros retornados pela API (ex.: results ou lista direta).
    """
    if not CANDIDATOS_API_URL:
        logger.warning('CANDIDATOS_API_URL não configurado; retornando lista vazia.')
        return []

    url = _url_habilitados_por_processo(processo_uuid)
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
        response = requests.get(
            url,
            headers=headers,
            timeout=TIMEOUT_SEGUNDOS,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
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
        }
    )
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    if isinstance(data, dict):
        return []
    return []