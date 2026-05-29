"""
Testes da API de templates de conteúdo de e-mail (GET e PATCH).
"""
import pytest
from django.urls import reverse
from rest_framework import status

from processos.models import EnvioEmailConteudo
from processos.models.envio_email import TIPO_CONVOCACAO

pytestmark = pytest.mark.django_db


@pytest.fixture
def conteudo_convocacao():
    return EnvioEmailConteudo.objects.get(tipo=TIPO_CONVOCACAO)


def test_envio_email_conteudo_list(authenticated_client, conteudo_convocacao):
    url = reverse('envio-email-conteudo-list')
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    data = response.data['results'] if 'results' in response.data else response.data
    assert len(data) >= 3
    tipos = {item['tipo'] for item in data}
    assert TIPO_CONVOCACAO in tipos


def test_envio_email_conteudo_list_filtrar_por_tipo(authenticated_client, conteudo_convocacao):
    url = reverse('envio-email-conteudo-list')
    response = authenticated_client.get(url, {'tipo': TIPO_CONVOCACAO})
    assert response.status_code == status.HTTP_200_OK
    data = response.data['results'] if 'results' in response.data else response.data
    assert len(data) == 1
    assert data[0]['tipo'] == TIPO_CONVOCACAO
    assert data[0]['uuid'] == str(conteudo_convocacao.uuid)


def test_envio_email_conteudo_list_filtrar_tipo_inexistente_retorna_vazio(authenticated_client):
    url = reverse('envio-email-conteudo-list')
    response = authenticated_client.get(url, {'tipo': 'INVALIDO'})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_envio_email_conteudo_retrieve(authenticated_client, conteudo_convocacao):
    url = reverse('envio-email-conteudo-detail', args=[conteudo_convocacao.uuid])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data['tipo'] == TIPO_CONVOCACAO
    assert 'conteudo' in response.data
    assert 'tipo_display' in response.data


def test_envio_email_conteudo_patch(authenticated_client, conteudo_convocacao):
    url = reverse('envio-email-conteudo-detail', args=[conteudo_convocacao.uuid])
    novo_html = '<p>Novo conteúdo {{ cargo }}</p>'
    response = authenticated_client.patch(url, {'conteudo': novo_html}, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert response.data['conteudo'] == novo_html
    conteudo_convocacao.refresh_from_db()
    assert conteudo_convocacao.conteudo == novo_html


def test_envio_email_conteudo_retorna_html_sem_escape_duplicado(
    authenticated_client, conteudo_convocacao,
):
    """GET não deve devolver \\\" literal; aspas normais como no banco após normalização."""
    html = '<p class="ql-align-center">Texto</p>'
    conteudo_convocacao.conteudo = '<p class=\\"ql-align-center\\">Texto</p>'
    conteudo_convocacao.save(update_fields=['conteudo', 'atualizado_em'])

    url = reverse('envio-email-conteudo-detail', args=[conteudo_convocacao.uuid])
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['conteudo'] == html
    assert '\\"' not in response.data['conteudo']


def test_envio_email_conteudo_patch_remove_escape_duplicado(
    authenticated_client, conteudo_convocacao,
):
    url = reverse('envio-email-conteudo-detail', args=[conteudo_convocacao.uuid])
    payload = '<p class=\\"ql-align-center\\">Centro</p>'
    response = authenticated_client.patch(
        url, {'conteudo': payload}, format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.data['conteudo'] == '<p class="ql-align-center">Centro</p>'
    conteudo_convocacao.refresh_from_db()
    assert conteudo_convocacao.conteudo == '<p class="ql-align-center">Centro</p>'


def test_envio_email_conteudo_post_nao_permitido(authenticated_client):
    url = reverse('envio-email-conteudo-list')
    response = authenticated_client.post(
        url,
        {'tipo': 'CONVOCACAO', 'conteudo': '<p>x</p>'},
        format='json',
    )
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_envio_email_conteudo_delete_nao_permitido(authenticated_client, conteudo_convocacao):
    url = reverse('envio-email-conteudo-detail', args=[conteudo_convocacao.uuid])
    response = authenticated_client.delete(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


def test_envio_email_conteudo_put_nao_permitido(authenticated_client, conteudo_convocacao):
    url = reverse('envio-email-conteudo-detail', args=[conteudo_convocacao.uuid])
    response = authenticated_client.put(url, {'conteudo': '<p>x</p>'}, format='json')
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
