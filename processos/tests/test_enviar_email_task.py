"""Testes unitários para processos.tasks.enviar_email_task."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from processos.models import EnvioEmail, EnvioEmailCandidato
from processos.models.envio_email import TIPO_CONVOCACAO
from processos.models.envio_email_candidato import (
    ENVIO_STATUS_ERRO,
    ENVIO_STATUS_PENDENTE,
    ENVIO_STATUS_SUCESSO,
)
from processos.tasks.enviar_email_task import (
    CID_LOGO_SIGLA,
    LOGO_EMAIL_PATH,
    enviar_email_candidato_task,
)

ASSUNTO_TESTE = "Assunto de teste"

pytestmark = pytest.mark.django_db


def _task_kwargs(candidato):
    """Executa  task kwargs."""
    return {
        "email": candidato.email,
        "assunto": ASSUNTO_TESTE,
        "conteudo": "<p>Olá</p>",
        "envio_email_candidato_id": str(candidato.uuid),
        "correlation_id": "1234567890",
    }


@pytest.fixture
def processo_convocacao(db):
    """Executa processo convocacao."""
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
    """Executa envio email."""
    return EnvioEmail.objects.create(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        tipo=TIPO_CONVOCACAO,
        quantidade_candidatos=1,
    )


@pytest.fixture
def envio_candidato(envio_email):
    """Executa envio candidato."""
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


@patch("processos.tasks.enviar_email_task.LOGO_EMAIL_PATH")
@patch("processos.tasks.enviar_email_task.EmailMultiAlternatives")
def test_enviar_email_candidato_task_converte_base64_para_cid(
    mock_email_cls,
    mock_logo_path,
    envio_candidato,
):
    """Verifica enviar email candidato task converte base64 para cid."""
    mock_logo_path.is_file.return_value = False
    mock_msg = MagicMock()
    mock_email_cls.return_value = mock_msg
    html = f'<img src="{PNG_1X1_DATA_URI}">'

    enviar_email_candidato_task.apply(
        kwargs={**_task_kwargs(envio_candidato), "conteudo": html},
    ).get()

    html_enviado = mock_msg.attach_alternative.call_args[0][0]
    assert "cid:email_img_0" in html_enviado
    assert PNG_1X1_DATA_URI not in html_enviado
    assert mock_msg.mixed_subtype == "related"
    assert mock_msg.attach.call_count == 1


@patch("processos.tasks.enviar_email_task.LOGO_EMAIL_PATH")
@patch("processos.tasks.enviar_email_task.EmailMultiAlternatives")
def test_enviar_email_candidato_task_sucesso_com_logo(
    mock_email_cls, mock_logo_path, envio_candidato
):
    """Verifica enviar email candidato task sucesso com logo."""
    mock_logo_path.is_file.return_value = True
    mock_logo_path.read_bytes.return_value = b"\x89PNG\r\n\x1a\n"
    mock_msg = MagicMock()
    mock_email_cls.return_value = mock_msg

    enviar_email_candidato_task.apply(
        kwargs=_task_kwargs(envio_candidato)
    ).get()

    call_kw = mock_email_cls.call_args[1]
    assert call_kw["subject"] == ASSUNTO_TESTE
    assert call_kw["body"] == "Olá"
    assert call_kw["to"] == [envio_candidato.email]
    mock_msg.send.assert_called_once()

    envio_candidato.refresh_from_db()
    assert envio_candidato.status == ENVIO_STATUS_SUCESSO
    assert envio_candidato.status_detalhe == ""


@patch("processos.tasks.enviar_email_task.LOGO_EMAIL_PATH")
@patch("processos.tasks.enviar_email_task.EmailMultiAlternatives")
def test_enviar_email_candidato_task_sucesso_sem_logo(
    mock_email_cls, mock_logo_path, envio_candidato
):
    """Verifica enviar email candidato task sucesso sem logo."""
    mock_logo_path.is_file.return_value = False
    mock_msg = MagicMock()
    mock_email_cls.return_value = mock_msg

    enviar_email_candidato_task.apply(
        kwargs={**_task_kwargs(envio_candidato), "conteudo": "<p>Conteúdo</p>"}
    ).get()

    mock_msg.attach.assert_not_called()
    envio_candidato.refresh_from_db()
    assert envio_candidato.status == ENVIO_STATUS_SUCESSO


@patch("processos.tasks.enviar_email_task.LOGO_EMAIL_PATH")
@patch("processos.tasks.enviar_email_task.EmailMultiAlternatives")
def test_enviar_email_candidato_task_erro_no_send(
    mock_email_cls, mock_logo_path, envio_candidato
):
    """Verifica enviar email candidato task erro no send."""
    mock_logo_path.is_file.return_value = False
    mock_msg = MagicMock()
    mock_msg.send.side_effect = Exception("Connection refused")
    mock_email_cls.return_value = mock_msg

    enviar_email_candidato_task.apply(
        kwargs=_task_kwargs(envio_candidato)
    ).get()

    envio_candidato.refresh_from_db()
    assert envio_candidato.status == ENVIO_STATUS_ERRO
    assert "Connection refused" in envio_candidato.status_detalhe


def test_constantes_task():
    """Verifica constantes task."""
    assert CID_LOGO_SIGLA == "logo_sigla"
    assert "templates" in str(LOGO_EMAIL_PATH) and "assets" in str(
        LOGO_EMAIL_PATH
    )
