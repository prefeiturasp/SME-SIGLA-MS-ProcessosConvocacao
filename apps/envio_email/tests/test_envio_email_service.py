"""Testes unitários para envio_email.services.envio_email_service."""

from unittest.mock import patch
from uuid import uuid4

import pytest

from envio_email.models import EnvioEmailCandidato
from processos.models import ProcessoConvocacao
from envio_email.models.envio_email import TIPO_CONVOCACAO
from envio_email.models.envio_email_candidato import ENVIO_STATUS_PENDENTE
from envio_email.services.envio_email_service import (
    ASSUNTO_POR_TIPO,
    TEMPLATE_POR_TIPO,
    _resolver_assunto_envio,
    _resolver_conteudo_envio,
    iniciar_processamento_envio,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def processo_convocacao(db):
    """Cria processo de convocação para teste."""
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid4(),
        concurso_nome="Concurso Teste",
        descricao="Descrição",
        tipo_escolha="NOVA_AUTORIZACAO",
        status="EM_ANDAMENTO",
    )


@patch(
    "envio_email.services.envio_email_service.CandidatosApiService.buscar_habilitados_por_processo"
)
def test_iniciar_processamento_envio_lista_vazia(
    mock_buscar, processo_convocacao
):
    """Verifica iniciar processamento envio lista vazia."""
    mock_buscar.return_value = []

    with patch("config.celery.app") as mock_celery:
        envio = iniciar_processamento_envio(
            processo_uuid=processo_convocacao.uuid,
            processo_nome=processo_convocacao.concurso_nome,
            tipo=TIPO_CONVOCACAO,
            conteudo="<p>Conteúdo</p>",
        )
    assert envio["quantidade_candidatos"] == 0
    assert EnvioEmailCandidato.objects.filter(envio_email__uuid=envio["uuid"]).count() == 0
    mock_celery.send_task.assert_not_called()


@patch("config.celery.app")
@patch("envio_email.services.envio_email_service.render_to_string")
@patch(
    "envio_email.services.envio_email_service.CandidatosApiService.buscar_habilitados_por_processo"
)
def test_iniciar_processamento_envio_um_habilitado(
    mock_buscar, mock_render, mock_celery, processo_convocacao
):
    """Verifica iniciar processamento envio um habilitado."""
    mock_buscar.return_value = [
        {
            "candidato": {
                "nome": "Fulano",
                "registro_funcional": "1234567",
                "email": "fulano@test.com",
            },
            "descricao_cargo": "Analista",
            "classificacao": 1,
            "categoria_efetiva": "",
        },
    ]
    mock_render.return_value = "<p>Email</p>"

    envio = iniciar_processamento_envio(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        tipo=TIPO_CONVOCACAO,
        conteudo="<p>Conteúdo</p>",
    )
    # breakpoint()
    assert envio["tipo"] == TIPO_CONVOCACAO
    candidatos = list(EnvioEmailCandidato.objects.filter(envio_email__uuid=envio["uuid"]))
    assert len(candidatos) == 1
    assert candidatos[0].status == ENVIO_STATUS_PENDENTE
    mock_celery.send_task.assert_called_once()
    assert (
        mock_celery.send_task.call_args[1]["kwargs"]["assunto"]
        == ASSUNTO_POR_TIPO[TIPO_CONVOCACAO]
    )


@patch("config.celery.app")
@patch("envio_email.services.envio_email_service.render_to_string")
@patch(
    "envio_email.services.envio_email_service.CandidatosApiService.buscar_habilitados_por_processo"
)
def test_iniciar_processamento_envio_usa_assunto_informado(
    mock_buscar, mock_render, mock_celery, processo_convocacao
):
    """Verifica envio com assunto personalizado informado no corpo."""
    mock_buscar.return_value = [
        {
            "candidato": {
                "nome": "Fulano",
                "registro_funcional": "1234567",
                "email": "fulano@test.com",
            },
            "descricao_cargo": "Analista",
            "classificacao": 1,
            "categoria_efetiva": "",
        },
    ]
    mock_render.return_value = "<p>Email</p>"

    iniciar_processamento_envio(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        tipo=TIPO_CONVOCACAO,
        conteudo="<p>Conteúdo</p>",
        assunto="Assunto personalizado",
    )

    assert (
        mock_celery.send_task.call_args[1]["kwargs"]["assunto"]
        == "Assunto personalizado"
    )


