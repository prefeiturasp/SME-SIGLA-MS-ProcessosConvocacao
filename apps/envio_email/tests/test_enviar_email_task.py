"""Testes unitários para envio_email.tasks.enviar_email_task."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from envio_email.models import EnvioEmail, EnvioEmailCandidato
from envio_email.models.envio_email import TIPO_CONVOCACAO
from envio_email.models.envio_email_candidato import (
    ENVIO_STATUS_ERRO,
    ENVIO_STATUS_PENDENTE,
    ENVIO_STATUS_SUCESSO,
)
from envio_email.tasks.enviar_email_task import (
    CAMINHO_LOGO_EMAIL,
    CID_LOGO_SIGLA,
    enviar_email_candidato_task,
)

ASSUNTO_TESTE = "Assunto de teste"

pytestmark = pytest.mark.django_db


def _kwargs_task(candidato):
    """Monta kwargs da task de envio."""
    return {
        "email": candidato.email,
        "assunto": ASSUNTO_TESTE,
        "conteudo": "<p>Olá</p>",
        "envio_email_candidato_id": str(candidato.uuid),
        "correlation_id": "1234567890",
    }


@pytest.fixture
def processo_convocacao(db):
    """Cria processo de convocação para teste."""
    from processos.models import ProcessoConvocacao

    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid4(),
        concurso_nome="Concurso Teste",
        descricao="Descrição",
        tipo_escolha="NOVA_AUTORIZACAO",
        status="EM_ANDAMENTO",
    )


@pytest.fixture
def envio_email(processo_convocacao):
    """Cria registro de envio de e-mail para teste."""
    return EnvioEmail.objects.create(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        tipo=TIPO_CONVOCACAO,
        quantidade_candidatos=1,
    )


@pytest.fixture
def envio_candidato(envio_email):
    """Cria candidato vinculado ao envio para teste."""
    return EnvioEmailCandidato.objects.create(
        envio_email=envio_email,
        nome="Fulano",
        rf="1234567",
        email="fulano@test.com",
        status=ENVIO_STATUS_PENDENTE,
        status_detalhe="",
        conteudo="<p>Conteúdo email</p>",
    )


PNG_1X1_DATA_URI = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQ"
    "DwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@patch("envio_email.tasks.enviar_email_task.CAMINHO_LOGO_EMAIL")
@patch("envio_email.tasks.enviar_email_task.EmailMultiAlternatives")
def test_enviar_email_candidato_task_converte_base64_para_cid(
    mock_classe_email,
    mock_caminho_logo,
    envio_candidato,
):
    """Verifica enviar email candidato task converte base64 para cid."""
    mock_caminho_logo.is_file.return_value = False
    mock_mensagem = MagicMock()
    mock_classe_email.return_value = mock_mensagem
    html = f'<img src="{PNG_1X1_DATA_URI}">'

    enviar_email_candidato_task.apply(
        kwargs={**_kwargs_task(envio_candidato), "conteudo": html},
    ).get()

    html_enviado = mock_mensagem.attach_alternative.call_args[0][0]
    assert "cid:email_img_0" in html_enviado
    assert PNG_1X1_DATA_URI not in html_enviado
    assert mock_mensagem.mixed_subtype == "related"
    assert mock_mensagem.attach.call_count == 1


@patch("envio_email.tasks.enviar_email_task.CAMINHO_LOGO_EMAIL")
@patch("envio_email.tasks.enviar_email_task.EmailMultiAlternatives")
def test_enviar_email_candidato_task_sucesso_com_logo(
    mock_classe_email, mock_caminho_logo, envio_candidato
):
    """Verifica enviar email candidato task sucesso com logo."""
    mock_caminho_logo.is_file.return_value = True
    mock_caminho_logo.read_bytes.return_value = b"\x89PNG\r\n\x1a\n"
    mock_mensagem = MagicMock()
    mock_classe_email.return_value = mock_mensagem

    enviar_email_candidato_task.apply(
        kwargs=_kwargs_task(envio_candidato)
    ).get()

    kwargs_chamada = mock_classe_email.call_args[1]
    assert kwargs_chamada["subject"] == ASSUNTO_TESTE
    assert kwargs_chamada["body"] == "Olá"
    assert kwargs_chamada["to"] == [envio_candidato.email]
    mock_mensagem.send.assert_called_once()

    envio_candidato.refresh_from_db()
    assert envio_candidato.status == ENVIO_STATUS_SUCESSO
    assert envio_candidato.status_detalhe == ""


@patch("envio_email.tasks.enviar_email_task.CAMINHO_LOGO_EMAIL")
@patch("envio_email.tasks.enviar_email_task.EmailMultiAlternatives")
def test_enviar_email_candidato_task_sucesso_sem_logo(
    mock_classe_email, mock_caminho_logo, envio_candidato
):
    """Verifica enviar email candidato task sucesso sem logo."""
    mock_caminho_logo.is_file.return_value = False
    mock_mensagem = MagicMock()
    mock_classe_email.return_value = mock_mensagem

    enviar_email_candidato_task.apply(
        kwargs={**_kwargs_task(envio_candidato), "conteudo": "<p>Conteúdo</p>"}
    ).get()

    mock_mensagem.attach.assert_not_called()
    envio_candidato.refresh_from_db()
    assert envio_candidato.status == ENVIO_STATUS_SUCESSO


@patch("envio_email.tasks.enviar_email_task.CAMINHO_LOGO_EMAIL")
@patch("envio_email.tasks.enviar_email_task.EmailMultiAlternatives")
def test_enviar_email_candidato_task_erro_no_envio(
    mock_classe_email, mock_caminho_logo, envio_candidato
):
    """Verifica erro no envio do e-mail na task."""
    mock_caminho_logo.is_file.return_value = False
    mock_mensagem = MagicMock()
    mock_mensagem.send.side_effect = Exception("Connection refused")
    mock_classe_email.return_value = mock_mensagem

    enviar_email_candidato_task.apply(
        kwargs=_kwargs_task(envio_candidato)
    ).get()

    envio_candidato.refresh_from_db()
    assert envio_candidato.status == ENVIO_STATUS_ERRO
    assert "Connection refused" in envio_candidato.status_detalhe


def test_constantes_task():
    """Verifica constantes task."""
    assert CID_LOGO_SIGLA == "logo_sigla"
    assert "templates" in str(CAMINHO_LOGO_EMAIL) and "assets" in str(
        CAMINHO_LOGO_EMAIL
    )
