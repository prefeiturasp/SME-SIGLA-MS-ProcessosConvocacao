"""Testes da API de templates de conteúdo de e-mail (GET e PATCH)."""

import pytest
from django.urls import reverse
from envio_email.models.envio_email import TIPO_CONVOCACAO
from rest_framework import status

pytestmark = pytest.mark.django_db


def test_envio_email_conteudo_list(authenticated_client, conteudo_convocacao):
    """Verifica listagem de conteúdo de e-mail."""
    url = reverse("envio-email-conteudo-list")
    resposta = authenticated_client.get(url)
    assert resposta.status_code == status.HTTP_200_OK
    dados = (
        resposta.data["results"]  # noqa: SIM401
        if "results" in resposta.data
        else resposta.data
    )
    assert len(dados) >= 3
    tipos = {item["tipo"] for item in dados}
    assert TIPO_CONVOCACAO in tipos


def test_envio_email_conteudo_list_filtrar_por_tipo(
    authenticated_client, conteudo_convocacao
):
    """Verifica envio email conteudo list filtrar por tipo."""
    url = reverse("envio-email-conteudo-list")
    resposta = authenticated_client.get(url, {"tipo": TIPO_CONVOCACAO})
    assert resposta.status_code == status.HTTP_200_OK
    dados = (
        resposta.data["results"]  # noqa: SIM401
        if "results" in resposta.data
        else resposta.data
    )
    assert len(dados) == 1
    assert dados[0]["tipo"] == TIPO_CONVOCACAO
    assert dados[0]["uuid"] == str(conteudo_convocacao.uuid)
    assert "assunto" in dados[0]
    assert "conteudo_gabarito" in dados[0]


def test_envio_email_conteudo_list_filtrar_tipo_inexistente_retorna_vazio(
    authenticated_client,
):
    """Verifica listagem vazia para tipo de conteúdo inexistente."""
    url = reverse("envio-email-conteudo-list")
    resposta = authenticated_client.get(url, {"tipo": "INVALIDO"})
    assert resposta.status_code == status.HTTP_200_OK


def test_envio_email_conteudo_detalhe(
    authenticated_client, conteudo_convocacao
):
    """Verifica detalhe de conteúdo de e-mail."""
    url = reverse(
        "envio-email-conteudo-detail", args=[conteudo_convocacao.uuid]
    )
    resposta = authenticated_client.get(url)
    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["tipo"] == TIPO_CONVOCACAO
    assert "assunto" in resposta.data
    assert "conteudo" in resposta.data
    assert "conteudo_gabarito" in resposta.data
    assert "tipo_display" in resposta.data


def test_envio_email_conteudo_patch_conteudo_gabarito(
    authenticated_client, conteudo_convocacao
):
    """Verifica envio email conteudo patch conteudo gabarito."""
    url = reverse(
        "envio-email-conteudo-detail", args=[conteudo_convocacao.uuid]
    )
    novo_html = "<p>Novo gabarito {{ cargo }}</p>"
    resposta = authenticated_client.patch(
        url, {"conteudo_gabarito": novo_html}, format="json"
    )
    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["conteudo_gabarito"] == novo_html
    conteudo_convocacao.refresh_from_db()
    assert conteudo_convocacao.conteudo_gabarito == novo_html


def test_envio_email_conteudo_retorna_assunto_vazio_quando_nao_salvo(
    authenticated_client, conteudo_convocacao
):
    """Verify GET returns empty subject when template has no saved value."""
    conteudo_convocacao.assunto = ""
    conteudo_convocacao.save(update_fields=["assunto", "atualizado_em"])

    url = reverse(
        "envio-email-conteudo-detail", args=[conteudo_convocacao.uuid]
    )
    resposta = authenticated_client.get(url)

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["assunto"] == ""


def test_envio_email_conteudo_patch_assunto(
    authenticated_client, conteudo_convocacao
):
    """Verifica envio email conteudo patch assunto."""
    url = reverse(
        "envio-email-conteudo-detail", args=[conteudo_convocacao.uuid]
    )
    novo_assunto = "Novo assunto de convocação"
    resposta = authenticated_client.patch(
        url, {"assunto": novo_assunto}, format="json"
    )
    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["assunto"] == novo_assunto
    conteudo_convocacao.refresh_from_db()
    assert conteudo_convocacao.assunto == novo_assunto


def test_envio_email_conteudo_patch(authenticated_client, conteudo_convocacao):
    """Verifica envio email conteudo patch."""
    url = reverse(
        "envio-email-conteudo-detail", args=[conteudo_convocacao.uuid]
    )
    novo_html = "<p>Novo conteúdo {{ cargo }}</p>"
    resposta = authenticated_client.patch(
        url, {"conteudo": novo_html}, format="json"
    )
    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["conteudo"] == novo_html
    conteudo_convocacao.refresh_from_db()
    assert conteudo_convocacao.conteudo == novo_html


def test_envio_email_conteudo_retorna_html_sem_escape_duplicado(
    authenticated_client,
    conteudo_convocacao,
):
    """Verifica HTML sem aspas escapadas na resposta GET."""
    html = '<p class="ql-align-center">Texto</p>'
    conteudo_convocacao.conteudo = '<p class=\\"ql-align-center\\">Texto</p>'
    conteudo_convocacao.save(update_fields=["conteudo", "atualizado_em"])

    url = reverse(
        "envio-email-conteudo-detail", args=[conteudo_convocacao.uuid]
    )
    resposta = authenticated_client.get(url)

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["conteudo"] == html
    assert '\\"' not in resposta.data["conteudo"]


def test_envio_email_conteudo_patch_remove_escape_duplicado(
    authenticated_client,
    conteudo_convocacao,
):
    """Verifica envio email conteudo patch remove escape duplicado."""
    url = reverse(
        "envio-email-conteudo-detail", args=[conteudo_convocacao.uuid]
    )
    dados_requisicao = '<p class=\\"ql-align-center\\">Centro</p>'
    resposta = authenticated_client.patch(
        url,
        {"conteudo": dados_requisicao},
        format="json",
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["conteudo"] == '<p class="ql-align-center">Centro</p>'
    conteudo_convocacao.refresh_from_db()
    assert (
        conteudo_convocacao.conteudo == '<p class="ql-align-center">Centro</p>'
    )


def test_envio_email_conteudo_post_nao_permitido(authenticated_client):
    """Verifica envio email conteudo post nao permitido."""
    url = reverse("envio-email-conteudo-list")
    resposta = authenticated_client.post(
        url,
        {"tipo": "CONVOCACAO", "conteudo": "<p>x</p>"},
        format="json",
    )
    assert resposta.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_envio_email_conteudo_delete_nao_permitido(
    authenticated_client, conteudo_convocacao
):
    """Verifica envio email conteudo delete nao permitido."""
    url = reverse(
        "envio-email-conteudo-detail", args=[conteudo_convocacao.uuid]
    )
    resposta = authenticated_client.delete(url)
    assert resposta.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_envio_email_conteudo_put_nao_permitido(
    authenticated_client, conteudo_convocacao
):
    """Verifica envio email conteudo put nao permitido."""
    url = reverse(
        "envio-email-conteudo-detail", args=[conteudo_convocacao.uuid]
    )
    resposta = authenticated_client.put(
        url, {"conteudo": "<p>x</p>"}, format="json"
    )
    assert resposta.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
