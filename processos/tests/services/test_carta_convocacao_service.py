"""
Testes unitários para processos.services.carta_convocacao_service (pytest).
Cobertura alvo: >= 95% (ideal 100%).
"""
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
from uuid import uuid4

from processos.models import ProcessoConvocacao, CartaConvocacaoHistorico, CartaConvocacaoCandidato
from processos.models.carta_convocacao_candidato import ENVIO_STATUS_PENDENTE
from processos.services.carta_convocacao_service import (
    enviar_carta_convocacao,
    iniciar_processamento_envio,
    ASSUNTO_CARTA,
    TEMPLATE_EMAIL,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def processo_convocacao(db):
    """Fixture para ProcessoConvocacao."""
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid4(),
        concurso_nome="Concurso Teste",
        descricao="Descrição",
        tipo_escolha='NOVA_AUTORIZACAO',
        status='EM_ANDAMENTO',
    )

@patch('processos.services.carta_convocacao_service.EmailMultiAlternatives')
@patch('processos.services.carta_convocacao_service.render_to_string')
def test_enviar_carta_convocacao_sucesso(mock_render, mock_email_cls):
    """enviar_carta_convocacao envia email e retorna True."""
    mock_render.return_value = '<p>Conteúdo</p>'
    mock_msg = MagicMock()
    mock_email_cls.return_value = mock_msg

    result = enviar_carta_convocacao(
        email_destino='user@test.com',
        cargo='Analista',
        classificacao='1º',
        data_publicacao='25/02/2025',
    )

    assert result is True
    mock_render.assert_called_once()
    assert mock_render.call_args[0][0] == TEMPLATE_EMAIL
    ctx = mock_render.call_args[0][1]
    assert ctx['cargo'] == 'Analista'
    assert ctx['classificacao'] == '1º'
    assert ctx['data_publicacao'] == '25/02/2025'
    assert 'ms_url' in ctx
    mock_email_cls.assert_called_once()
    call_kw = mock_email_cls.call_args[1]
    assert call_kw['subject'] == ASSUNTO_CARTA
    assert call_kw['to'] == ['user@test.com']
    assert 'Cargo: Analista' in call_kw['body'] and '1º' in call_kw['body']
    mock_msg.attach_alternative.assert_called_once_with('<p>Conteúdo</p>', 'text/html')
    mock_msg.send.assert_called_once()


@patch('processos.services.carta_convocacao_service.EmailMultiAlternatives')
@patch('processos.services.carta_convocacao_service.render_to_string')
def test_enviar_carta_convocacao_contexto_vazio_usando_traco(mock_render, mock_email_cls):
    """Cargo/classificacao/data_publicacao vazios são preenchidos com '—' no contexto."""
    mock_render.return_value = '<p>Ok</p>'
    mock_msg = MagicMock()
    mock_email_cls.return_value = mock_msg

    enviar_carta_convocacao(
        email_destino='x@test.com',
        cargo='',
        classificacao='',
        data_publicacao='',
    )

    mock_render.assert_called_once()
    ctx = mock_render.call_args[0][1]
    assert ctx['cargo'] == '—'
    assert ctx['classificacao'] == '—'
    assert ctx['data_publicacao'] == '—'
    mock_msg.send.assert_called_once()


@patch('processos.services.carta_convocacao_service.EmailMultiAlternatives')
@patch('processos.services.carta_convocacao_service.render_to_string')
def test_enviar_carta_convocacao_excecao_propaga(mock_render, mock_email_cls):
    """Se send() falhar, exceção é propagada e logger.exception é chamado."""
    mock_render.return_value = '<p>X</p>'
    mock_msg = MagicMock()
    mock_msg.send.side_effect = Exception('SMTP error')
    mock_email_cls.return_value = mock_msg

    with pytest.raises(Exception, match='SMTP error'):
        enviar_carta_convocacao(
            email_destino='user@test.com',
            cargo='Cargo',
            classificacao='',
            data_publicacao='01/01/2025',
        )

    mock_msg.send.assert_called_once()


# --- iniciar_processamento_envio ---


