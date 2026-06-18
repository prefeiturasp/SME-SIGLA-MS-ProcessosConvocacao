"""Módulo tests/services/test_escolhas_api_service."""

from unittest.mock import Mock, patch

import pytest
from django.test import override_settings

from processos.services.escolhas_service import EscolhasApiService
from processos.services.exceptions import EscolhasServiceError


def test_buscar_candidatos_com_escolha_sem_config_retorna_lista_vazia():
    """Sem config, buscar candidatos com escolha retorna lista vazia."""
    service = EscolhasApiService()
    with override_settings(ESCOLHAS_API_URL=""):
        assert service.buscar_candidatos_com_escolha("concurso") == []


@override_settings(ESCOLHAS_API_URL="http://ms-escolha")
def test_buscar_candidatos_com_escolha_json_lista_mapeia_candidato_uuid():
    """JSON lista mapeia candidato_uuid em buscar com escolha."""
    service = EscolhasApiService()
    concurso_uuid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

    resposta = Mock()
    resposta.raise_for_status.return_value = None
    resposta.json.return_value = [
        {"candidato_uuid": "1"},
        {"candidato_uuid": "2"},
        {"candidato_uuid": None},
        {},
    ]

    with patch(
        "processos.services.escolhas_service.http_client.get",
        return_value=resposta,
    ) as mock_get:
        resultado = service.buscar_candidatos_com_escolha(concurso_uuid)

    assert resultado == ["1", "2"]
    mock_get.assert_called_once()
    url_chamada = mock_get.call_args[0][0]
    kwargs_chamada = mock_get.call_args.kwargs
    assert url_chamada.startswith("http://ms-escolha/api/v1/escolhas/?")
    assert "concurso_uuid=" in url_chamada
    assert "situacao__in=" in url_chamada
    assert "page_size=" in url_chamada
    assert kwargs_chamada["timeout"] == service.TIMEOUT_SEGUNDOS
    assert kwargs_chamada["headers"] == {"Accept": "application/json"}


@override_settings(ESCOLHAS_API_URL="http://ms-escolha")
def test_buscar_candidatos_com_escolha_json_dict_results_mapeia_candidato_uuid():  # noqa: E501
    """Verifica mapeamento de candidato_uuid em results."""
    service = EscolhasApiService()

    resposta = Mock()
    resposta.raise_for_status.return_value = None
    resposta.json.return_value = {"results": [{"candidato_uuid": "x"}]}

    with patch(
        "processos.services.escolhas_service.http_client.get",
        return_value=resposta,
    ):
        assert service.buscar_candidatos_com_escolha("concurso") == ["x"]


@override_settings(ESCOLHAS_API_URL="http://ms-escolha")
def test_buscar_candidatos_com_escolha_json_dict_sem_results_retorna_lista_vazia():  # noqa: E501
    """Verifica lista vazia sem results na resposta."""
    service = EscolhasApiService()

    resposta = Mock()
    resposta.raise_for_status.return_value = None
    resposta.json.return_value = {"count": 0}

    with patch(
        "processos.services.escolhas_service.http_client.get",
        return_value=resposta,
    ):
        assert service.buscar_candidatos_com_escolha("concurso") == []


@override_settings(ESCOLHAS_API_URL="http://ms-escolha")
def test_buscar_candidatos_com_escolha_erro_do_client_e_propagado():
    """Verifica buscar candidatos com escolha erro do client e propagado."""
    service = EscolhasApiService()

    resposta = Mock()
    resposta.raise_for_status.side_effect = Exception("boom")

    with patch(  # noqa: SIM117
        "processos.services.escolhas_service.http_client.get",
        return_value=resposta,
    ):
        with pytest.raises(Exception):  # noqa: B017
            service.buscar_candidatos_com_escolha("concurso")


def test_excluir_lotes_vagas_por_processo_sem_config_gera_value_error():
    """Sem config, excluir lotes vagas por processo levanta ValueError."""
    service = EscolhasApiService()
    with override_settings(ESCOLHAS_API_URL=""), pytest.raises(ValueError):
        service.excluir_lotes_vagas_por_processo("processo")


@override_settings(ESCOLHAS_API_URL="http://ms-escolha")
def test_excluir_lotes_vagas_por_processo_sucesso_retorna_json():
    """Verifica excluir lotes vagas por processo sucesso retorna json."""
    service = EscolhasApiService()
    processo_uuid = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    resposta = Mock()
    resposta.status_code = 200
    resposta.text = '{"ok": true}'
    resposta.content = b'{"ok": true}'
    resposta.json.return_value = {"ok": True}

    with patch(
        "processos.services.escolhas_service.http_client.delete",
        return_value=resposta,
    ) as mock_delete:
        resultado = service.excluir_lotes_vagas_por_processo(processo_uuid)

    assert resultado == {"ok": True}
    mock_delete.assert_called_once()
    url_chamada = mock_delete.call_args[0][0]
    kwargs_chamada = mock_delete.call_args.kwargs
    assert url_chamada == "http://ms-escolha/api/v1/vagas-escolas/por-processo/"
    assert kwargs_chamada["params"] == {"processo_uuid": processo_uuid}
    assert kwargs_chamada["headers"] == {"Accept": "application/json"}
    assert kwargs_chamada["timeout"] == service.TIMEOUT_SEGUNDOS


@override_settings(ESCOLHAS_API_URL="http://ms-escolha")
def test_excluir_lotes_vagas_por_processo_sucesso_sem_body_retorna_dict_vazio():  # noqa: E501
    """Verifica exclusão de lotes sem corpo na resposta."""
    service = EscolhasApiService()

    resposta = Mock()
    resposta.status_code = 200
    resposta.text = ""
    resposta.content = b""
    resposta.json.return_value = {"ignored": True}

    with patch(
        "processos.services.escolhas_service.http_client.delete",
        return_value=resposta,
    ):
        assert service.excluir_lotes_vagas_por_processo("processo") == {}


@override_settings(ESCOLHAS_API_URL="http://ms-escolha")
def test_excluir_lotes_vagas_por_processo_status_diferente_200_gera_erro():
    """Verifica erro quando status da exclusão não é 200."""
    service = EscolhasApiService()

    resposta = Mock()
    resposta.status_code = 500
    resposta.text = "erro"
    resposta.content = b"erro"

    with patch(  # noqa: SIM117
        "processos.services.escolhas_service.http_client.delete",
        return_value=resposta,
    ):
        with pytest.raises(EscolhasServiceError) as exc:
            service.excluir_lotes_vagas_por_processo("processo")

    assert "MS-Escolha retornou status 500" in str(exc.value)


@override_settings(ESCOLHAS_API_URL="http://ms-escolha")
def test_excluir_lotes_vagas_por_processo_excecao_do_client_gera_erro():
    """Exceção do client ao excluir lotes vagas propaga erro."""
    service = EscolhasApiService()

    with patch(  # noqa: SIM117
        "processos.services.escolhas_service.http_client.delete",
        side_effect=Exception("boom"),
    ):
        with pytest.raises(EscolhasServiceError) as exc:
            service.excluir_lotes_vagas_por_processo("processo")

    assert "Falha ao conectar no MS-Escolha" in str(exc.value)
