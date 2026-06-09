"""Módulo tests/services/test_escolhas_api_service."""
from unittest.mock import Mock, patch

import pytest
from django.test import override_settings

from processos.services.escolhas_service import EscolhasApiService
from processos.services.exceptions import EscolhasServiceError


def test_buscar_candidatos_com_escolha_sem_config_retorna_lista_vazia():
    """Verifica buscar candidatos com escolha sem config retorna lista vazia.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    service = EscolhasApiService()
    with override_settings(ESCOLHAS_API_URL=""):
        assert service.buscar_candidatos_com_escolha("concurso") == []


@override_settings(ESCOLHAS_API_URL="http://ms-escolha")
def test_buscar_candidatos_com_escolha_json_lista_mapeia_candidato_uuid():
    """Verifica buscar candidatos com escolha json lista mapeia candidato uuid.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    service = EscolhasApiService()
    concurso_uuid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = [
        {"candidato_uuid": "1"},
        {"candidato_uuid": "2"},
        {"candidato_uuid": None},
        {},
    ]

    with patch(
        "processos.services.escolhas_service.http_client.get",
        return_value=response,
    ) as mock_get:
        result = service.buscar_candidatos_com_escolha(concurso_uuid)

    assert result == ["1", "2"]
    mock_get.assert_called_once()
    called_url = mock_get.call_args[0][0]
    called_kwargs = mock_get.call_args.kwargs
    assert called_url.startswith("http://ms-escolha/api/v1/escolhas/?")
    assert "concurso_uuid=" in called_url
    assert "situacao__in=" in called_url
    assert "page_size=" in called_url
    assert called_kwargs["timeout"] == service.DEFAULT_TIMEOUT
    assert called_kwargs["headers"] == {"Accept": "application/json"}


@override_settings(ESCOLHAS_API_URL="http://ms-escolha")
def test_buscar_candidatos_com_escolha_json_dict_results_mapeia_candidato_uuid():  # noqa: E501
    """Verifica buscar candidatos com escolha json dict results mapeia candidato uuid.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    service = EscolhasApiService()

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"results": [{"candidato_uuid": "x"}]}

    with patch(
        "processos.services.escolhas_service.http_client.get",
        return_value=response,
    ):
        assert service.buscar_candidatos_com_escolha("concurso") == ["x"]


@override_settings(ESCOLHAS_API_URL="http://ms-escolha")
def test_buscar_candidatos_com_escolha_json_dict_sem_results_retorna_lista_vazia():  # noqa: E501
    """Verifica buscar candidatos com escolha json dict sem results retorna lista vazia.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    service = EscolhasApiService()

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"count": 0}

    with patch(
        "processos.services.escolhas_service.http_client.get",
        return_value=response,
    ):
        assert service.buscar_candidatos_com_escolha("concurso") == []


@override_settings(ESCOLHAS_API_URL="http://ms-escolha")
def test_buscar_candidatos_com_escolha_erro_do_client_e_propagado():
    """Verifica buscar candidatos com escolha erro do client e propagado.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    service = EscolhasApiService()

    response = Mock()
    response.raise_for_status.side_effect = Exception("boom")

    with patch(  # noqa: SIM117
        "processos.services.escolhas_service.http_client.get",
        return_value=response,
    ):
        with pytest.raises(Exception):  # noqa: B017
            service.buscar_candidatos_com_escolha("concurso")


def test_excluir_lotes_vagas_por_processo_sem_config_gera_value_error():
    """Verifica excluir lotes vagas por processo sem config gera value error.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    service = EscolhasApiService()
    with override_settings(ESCOLHAS_API_URL=""), pytest.raises(ValueError):
        service.excluir_lotes_vagas_por_processo("processo")


@override_settings(ESCOLHAS_API_URL="http://ms-escolha")
def test_excluir_lotes_vagas_por_processo_sucesso_retorna_json():
    """Verifica excluir lotes vagas por processo sucesso retorna json.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    service = EscolhasApiService()
    processo_uuid = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    response = Mock()
    response.status_code = 200
    response.text = '{"ok": true}'
    response.content = b'{"ok": true}'
    response.json.return_value = {"ok": True}

    with patch(
        "processos.services.escolhas_service.http_client.delete",
        return_value=response,
    ) as mock_delete:
        result = service.excluir_lotes_vagas_por_processo(processo_uuid)

    assert result == {"ok": True}
    mock_delete.assert_called_once()
    called_url = mock_delete.call_args[0][0]
    called_kwargs = mock_delete.call_args.kwargs
    assert called_url == "http://ms-escolha/api/v1/vagas-escolas/por-processo/"
    assert called_kwargs["params"] == {"processo_uuid": processo_uuid}
    assert called_kwargs["headers"] == {"Accept": "application/json"}
    assert called_kwargs["timeout"] == service.TIMEOUT_SEGUNDOS


@override_settings(ESCOLHAS_API_URL="http://ms-escolha")
def test_excluir_lotes_vagas_por_processo_sucesso_sem_body_retorna_dict_vazio():  # noqa: E501
    """Verifica excluir lotes vagas por processo sucesso sem body retorna dict vazio.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    service = EscolhasApiService()

    response = Mock()
    response.status_code = 200
    response.text = ""
    response.content = b""
    response.json.return_value = {"ignored": True}

    with patch(
        "processos.services.escolhas_service.http_client.delete",
        return_value=response,
    ):
        assert service.excluir_lotes_vagas_por_processo("processo") == {}


@override_settings(ESCOLHAS_API_URL="http://ms-escolha")
def test_excluir_lotes_vagas_por_processo_status_diferente_200_gera_erro():
    """Verifica excluir lotes vagas por processo status diferente 200 gera erro.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    service = EscolhasApiService()

    response = Mock()
    response.status_code = 500
    response.text = "erro"
    response.content = b"erro"

    with patch(  # noqa: SIM117
        "processos.services.escolhas_service.http_client.delete",
        return_value=response,
    ):
        with pytest.raises(EscolhasServiceError) as exc:
            service.excluir_lotes_vagas_por_processo("processo")

    assert "MS-Escolha retornou status 500" in str(exc.value)


@override_settings(ESCOLHAS_API_URL="http://ms-escolha")
def test_excluir_lotes_vagas_por_processo_excecao_do_client_gera_erro():
    """Verifica excluir lotes vagas por processo excecao do client gera erro.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    service = EscolhasApiService()

    with patch(  # noqa: SIM117
        "processos.services.escolhas_service.http_client.delete",
        side_effect=Exception("boom"),
    ):
        with pytest.raises(EscolhasServiceError) as exc:
            service.excluir_lotes_vagas_por_processo("processo")

    assert "Falha ao conectar no MS-Escolha" in str(exc.value)
