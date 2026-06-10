"""Módulo tests/services/test_candidatos_api_service."""

from unittest.mock import Mock, patch

import pytest
from django.test import override_settings

from processos.services.candidatos_api_url import CandidatosApiService
from processos.services.exceptions import CandidatosServiceError


def test_buscar_habilitados_por_processo_sem_config_retorna_lista_vazia():
    """Sem config, buscar habilitados por processo retorna lista vazia."""
    service = CandidatosApiService()
    with override_settings(CANDIDATOS_API_URL=""):
        assert service.buscar_habilitados_por_processo("uuid") == []


@override_settings(CANDIDATOS_API_URL="http://ms-candidatos")
def test_buscar_habilitados_por_processo_retorna_lista_quando_json_lista():
    """Verifica habilitados quando a API retorna lista JSON."""
    service = CandidatosApiService()
    processo_uuid = "11111111-1111-1111-1111-111111111111"

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = [{"a": 1}]

    with patch(
        "processos.services.candidatos_api_url.http_client.get",
        return_value=response,
    ) as mock_get:
        result = service.buscar_habilitados_por_processo(processo_uuid)

    assert result == [{"a": 1}]
    mock_get.assert_called_once()
    called_url = mock_get.call_args[0][0]
    called_kwargs = mock_get.call_args.kwargs
    assert called_url.startswith("http://ms-candidatos/api/v1/habilitados/?")
    assert "processo_uuid=" in called_url
    assert "foi_convocado=true" in called_url
    assert called_kwargs["headers"] == {"Accept": "application/json"}
    assert called_kwargs["timeout"] == service.TIMEOUT_SEGUNDOS


@override_settings(CANDIDATOS_API_URL="http://ms-candidatos")
def test_buscar_habilitados_por_processo_retorna_results_quando_json_dict_com_results():  # noqa: E501
    """Verifica habilitados quando a API retorna results."""
    service = CandidatosApiService()

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"results": [{"x": 1}, {"x": 2}]}

    with patch(
        "processos.services.candidatos_api_url.http_client.get",
        return_value=response,
    ):
        assert service.buscar_habilitados_por_processo("uuid") == [
            {"x": 1},
            {"x": 2},
        ]


@override_settings(CANDIDATOS_API_URL="http://ms-candidatos")
def test_buscar_habilitados_por_processo_retorna_vazio_quando_json_dict_sem_results():  # noqa: E501
    """Verifica habilitados vazios sem results no JSON."""
    service = CandidatosApiService()

    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"count": 0}

    with patch(
        "processos.services.candidatos_api_url.http_client.get",
        return_value=response,
    ):
        assert service.buscar_habilitados_por_processo("uuid") == []


@override_settings(CANDIDATOS_API_URL="http://ms-candidatos")
def test_buscar_habilitados_por_processo_propagada_erro_do_client():
    """Verifica buscar habilitados por processo propagada erro do client."""
    service = CandidatosApiService()

    response = Mock()
    response.raise_for_status.side_effect = Exception("boom")

    with patch(  # noqa: SIM117
        "processos.services.candidatos_api_url.http_client.get",
        return_value=response,
    ):
        with pytest.raises(Exception):  # noqa: B017
            service.buscar_habilitados_por_processo("uuid")


def test_desconvocar_por_processo_sem_config_gera_value_error():
    """Verifica desconvocar por processo sem config gera value error."""
    service = CandidatosApiService()
    with override_settings(CANDIDATOS_API_URL=""):  # noqa: SIM117
        with pytest.raises(ValueError):
            service.desconvocar_por_processo("uuid")


@override_settings(CANDIDATOS_API_URL="http://ms-candidatos")
def test_desconvocar_por_processo_sucesso_retorna_json():
    """Verifica desconvocar por processo sucesso retorna json."""
    service = CandidatosApiService()
    processo_uuid = "22222222-2222-2222-2222-222222222222"

    response = Mock()
    response.status_code = 200
    response.text = '{"ok": true}'
    response.content = b'{"ok": true}'
    response.json.return_value = {"ok": True}

    with patch(
        "processos.services.candidatos_api_url.http_client.patch",
        return_value=response,
    ) as mock_patch:
        result = service.desconvocar_por_processo(processo_uuid)

    assert result == {"ok": True}
    mock_patch.assert_called_once()
    called_url = mock_patch.call_args[0][0]
    called_kwargs = mock_patch.call_args.kwargs
    assert called_url == "http://ms-candidatos/api/v1/habilitados/desconvocar/"
    assert called_kwargs["json"] == {"processo_uuid": processo_uuid}
    assert called_kwargs["headers"] == {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    assert called_kwargs["timeout"] == service.TIMEOUT_SEGUNDOS


@override_settings(CANDIDATOS_API_URL="http://ms-candidatos")
def test_desconvocar_por_processo_sucesso_sem_body_retorna_dict_vazio():
    """Desconvocar por processo sem body retorna dict vazio."""
    service = CandidatosApiService()

    response = Mock()
    response.status_code = 200
    response.text = ""
    response.content = b""
    response.json.return_value = {"ignored": True}

    with patch(
        "processos.services.candidatos_api_url.http_client.patch",
        return_value=response,
    ):
        assert service.desconvocar_por_processo("uuid") == {}


@override_settings(CANDIDATOS_API_URL="http://ms-candidatos")
def test_desconvocar_por_processo_status_diferente_200_gera_erro():
    """Verifica desconvocar por processo status diferente 200 gera erro."""
    service = CandidatosApiService()

    response = Mock()
    response.status_code = 400
    response.text = "erro"
    response.content = b"erro"

    with patch(  # noqa: SIM117
        "processos.services.candidatos_api_url.http_client.patch",
        return_value=response,
    ):
        with pytest.raises(CandidatosServiceError) as exc:
            service.desconvocar_por_processo("uuid")

    assert "MS-Candidatos retornou status 400" in str(exc.value)


@override_settings(CANDIDATOS_API_URL="http://ms-candidatos")
def test_desconvocar_por_processo_excecao_do_client_gera_erro():
    """Verifica desconvocar por processo excecao do client gera erro."""
    service = CandidatosApiService()

    with patch(  # noqa: SIM117
        "processos.services.candidatos_api_url.http_client.patch",
        side_effect=Exception("boom"),
    ):
        with pytest.raises(CandidatosServiceError) as exc:
            service.desconvocar_por_processo("uuid")

    assert "Falha ao conectar no MS-Candidatos" in str(exc.value)
