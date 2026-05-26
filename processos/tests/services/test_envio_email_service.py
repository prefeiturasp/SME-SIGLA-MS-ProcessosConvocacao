"""
Testes unitários para processos.services.envio_email_service.
"""
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from uuid import uuid4

from processos.models import ProcessoConvocacao, EnvioEmail, EnvioEmailCandidato
from processos.models.envio_email import TIPO_CONVOCACAO
from processos.models.envio_email_candidato import ENVIO_STATUS_PENDENTE
from processos.services.envio_email_service import (
    iniciar_processamento_envio,
    ASSUNTO_POR_TIPO,
    TEMPLATE_POR_TIPO,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def processo_convocacao(db):
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid4(),
        concurso_nome="Concurso Teste",
        descricao="Descrição",
        tipo_escolha='NOVA_AUTORIZACAO',
        status='EM_ANDAMENTO',
    )


@patch('processos.services.envio_email_service.CandidatosApiService.buscar_habilitados_por_processo')
def test_iniciar_processamento_envio_lista_vazia(mock_buscar, processo_convocacao):
    mock_buscar.return_value = []

    with patch('config.celery.app') as mock_celery:
        envio = iniciar_processamento_envio(
            processo_uuid=processo_convocacao.uuid,
            processo_nome=processo_convocacao.concurso_nome,
            tipo=TIPO_CONVOCACAO,
            conteudo='<p>Conteúdo</p>',
        )

    assert envio.quantidade_candidatos == 0
    assert EnvioEmailCandidato.objects.filter(envio_email=envio).count() == 0
    mock_celery.send_task.assert_not_called()


@patch('config.celery.app')
@patch('processos.services.envio_email_service.render_to_string')
@patch('processos.services.envio_email_service.CandidatosApiService.buscar_habilitados_por_processo')
def test_iniciar_processamento_envio_um_habilitado(mock_buscar, mock_render, mock_celery, processo_convocacao):
    mock_buscar.return_value = [
        {
            'candidato': {'nome': 'Fulano', 'registro_funcional': '1234567', 'email': 'fulano@test.com'},
            'descricao_cargo': 'Analista',
            'classificacao': 1,
            'categoria_efetiva': '',
        },
    ]
    mock_render.return_value = '<p>Email</p>'

    envio = iniciar_processamento_envio(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        tipo=TIPO_CONVOCACAO,
        conteudo='<p>Conteúdo</p>',
    )

    assert envio.tipo == TIPO_CONVOCACAO
    cands = list(EnvioEmailCandidato.objects.filter(envio_email=envio))
    assert len(cands) == 1
    assert cands[0].status == ENVIO_STATUS_PENDENTE
    mock_celery.send_task.assert_called_once()
    assert mock_celery.send_task.call_args[1]['kwargs']['assunto'] == ASSUNTO_POR_TIPO[TIPO_CONVOCACAO]


def test_constantes_servico():
    assert TIPO_CONVOCACAO in ASSUNTO_POR_TIPO
    assert TEMPLATE_POR_TIPO[TIPO_CONVOCACAO] == 'email/email_convocacao_padrao.html'