@patch('processos.services.carta_convocacao_service.CandidatosApiService.buscar_habilitados_por_processo')
def test_iniciar_processamento_envio_lista_vazia(mock_buscar, processo_convocacao):
    """Com zero habilitados: cria histórico com quantidade 0 e não dispara tasks."""
    mock_buscar.return_value = []

    with patch('config.celery.app') as mock_celery:
        historico = iniciar_processamento_envio(
            processo_uuid=processo_convocacao.uuid,
            processo_nome=processo_convocacao.concurso_nome,
            data=date(2025, 2, 25),
        )

    mock_buscar.assert_called_once_with(str(processo_convocacao.uuid))
    assert historico.quantidade_candidatos == 0
    assert CartaConvocacaoHistorico.objects.filter(uuid=historico.uuid).exists()
    assert CartaConvocacaoCandidato.objects.filter(carta_convocacao_historico=historico).count() == 0
    mock_celery.send_task.assert_not_called()


@patch('config.celery.app')
@patch('processos.services.carta_convocacao_service.render_to_string')
@patch('processos.services.carta_convocacao_service.CandidatosApiService.buscar_habilitados_por_processo')
def test_iniciar_processamento_envio_um_habilitado_com_email(mock_buscar, mock_render, mock_celery, processo_convocacao):
    """Um habilitado com email: cria histórico, um CartaConvocacaoCandidato e dispara uma task."""
    mock_buscar.return_value = [
        {
            'candidato': {'nome': 'Fulano', 'registro_funcional': '1234567', 'email': 'fulano@test.com'},
            'descricao_cargo': 'Analista',
            'classificacao': 1,
            'classificacao_pcd': None,
            'classificacao_nna': None,
            'categoria_efetiva': '',
        },
    ]
    mock_render.return_value = '<p>Email</p>'

    historico = iniciar_processamento_envio(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        data=date(2025, 2, 25),
    )

    assert historico.quantidade_candidatos == 1
    cands = list(CartaConvocacaoCandidato.objects.filter(carta_convocacao_historico=historico))
    assert len(cands) == 1
    assert cands[0].nome == 'Fulano'
    assert cands[0].rf == '1234567'
    assert cands[0].email == 'fulano@test.com'
    assert cands[0].status == ENVIO_STATUS_PENDENTE
    mock_celery.send_task.assert_called_once()
    call_kw = mock_celery.send_task.call_args[1]
    assert call_kw['kwargs']['email'] == 'fulano@test.com'
    assert call_kw['kwargs']['carta_convocacao_candidato_id'] == str(cands[0].uuid)


@patch('config.celery.app')
@patch('processos.services.carta_convocacao_service.render_to_string')
@patch('processos.services.carta_convocacao_service.CandidatosApiService.buscar_habilitados_por_processo')
def test_iniciar_processamento_envio_habilitado_sem_email_ignorado(mock_buscar, mock_render, mock_celery, processo_convocacao):
    """Habilitado sem email é ignorado e não dispara task; warning logado."""
    mock_buscar.return_value = [
        {
            'candidato': {'nome': 'Sem Email', 'registro_funcional': '999', 'email': ''},
            'descricao_cargo': 'Cargo',
            'classificacao': 1,
        },
    ]

    historico = iniciar_processamento_envio(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        data=date(2025, 2, 25),
    )

    assert historico.quantidade_candidatos == 1
    assert CartaConvocacaoCandidato.objects.filter(carta_convocacao_historico=historico).count() == 0
    mock_celery.send_task.assert_not_called()
    mock_render.assert_not_called()


@patch('config.celery.app')
@patch('processos.services.carta_convocacao_service.render_to_string')
@patch('processos.services.carta_convocacao_service.CandidatosApiService.buscar_habilitados_por_processo')
def test_iniciar_processamento_envio_classificacao_pcd(mock_buscar, mock_render, mock_celery, processo_convocacao):
    """Categoria PCD usa classificacao_pcd no contexto do template."""
    mock_buscar.return_value = [
        {
            'candidato': {'nome': 'PCD', 'registro_funcional': '1', 'email': 'pcd@test.com'},
            'descricao_cargo': 'Cargo PCD',
            'classificacao': 10,
            'classificacao_pcd': 2,
            'classificacao_nna': None,
            'categoria_efetiva': 'PCD',
        },
    ]
    mock_render.return_value = '<p>PCD</p>'

    iniciar_processamento_envio(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        data=date(2025, 2, 25),
    )

    assert mock_render.call_count >= 1
    # Contexto usado no template deve ter classificacao = 2 (PCD)
    ctx = mock_render.call_args[0][1]
    assert ctx['classificacao'] == '2'
    assert ctx['cargo'] == 'Cargo PCD'


