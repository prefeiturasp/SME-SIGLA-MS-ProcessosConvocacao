"""Módulo tests/services/test_agenda_api_service."""

from unittest.mock import Mock, patch

import pytest
from django.test import override_settings
from processos.services.agenda_api_service import AgendaApiService
from processos.services.exceptions import AgendaServiceError


@override_settings(AGENDA_API_URL="http://ms-agenda")
def test_excluir_agendas_por_processo_sucesso_retorna_json():
    """Verifica excluir agendas por processo sucesso retorna json."""
    service = AgendaApiService()
    processo_uuid = "11111111-1111-1111-1111-111111111111"

    resposta = Mock()
    resposta.status_code = 200
    resposta.text = '{"ok": true}'
    resposta.content = b'{"ok": true}'
    resposta.json.return_value = {"ok": True}

    with patch(
        "processos.services.agenda_api_service.http_client.delete",
        return_value=resposta,
    ) as mock_delete:
        resultado = service.excluir_agendas_por_processo(processo_uuid)

    assert resultado == {"ok": True}
    mock_delete.assert_called_once()
    url_chamada = mock_delete.call_args[0][0]
    kwargs_chamada = mock_delete.call_args.kwargs
    assert url_chamada == "http://ms-agenda/api/v1/agendas/por-processo/"
    assert kwargs_chamada["params"] == {"processo_uuid": processo_uuid}
    assert kwargs_chamada["headers"] == {"Accept": "application/json"}
    assert kwargs_chamada["timeout"] == service.TIMEOUT_SEGUNDOS


@override_settings(AGENDA_API_URL="http://ms-agenda")
def test_excluir_agendas_por_processo_sucesso_sem_body_retorna_dict_vazio():
    """Verifica exclusão de agendas sem corpo na resposta."""
    service = AgendaApiService()
    processo_uuid = "22222222-2222-2222-2222-222222222222"

    resposta = Mock()
    resposta.status_code = 200
    resposta.text = ""
    resposta.content = b""
    resposta.json.return_value = {"ignored": True}

    with patch(
        "processos.services.agenda_api_service.http_client.delete",
        return_value=resposta,
    ):
        resultado = service.excluir_agendas_por_processo(processo_uuid)

    assert resultado == {}


@override_settings(AGENDA_API_URL="http://ms-agenda")
def test_excluir_agendas_por_processo_status_diferente_200_gera_erro():
    """Verifica excluir agendas por processo status diferente 200 gera erro."""
    service = AgendaApiService()
    processo_uuid = "33333333-3333-3333-3333-333333333333"

    resposta = Mock()
    resposta.status_code = 500
    resposta.text = "erro"
    resposta.content = b"erro"
    resposta.json.return_value = {"detail": "erro"}

    with patch(  # noqa: SIM117
        "processos.services.agenda_api_service.http_client.delete",
        return_value=resposta,
    ):
        with pytest.raises(AgendaServiceError) as exc:
            service.excluir_agendas_por_processo(processo_uuid)

    assert "MS-Agenda retornou status 500" in str(exc.value)


@override_settings(AGENDA_API_URL="http://ms-agenda")
def test_excluir_agendas_por_processo_excecao_do_client_gera_erro():
    """Verifica excluir agendas por processo excecao do client gera erro."""
    service = AgendaApiService()
    processo_uuid = "44444444-4444-4444-4444-444444444444"

    with patch(  # noqa: SIM117
        "processos.services.agenda_api_service.http_client.delete",
        side_effect=Exception("boom"),
    ):
        with pytest.raises(AgendaServiceError) as exc:
            service.excluir_agendas_por_processo(processo_uuid)

    assert "Falha ao conectar no MS-Agenda" in str(exc.value)
