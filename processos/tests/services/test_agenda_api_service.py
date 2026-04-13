import pytest
from unittest.mock import Mock, patch

from django.test import override_settings

from processos.services.agenda_api_service import AgendaApiService
from processos.services.exceptions import AgendaServiceError


@override_settings(AGENDA_API_URL="http://ms-agenda")
def test_excluir_agendas_por_processo_sucesso_retorna_json():
    service = AgendaApiService()
    processo_uuid = "11111111-1111-1111-1111-111111111111"

    response = Mock()
    response.status_code = 200
    response.text = '{"ok": true}'
    response.content = b'{"ok": true}'
    response.json.return_value = {"ok": True}

    with patch("processos.services.agenda_api_service.http_client.delete", return_value=response) as mock_delete:
        result = service.excluir_agendas_por_processo(processo_uuid)

    assert result == {"ok": True}
    mock_delete.assert_called_once()
    called_url = mock_delete.call_args[0][0]
    called_kwargs = mock_delete.call_args.kwargs
    assert called_url == "http://ms-agenda/api/v1/agendas/por-processo/"
    assert called_kwargs["params"] == {"processo_uuid": processo_uuid}
    assert called_kwargs["headers"] == {"Accept": "application/json"}
    assert called_kwargs["timeout"] == service.TIMEOUT_SEGUNDOS


@override_settings(AGENDA_API_URL="http://ms-agenda")
def test_excluir_agendas_por_processo_sucesso_sem_body_retorna_dict_vazio():
    service = AgendaApiService()
    processo_uuid = "22222222-2222-2222-2222-222222222222"

    response = Mock()
    response.status_code = 200
    response.text = ""
    response.content = b""
    response.json.return_value = {"ignored": True}

    with patch("processos.services.agenda_api_service.http_client.delete", return_value=response):
        result = service.excluir_agendas_por_processo(processo_uuid)

    assert result == {}


@override_settings(AGENDA_API_URL="http://ms-agenda")
def test_excluir_agendas_por_processo_status_diferente_200_gera_erro():
    service = AgendaApiService()
    processo_uuid = "33333333-3333-3333-3333-333333333333"

    response = Mock()
    response.status_code = 500
    response.text = "erro"
    response.content = b"erro"
    response.json.return_value = {"detail": "erro"}

    with patch("processos.services.agenda_api_service.http_client.delete", return_value=response):
        with pytest.raises(AgendaServiceError) as exc:
            service.excluir_agendas_por_processo(processo_uuid)

    assert "MS-Agenda retornou status 500" in str(exc.value)


@override_settings(AGENDA_API_URL="http://ms-agenda")
def test_excluir_agendas_por_processo_excecao_do_client_gera_erro():
    service = AgendaApiService()
    processo_uuid = "44444444-4444-4444-4444-444444444444"

    with patch("processos.services.agenda_api_service.http_client.delete", side_effect=Exception("boom")):
        with pytest.raises(AgendaServiceError) as exc:
            service.excluir_agendas_por_processo(processo_uuid)

    assert "Falha ao conectar no MS-Agenda" in str(exc.value)

