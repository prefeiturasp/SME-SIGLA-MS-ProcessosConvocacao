"""Módulo tests/services/test_concursos_api_service."""

from unittest.mock import Mock, patch

import pytest
from django.test import override_settings
from processos.services.concursos_api_service import ConcursosApiService
from processos.services.exceptions import ConcursoServiceError


@override_settings(CONCURSOS_API_URL="http://ms-concursos")
def test_atualizar_situacao_sucesso_retorna_json():
    """Verifica atualizar situação sucesso retorna json."""
    service = ConcursosApiService()
    concurso_uuid = "11111111-1111-1111-1111-111111111111"

    resposta = Mock()
    resposta.status_code = 200
    resposta.content = b'{"situacao": "EM_ANDAMENTO"}'
    resposta.json.return_value = {"situacao": "EM_ANDAMENTO"}

    with patch(
        "processos.services.concursos_api_service.http_client.patch",
        return_value=resposta,
    ) as mock_patch:
        resultado = service.atualizar_situacao(concurso_uuid, "EM_ANDAMENTO")

    assert resultado == {"situacao": "EM_ANDAMENTO"}
    mock_patch.assert_called_once()
    url_chamada = mock_patch.call_args[0][0]
    kwargs_chamada = mock_patch.call_args.kwargs
    assert (
        url_chamada
        == f"http://ms-concursos/api/v1/concursos/{concurso_uuid}/atualizar-situacao/"  # noqa: E501
    )
    assert kwargs_chamada["json"] == {"situacao": "EM_ANDAMENTO"}
    assert kwargs_chamada["headers"] == service.headers
    assert kwargs_chamada["timeout"] == service.timeout_seconds


@override_settings(
    CONCURSOS_API_URL="http://ms-concursos",
    CONCURSOS_API_KEY="test-key",
    API_KEY_HEADER="X-API-Key",
)
def test_atualizar_situacao_envia_api_key():
    """Verifica envio do header X-API-Key quando CONCURSOS_API_KEY está configurada."""  # noqa: E501
    service = ConcursosApiService()
    resposta = Mock()
    resposta.status_code = 200
    resposta.content = b"{}"
    resposta.json.return_value = {}

    with patch(
        "processos.services.concursos_api_service.http_client.patch",
        return_value=resposta,
    ) as mock_patch:
        service.atualizar_situacao(
            "22222222-2222-2222-2222-222222222222", "COMPLETO"
        )

    assert mock_patch.call_args.kwargs["headers"] == {
        "Accept": "application/json",
        "X-API-Key": "test-key",
    }


@override_settings(CONCURSOS_API_URL="http://ms-concursos")
def test_atualizar_situacao_status_diferente_200_gera_erro():
    """Verifica que status HTTP diferente de 200 gera ConcursoServiceError."""
    service = ConcursosApiService()
    resposta = Mock()
    resposta.status_code = 500
    resposta.text = "erro"
    resposta.content = b"erro"

    with patch(  # noqa: SIM117
        "processos.services.concursos_api_service.http_client.patch",
        return_value=resposta,
    ):
        with pytest.raises(ConcursoServiceError) as exc:
            service.atualizar_situacao(
                "33333333-3333-3333-3333-333333333333", "COMPLETO"
            )

    assert "MS-Concursos retornou status 500" in str(exc.value)


@override_settings(CONCURSOS_API_URL="http://ms-concursos")
def test_atualizar_situacao_excecao_do_client_gera_erro():
    """Verifica que exceção do client HTTP gera ConcursoServiceError."""
    service = ConcursosApiService()

    with patch(  # noqa: SIM117
        "processos.services.concursos_api_service.http_client.patch",
        side_effect=Exception("boom"),
    ):
        with pytest.raises(ConcursoServiceError) as exc:
            service.atualizar_situacao(
                "44444444-4444-4444-4444-444444444444", "EM_ANDAMENTO"
            )

    assert "Falha ao conectar no MS-Concursos" in str(exc.value)