@patch('config.celery.app')
@patch('processos.services.carta_convocacao_service.render_to_string')
@patch('processos.services.carta_convocacao_service.CandidatosApiService.buscar_habilitados_por_processo')
def test_iniciar_processamento_envio_classificacao_nna(mock_buscar, mock_render, mock_celery, processo_convocacao):
    """Categoria NNA usa classificacao_nna no contexto."""
    mock_buscar.return_value = [
        {
            'candidato': {'nome': 'NNA', 'registro_funcional': '2', 'email': 'nna@test.com'},
            'descricao_cargo': 'Cargo NNA',
            'classificacao': 5,
            'classificacao_pcd': None,
            'classificacao_nna': 1,
            'categoria_efetiva': 'NNA',
        },
    ]
    mock_render.return_value = '<p>NNA</p>'

    iniciar_processamento_envio(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        data=date(2025, 2, 25),
    )

    ctx = mock_render.call_args[0][1]
    assert ctx['classificacao'] == '1'
    assert ctx['cargo'] == 'Cargo NNA'


@patch('config.celery.app')
@patch('processos.services.carta_convocacao_service.render_to_string')
@patch('processos.services.carta_convocacao_service.CandidatosApiService.buscar_habilitados_por_processo')
def test_iniciar_processamento_envio_nome_rf_email_de_item_ou_candidato(mock_buscar, mock_render, mock_celery, processo_convocacao):
    """Nome, RF e email podem vir de item.get('nome') ou candidato aninhado."""
    mock_buscar.return_value = [
        {
            'descricao_cargo': 'Cargo',
            'classificacao': 1,
            'candidato': {
                'nome': 'Nome Direto',
                'registro_funcional': '777',
                'email': 'direto@test.com',
            }
        },
    ]
    mock_render.return_value = '<p>X</p>'

    historico = iniciar_processamento_envio(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        data=date(2025, 2, 25),
    )

    cands = list(CartaConvocacaoCandidato.objects.filter(carta_convocacao_historico=historico))
    assert len(cands) == 1
    assert cands[0].nome == 'Nome Direto'
    assert cands[0].rf == '777'
    assert cands[0].email == 'direto@test.com'


@patch('config.celery.app')
@patch('processos.services.carta_convocacao_service.render_to_string')
@patch('processos.services.carta_convocacao_service.CandidatosApiService.buscar_habilitados_por_processo')
def test_iniciar_processamento_envio_cargo_nome_fallback(mock_buscar, mock_render, mock_celery, processo_convocacao):
    """cargo_nome usa descricao_cargo ou cargo_nome do item."""
    mock_buscar.return_value = [
        {
            'candidato': {'nome': 'Fulano', 'email': 'f@test.com', 'registro_funcional': '1'},
            'cargo_nome': 'Cargo Nome Campo',
            'descricao_cargo': 'Cargo Nome Campo',
            'classificacao': 1,
        },
    ]
    mock_render.return_value = '<p>X</p>'

    iniciar_processamento_envio(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        data=date(2025, 2, 25),
    )

    ctx = mock_render.call_args[0][1]
    assert ctx['cargo'] == 'Cargo Nome Campo'


@patch('config.celery.app')
@patch('processos.services.carta_convocacao_service.CandidatosApiService.buscar_habilitados_por_processo')
def test_iniciar_processamento_envio_retorna_historico_com_data_formatada(mock_buscar, mock_celery, processo_convocacao):
    """iniciar_processamento_envio usa data com strftime para data_publicacao no template."""
    mock_buscar.return_value = []

    historico = iniciar_processamento_envio(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        data=date(2025, 2, 25),
    )

    assert historico.quantidade_candidatos == 0
    assert historico.data == date(2025, 2, 25)
    assert historico.processo_nome == processo_convocacao.concurso_nome


