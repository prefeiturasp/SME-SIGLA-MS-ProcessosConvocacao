"""Testes da API de envio de e-mail (listagem, detalhe e criação)."""

import uuid
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from envio_email.models import EnvioEmail, EnvioEmailCandidato
from envio_email.models.envio_email import TIPO_CONVOCACAO

pytestmark = pytest.mark.django_db


@pytest.fixture
def envio_email(processo_convocacao):
    """Fixture para EnvioEmail."""
    return EnvioEmail.objects.create(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        tipo=TIPO_CONVOCACAO,
        quantidade_candidatos=2,
    )


@pytest.fixture
def envio_email_candidatos(envio_email):
    """Fixture para EnvioEmailCandidato vinculados ao envio."""
    from envio_email.models.envio_email_candidato import (
        ENVIO_STATUS_ERRO,
        ENVIO_STATUS_SUCESSO,
    )

    EnvioEmailCandidato.objects.create(
        envio_email=envio_email,
        nome="Fulano",
        rf="1234567",
        email="fulano@test.com",
        status=ENVIO_STATUS_SUCESSO,
        conteudo="<p>Conteúdo 1</p>",
    )
    EnvioEmailCandidato.objects.create(
        envio_email=envio_email,
        nome="Ciclano",
        rf="7654321",
        email="ciclano@test.com",
        status=ENVIO_STATUS_ERRO,
        conteudo="<p>Conteúdo 2</p>",
    )
    return list(envio_email.candidatos.all())


def test_envio_email_list(authenticated_client, envio_email):
    """Testa GET /api/v1/envio-email/ (listagem do histórico)."""
    url = reverse("envio-email-list")
    resposta = authenticated_client.get(url)
    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data) >= 1
    assert resposta.data[0]["uuid"] == str(envio_email.uuid)
    assert resposta.data[0]["processo_nome"] == envio_email.processo_nome
    assert (
        resposta.data[0]["quantidade_candidatos"]
        == envio_email.quantidade_candidatos
    )
    assert resposta.data[0]["tipo"] == TIPO_CONVOCACAO


def test_envio_email_retrieve(
    authenticated_client, envio_email, envio_email_candidatos
):
    """Testa GET /api/v1/envio-email/<uuid>/ (detalhe com candidatos)."""
    url = reverse("envio-email-detail", args=[envio_email.uuid])
    resposta = authenticated_client.get(url)
    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["uuid"] == str(envio_email.uuid)
    assert resposta.data["processo_nome"] == envio_email.processo_nome
    assert "candidatos" in resposta.data
    assert len(resposta.data["candidatos"]) == 2
    nomes = [c["nome"] for c in resposta.data["candidatos"]]
    assert "Fulano" in nomes
    assert "Ciclano" in nomes


def test_envio_email_detalhe_nao_encontrado(authenticated_client):
    """Testa GET detalhe com UUID inexistente."""
    url = reverse("envio-email-detail", args=[uuid.uuid4()])
    resposta = authenticated_client.get(url)
    assert resposta.status_code == status.HTTP_404_NOT_FOUND


@patch("envio_email.api.views.views_envio.iniciar_processamento_envio")
def test_envio_email_create(
    mock_iniciar, authenticated_client, processo_convocacao
):
    """Testa POST /api/v1/envio-email/ (inicia processamento de envio)."""
    mock_envio = {
        "processo_uuid": str(processo_convocacao.uuid),
        "processo_nome": processo_convocacao.concurso_nome,
        "tipo": TIPO_CONVOCACAO,
        "quantidade_candidatos": 0,
        "uuid": str(uuid.uuid4()),
    }
    mock_iniciar.return_value = mock_envio
    url = reverse("envio-email-list")
    dados_requisicao = {
        "processo_uuid": str(processo_convocacao.uuid),
        "processo_nome": processo_convocacao.concurso_nome,
        "tipo": TIPO_CONVOCACAO,
        "conteudo": "<p>Conteúdo</p>",
    }
    resposta = authenticated_client.post(url, dados_requisicao, format="json")
    assert resposta.status_code == status.HTTP_200_OK
    assert "detail" in resposta.data
    assert "envio_email_uuid" in resposta.data
    assert resposta.data["envio_email_uuid"] == str(mock_envio["uuid"])
    mock_iniciar.assert_called_once()
    kwargs_chamada = mock_iniciar.call_args[1]
    assert kwargs_chamada["processo_nome"] == processo_convocacao.concurso_nome
    assert kwargs_chamada["tipo"] == TIPO_CONVOCACAO


@patch("envio_email.api.views.views_envio.iniciar_processamento_envio")
def test_envio_email_criacao_corpo_invalido(
    mock_iniciar, authenticated_client
):
    """Testa POST com corpo inválido (processo não encontrado)."""
    url = reverse("envio-email-list")
    dados_requisicao = {
        "processo_uuid": str(uuid.uuid4()),
        "processo_nome": "Inexistente",
        "tipo": TIPO_CONVOCACAO,
        "conteudo": "<p>Conteúdo</p>",
    }
    resposta = authenticated_client.post(url, dados_requisicao, format="json")
    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    mock_iniciar.assert_not_called()


@patch("envio_email.api.views.views_envio.iniciar_processamento_envio")
def test_envio_email_create_quando_servico_levanta_excecao_retorna_500(
    mock_iniciar, authenticated_client, processo_convocacao
):
    """Exceção em iniciar_processamento_envio retorna 500 na view."""
    mock_iniciar.side_effect = Exception(
        "Email duplicado entre candidatos: duplicado@test.com"
    )

    url = reverse("envio-email-list")
    dados_requisicao = {
        "processo_uuid": str(processo_convocacao.uuid),
        "processo_nome": processo_convocacao.concurso_nome,
        "tipo": TIPO_CONVOCACAO,
        "conteudo": "<p>Conteúdo</p>",
    }
    resposta = authenticated_client.post(url, dados_requisicao, format="json")

    assert resposta.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "detail" in resposta.data
    assert "duplicado@test.com" in resposta.data["detail"]