@patch("config.celery.app")
@patch("envio_email.services.envio_email_service.render_to_string")
@patch(
    "envio_email.services.envio_email_service.CandidatosApiService.buscar_habilitados_por_processo"
)
def test_iniciar_processamento_envio_usa_gabarito_quando_conteudo_vazio(
    mock_buscar, mock_render, mock_celery, processo_convocacao, conteudo_convocacao
):
    """Verifica fallback para gabarito quando corpo de conteúdo vazio."""
    mock_buscar.return_value = [
        {
            "candidato": {
                "nome": "Fulano",
                "registro_funcional": "1234567",
                "email": "fulano@test.com",
            },
            "descricao_cargo": "Analista",
            "classificacao": 1,
            "categoria_efetiva": "",
        },
    ]
    mock_render.return_value = "<p>Email</p>"
    conteudo_convocacao.conteudo = ""
    conteudo_convocacao.conteudo_gabarito = "<p>gabarito envio</p>"
    conteudo_convocacao.save(
        update_fields=["conteudo", "conteudo_gabarito", "atualizado_em"]
    )

    iniciar_processamento_envio(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        tipo=TIPO_CONVOCACAO,
        conteudo="",
        assunto="",
    )

    mock_celery.send_task.assert_called_once()
    assert (
        mock_celery.send_task.call_args[1]["kwargs"]["assunto"]
        == ASSUNTO_POR_TIPO[TIPO_CONVOCACAO]
    )


def test_constantes_servico():
    """Verifica constantes servico."""
    assert TIPO_CONVOCACAO in ASSUNTO_POR_TIPO
    assert (
        TEMPLATE_POR_TIPO[TIPO_CONVOCACAO]
        == "email/email_convocacao_padrao.html"
    )


def test_resolver_conteudo_envio_usa_corpo_quando_informado():
    """Verifica resolver conteúdo usa corpo quando informado."""
    assert _resolver_conteudo_envio(TIPO_CONVOCACAO, "<p>personalizado</p>") == "<p>personalizado</p>"


def test_resolver_conteudo_envio_fallback_para_gabarito(conteudo_convocacao):
    """Verifica fallback para gabarito quando corpo vazio."""
    conteudo_convocacao.conteudo = ""
    conteudo_convocacao.conteudo_gabarito = "<p>gabarito</p>"
    conteudo_convocacao.save(
        update_fields=["conteudo", "conteudo_gabarito", "atualizado_em"]
    )

    assert _resolver_conteudo_envio(TIPO_CONVOCACAO, "") == "<p>gabarito</p>"


def test_resolver_conteudo_envio_prefere_conteudo_salvo(conteudo_convocacao):
    """Verifica preferência por conteúdo salvo antes do gabarito."""
    conteudo_convocacao.conteudo = "<p>salvo</p>"
    conteudo_convocacao.conteudo_gabarito = "<p>gabarito</p>"
    conteudo_convocacao.save(
        update_fields=["conteudo", "conteudo_gabarito", "atualizado_em"]
    )

    assert _resolver_conteudo_envio(TIPO_CONVOCACAO, "") == "<p>salvo</p>"


def test_resolver_assunto_envio_usa_corpo_quando_informado():
    """Verifica resolver assunto usa corpo quando informado."""
    assert _resolver_assunto_envio(TIPO_CONVOCACAO, "Assunto personalizado") == "Assunto personalizado"


def test_resolver_assunto_envio_fallback_para_padrao_do_tipo(conteudo_convocacao):
    """Verifica fallback para assunto padrão quando corpo vazio."""
    conteudo_convocacao.assunto = "Assunto do template"
    conteudo_convocacao.save(update_fields=["assunto", "atualizado_em"])

    assert (
        _resolver_assunto_envio(TIPO_CONVOCACAO, "")
        == ASSUNTO_POR_TIPO[TIPO_CONVOCACAO]
    )