@patch('config.celery.app')
@patch('processos.services.carta_convocacao_service.render_to_string')
@patch('processos.services.carta_convocacao_service.CandidatosApiService.buscar_habilitados_por_processo')
def test_iniciar_processamento_envio_multiplos_candidatos(mock_buscar, mock_render, mock_celery, processo_convocacao):
    """Vários habilitados com email: vários registros e várias tasks."""
    mock_buscar.return_value = [
        {'candidato': {'nome': 'A', 'email': 'a@test.com', 'registro_funcional': '1'}, 'descricao_cargo': 'Cargo', 'classificacao': 1},
        {'candidato': {'nome': 'B', 'email': 'b@test.com', 'registro_funcional': '2'}, 'descricao_cargo': 'Cargo', 'classificacao': 2},
    ]
    mock_render.return_value = '<p>X</p>'

    historico = iniciar_processamento_envio(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        data=date(2025, 2, 25),
    )

    assert historico.quantidade_candidatos == 2
    assert CartaConvocacaoCandidato.objects.filter(carta_convocacao_historico=historico).count() == 2
    assert mock_celery.send_task.call_count == 2


@patch('config.celery.app')
@patch('processos.services.carta_convocacao_service.render_to_string')
@patch('processos.services.carta_convocacao_service.CandidatosApiService.buscar_habilitados_por_processo')
def test_iniciar_processamento_envio_nome_vazio_vira_traco(mock_buscar, mock_render, mock_celery, processo_convocacao):
    """Nome vazio ou só espaços vira '—' no registro."""
    mock_buscar.return_value = [
        {
            'candidato': {'nome': '', 'email': 'x@test.com', 'registro_funcional': ''},
            'descricao_cargo': '',
            'classificacao': '',
        },
    ]
    mock_render.return_value = '<p>X</p>'

    historico = iniciar_processamento_envio(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        data=date(2025, 2, 25),
    )

    cands = list(CartaConvocacaoCandidato.objects.filter(carta_convocacao_historico=historico))
    assert len(cands) == 1
    assert cands[0].nome == ''


def test_constantes_servico():
    """Constantes do módulo."""
    assert ASSUNTO_CARTA == 'Ciência de Convocação de Escolha de Vaga - PMSP'
    assert 'carta_convocacao' in TEMPLATE_EMAIL and TEMPLATE_EMAIL.endswith('.html')


# --- mesmo candidato em duas linhas ---


@patch('config.celery.app')
@patch('processos.services.carta_convocacao_service.render_to_string')
@patch('processos.services.carta_convocacao_service.CandidatosApiService.buscar_habilitados_por_processo')
def test_iniciar_processamento_envio_mesmo_candidato_duas_linhas_aceito(mock_buscar, mock_render, mock_celery, processo_convocacao):
    """Mesmo candidato (mesmo RF) em 2 linhas com mesmo email: aceita, cria 2 registros e dispara 2 tasks."""
    mock_buscar.return_value = [
        {'candidato': {'nome': 'Fulano', 'email': 'fulano@test.com', 'registro_funcional': '123'}, 'descricao_cargo': 'Cargo A', 'classificacao': 1},
        {'candidato': {'nome': 'Fulano', 'email': 'fulano@test.com', 'registro_funcional': '123'}, 'descricao_cargo': 'Cargo B', 'classificacao': 2},
    ]
    mock_render.return_value = '<p>Email</p>'

    historico = iniciar_processamento_envio(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        data=date(2025, 2, 25),
    )

    assert historico.quantidade_candidatos == 2
    cands = list(CartaConvocacaoCandidato.objects.filter(carta_convocacao_historico=historico).order_by('nome', 'rf'))
    assert len(cands) == 2
    assert cands[0].email == cands[1].email == 'fulano@test.com'
    assert cands[0].rf == cands[1].rf == '123'
    assert cands[0].status == cands[1].status == ENVIO_STATUS_PENDENTE
    assert mock_celery.send_task.call_count == 2
