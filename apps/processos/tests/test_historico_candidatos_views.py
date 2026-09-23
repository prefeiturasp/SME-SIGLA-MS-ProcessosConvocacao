"""Testes da action historico-candidatos."""

from __future__ import annotations

import uuid
from unittest.mock import Mock, patch

from django.urls import reverse
from processos.api.views import ProcessoConvocacaoViewSet
from processos.services.exceptions import CandidatosServiceError
from rest_framework import status
from rest_framework.test import APIRequestFactory, force_authenticate


def _post_historico(payload: dict):
    factory = APIRequestFactory()
    request = factory.post(
        reverse("processoconvocacao-historico-candidatos"),
        payload,
        format="json",
    )
    force_authenticate(request, user=Mock(is_authenticated=True))
    view = ProcessoConvocacaoViewSet.as_view({"post": "historico_candidatos"})
    return view(request)


def test_historico_candidatos_sem_lista_retorna_400():
    """Body sem processos_uuids retorna 400."""
    resposta = _post_historico({})
    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "processos_uuids" in resposta.data["detail"]

    resposta = _post_historico({"processos_uuids": "nao-lista"})
    assert resposta.status_code == status.HTTP_400_BAD_REQUEST


def test_historico_candidatos_lista_vazia_retorna_400():
    """Lista vazia de processos_uuids retorna 400."""
    resposta = _post_historico({"processos_uuids": []})
    assert resposta.status_code == status.HTTP_400_BAD_REQUEST


@patch(
    "processos.api.views.HistoricoCandidatosService.historico_candidatos_por_processos"
)
def test_historico_candidatos_sucesso(mock_historico):
    """Retorna o resultado montado pelo service."""
    pid = str(uuid.uuid4())
    esperado = [
        {
            "descricao": "Processo",
            "data_convocacao": "2026-01-15T12:00:00+00:00",
            "candidatos": {"total": 1, "geral": 1, "nna": 0, "pcd": 0},
            "escolha": {"total": 1, "geral": 1, "nna": 0, "pcd": 0},
            "nao-escolha": {"total": 0, "geral": 0, "nna": 0, "pcd": 0},
            "reconvocacao": {"total": 0, "geral": 0, "nna": 0, "pcd": 0},
        }
    ]
    mock_historico.return_value = esperado

    resposta = _post_historico({"processos_uuids": [pid]})

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data == esperado
    mock_historico.assert_called_once_with([pid])


@patch(
    "processos.api.views.HistoricoCandidatosService.historico_candidatos_por_processos"
)
def test_historico_candidatos_erro_service_retorna_400(mock_historico):
    """Erros de integração retornam 400 com a mensagem do service."""
    mock_historico.side_effect = CandidatosServiceError("falha ms-candidatos")

    resposta = _post_historico({"processos_uuids": [str(uuid.uuid4())]})

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data["detail"] == "falha ms-candidatos"


@patch(
    "processos.api.views.HistoricoCandidatosService.historico_candidatos_por_processos"
)
def test_historico_candidatos_erro_inesperado_retorna_400(mock_historico):
    """Exceção genérica retorna 400 com mensagem padrão."""
    mock_historico.side_effect = RuntimeError("boom")

    resposta = _post_historico({"processos_uuids": [str(uuid.uuid4())]})

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data["detail"] == "Erro ao montar histórico de candidatos."
