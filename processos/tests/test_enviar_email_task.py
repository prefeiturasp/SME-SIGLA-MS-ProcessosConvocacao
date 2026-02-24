"""
Testes unitários para processos.tasks.enviar_email_task (sintaxe pytest).
Cobertura 100% do módulo enviar_email_task.py.
"""
import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4

from processos.models import CartaConvocacaoHistorico, CartaConvocacaoCandidato
from processos.models.carta_convocacao_candidato import ENVIO_STATUS_PENDENTE, ENVIO_STATUS_SUCESSO, ENVIO_STATUS_ERRO
from processos.tasks.enviar_email_task import (
    enviar_email_task,
    enviar_email_carta_candidato_task,
    ASSUNTO_CARTA,
    LOGO_EMAIL_PATH,
    CID_LOGO_SIGLA,
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def processo_convocacao(db):
    """Fixture para ProcessoConvocacao (via CartaConvocacaoHistorico)."""
    from processos.models import ProcessoConvocacao
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid4(),
        concurso_nome="Concurso Teste",
        descricao="Descrição",
        tipo_escolha='NOVA_AUTORIZACAO',
        status='EM_ANDAMENTO',
    )


@pytest.fixture
def carta_historico(processo_convocacao):
    """Fixture para CartaConvocacaoHistorico."""
    return CartaConvocacaoHistorico.objects.create(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        data=__import__('datetime').date.today(),
        quantidade_candidatos=1,
    )


@pytest.fixture
def carta_candidato(carta_historico):
    """Fixture para CartaConvocacaoCandidato."""
    return CartaConvocacaoCandidato.objects.create(
        carta_convocacao_historico=carta_historico,
        nome="Fulano",
        rf="1234567",
        email="fulano@test.com",
        status=ENVIO_STATUS_PENDENTE,
        status_detalhe="",
        conteudo="<p>Conteúdo email</p>",
    )


# --- enviar_email_task ---


@patch('processos.tasks.enviar_email_task.enviar_carta_convocacao')
def test_enviar_email_task_chama_servico_e_retorna_resultado(mock_enviar):
    """enviar_email_task delega para enviar_carta_convocacao e retorna o resultado."""
    mock_enviar.return_value = True
    result = enviar_email_task.apply(
        kwargs={
            'email_destino': 'user@test.com',
            'cargo': 'Analista',
            'classificacao': '1º',
            'data_publicacao': '25/02/2025',
        }
    )
    assert result.get() is True
    mock_enviar.assert_called_once_with(
        email_destino='user@test.com',
        cargo='Analista',
        classificacao='1º',
        data_publicacao='25/02/2025',
    )


@patch('processos.tasks.enviar_email_task.enviar_carta_convocacao')
def test_enviar_email_task_retorna_false_se_servico_falhar(mock_enviar):
    """enviar_email_task propaga exceção se enviar_carta_convocacao falhar."""
    mock_enviar.side_effect = Exception('SMTP error')
    with pytest.raises(Exception, match='SMTP error'):
        enviar_email_task.apply(
            kwargs={
                'email_destino': 'user@test.com',
                'cargo': 'Cargo',
                'classificacao': '',
                'data_publicacao': '01/01/2025',
            }
        ).get()
    mock_enviar.assert_called_once()


# --- enviar_email_carta_candidato_task: sucesso com logo ---


@patch('processos.tasks.enviar_email_task.LOGO_EMAIL_PATH')
@patch('processos.tasks.enviar_email_task.EmailMultiAlternatives')
def test_enviar_email_carta_candidato_task_sucesso_com_logo(mock_email_cls, mock_logo_path, carta_candidato):
    """Sucesso: logo existe, email enviado, registro atualizado para SUCESSO."""
    mock_logo_path.is_file.return_value = True
    mock_logo_path.read_bytes.return_value = b'\x89PNG\r\n\x1a\n'
    mock_msg = MagicMock()
    mock_email_cls.return_value = mock_msg

    enviar_email_carta_candidato_task.apply(
        kwargs={
            'email': carta_candidato.email,
            'conteudo': '<p>Olá</p>',
            'carta_convocacao_candidato_id': str(carta_candidato.uuid),
        }
    ).get()

    mock_email_cls.assert_called_once()
    call_kw = mock_email_cls.call_args[1]
    assert call_kw['subject'] == ASSUNTO_CARTA
    assert call_kw['body'] == 'Olá'
    assert call_kw['to'] == [carta_candidato.email]
    assert call_kw['from_email']  # definido por settings
    mock_msg.attach_alternative.assert_called_once_with('<p>Olá</p>', 'text/html')
    mock_msg.attach.assert_called_once()
    mock_msg.send.assert_called_once()

    carta_candidato.refresh_from_db()
    assert carta_candidato.status == ENVIO_STATUS_SUCESSO
    assert carta_candidato.status_detalhe == ''


# --- enviar_email_carta_candidato_task: sucesso sem logo ---


@patch('processos.tasks.enviar_email_task.LOGO_EMAIL_PATH')
@patch('processos.tasks.enviar_email_task.EmailMultiAlternatives')
def test_enviar_email_carta_candidato_task_sucesso_sem_logo(mock_email_cls, mock_logo_path, carta_candidato, caplog):
    """Sucesso: logo não existe, warning logado, email enviado, registro SUCESSO."""
    mock_logo_path.is_file.return_value = False
    mock_msg = MagicMock()
    mock_email_cls.return_value = mock_msg

    enviar_email_carta_candidato_task.apply(
        kwargs={
            'email': carta_candidato.email,
            'conteudo': '<p>Conteúdo</p>',
            'carta_convocacao_candidato_id': str(carta_candidato.uuid),
        }
    ).get()

    mock_msg.attach_alternative.assert_called_once_with('<p>Conteúdo</p>', 'text/html')
    mock_msg.attach.assert_not_called()
    mock_msg.send.assert_called_once()

    carta_candidato.refresh_from_db()
    assert carta_candidato.status == ENVIO_STATUS_SUCESSO
    assert 'Logo do e-mail não encontrada' in caplog.text or any('Logo' in r.message for r in caplog.records)


# --- enviar_email_carta_candidato_task: conteudo vazio ---


@patch('processos.tasks.enviar_email_task.LOGO_EMAIL_PATH')
@patch('processos.tasks.enviar_email_task.EmailMultiAlternatives')
def test_enviar_email_carta_candidato_task_conteudo_vazio(mock_email_cls, mock_logo_path, carta_candidato):
    """Conteúdo vazio: text_plain vazio e attach_alternative com string vazia."""
    mock_logo_path.is_file.return_value = False
    mock_msg = MagicMock()
    mock_email_cls.return_value = mock_msg

    enviar_email_carta_candidato_task.apply(
        kwargs={
            'email': carta_candidato.email,
            'conteudo': '',
            'carta_convocacao_candidato_id': str(carta_candidato.uuid),
        }
    ).get()

    mock_email_cls.assert_called_once()
    call_kwargs = mock_email_cls.call_args[1]
    assert call_kwargs['body'] == ''
    mock_msg.attach_alternative.assert_called_once_with('', 'text/html')
    mock_msg.send.assert_called_once()
    carta_candidato.refresh_from_db()
    assert carta_candidato.status == ENVIO_STATUS_SUCESSO


# --- enviar_email_carta_candidato_task: exceção no send ---


@patch('processos.tasks.enviar_email_task.LOGO_EMAIL_PATH')
@patch('processos.tasks.enviar_email_task.EmailMultiAlternatives')
def test_enviar_email_carta_candidato_task_erro_no_send(mock_email_cls, mock_logo_path, carta_candidato):
    """Exceção no send: status ERRO e status_detalhe preenchido (limitado 2000 chars)."""
    mock_logo_path.is_file.return_value = False
    mock_msg = MagicMock()
    mock_msg.send.side_effect = Exception('Connection refused')
    mock_email_cls.return_value = mock_msg

    enviar_email_carta_candidato_task.apply(
        kwargs={
            'email': carta_candidato.email,
            'conteudo': '<p>Ok</p>',
            'carta_convocacao_candidato_id': str(carta_candidato.uuid),
        }
    ).get()

    carta_candidato.refresh_from_db()
    assert carta_candidato.status == ENVIO_STATUS_ERRO
    assert 'Connection refused' in carta_candidato.status_detalhe
    assert len(carta_candidato.status_detalhe) <= 2000


@patch('processos.tasks.enviar_email_task.LOGO_EMAIL_PATH')
@patch('processos.tasks.enviar_email_task.EmailMultiAlternatives')
def test_enviar_email_carta_candidato_task_erro_status_detalhe_limitado(mock_email_cls, mock_logo_path, carta_candidato):
    """status_detalhe é truncado a 2000 caracteres."""
    mock_logo_path.is_file.return_value = False
    mock_msg = MagicMock()
    long_error = 'x' * 3000
    mock_msg.send.side_effect = Exception(long_error)
    mock_email_cls.return_value = mock_msg

    enviar_email_carta_candidato_task.apply(
        kwargs={
            'email': carta_candidato.email,
            'conteudo': '<p>Ok</p>',
            'carta_convocacao_candidato_id': str(carta_candidato.uuid),
        }
    ).get()

    carta_candidato.refresh_from_db()
    assert carta_candidato.status == ENVIO_STATUS_ERRO
    assert len(carta_candidato.status_detalhe) == 2000


# --- enviar_email_carta_candidato_task: CartaConvocacaoCandidato.DoesNotExist ---


@patch('processos.tasks.enviar_email_task.LOGO_EMAIL_PATH')
@patch('processos.tasks.enviar_email_task.EmailMultiAlternatives')
def test_enviar_email_carta_candidato_task_registro_nao_encontrado(mock_email_cls, mock_logo_path, carta_candidato, caplog):
    """Se o registro CartaConvocacaoCandidato não existir, loga warning e não quebra."""
    mock_logo_path.is_file.return_value = False
    mock_msg = MagicMock()
    mock_email_cls.return_value = mock_msg

    uuid_inexistente = uuid4()
    # Garantir que não existe no banco
    assert not CartaConvocacaoCandidato.objects.filter(uuid=uuid_inexistente).exists()

    enviar_email_carta_candidato_task.apply(
        kwargs={
            'email': 'outro@test.com',
            'conteudo': '<p>Ok</p>',
            'carta_convocacao_candidato_id': str(uuid_inexistente),
        }
    ).get()

    mock_msg.send.assert_called_once()
    assert 'não encontrado para atualizar status' in caplog.text or any(
        'não encontrado' in getattr(r, 'message', str(r)) for r in caplog.records
    )


# --- constantes e logo (branches de anexo) ---


def test_constantes_task():
    """Constantes do módulo estão definidas."""
    assert ASSUNTO_CARTA == 'Ciência de Convocação de Escolha de Vaga - PMSP'
    assert CID_LOGO_SIGLA == 'logo_sigla'
    assert 'templates' in str(LOGO_EMAIL_PATH) and 'assets' in str(LOGO_EMAIL_PATH)


@patch('processos.tasks.enviar_email_task.LOGO_EMAIL_PATH')
@patch('processos.tasks.enviar_email_task.MIMEImage')
@patch('processos.tasks.enviar_email_task.EmailMultiAlternatives')
def test_enviar_email_carta_candidato_task_anexa_mime_com_cid_correto(mock_email_cls, mock_mime_cls, mock_logo_path, carta_candidato):
    """Com logo: MIMEImage criado e anexado com Content-ID e Content-Disposition corretos."""
    mock_logo_path.is_file.return_value = True
    mock_logo_path.read_bytes.return_value = b'\x89PNG\r\n\x1a\n'
    mock_mime = MagicMock()
    mock_mime_cls.return_value = mock_mime
    mock_msg = MagicMock()
    mock_email_cls.return_value = mock_msg

    enviar_email_carta_candidato_task.apply(
        kwargs={
            'email': carta_candidato.email,
            'conteudo': '<p>X</p>',
            'carta_convocacao_candidato_id': str(carta_candidato.uuid),
        }
    ).get()

    mock_mime_cls.assert_called_once_with(b'\x89PNG\r\n\x1a\n', _subtype='png')
    mock_mime.add_header.assert_any_call('Content-Disposition', 'inline', filename='logo_sigla.png')
    mock_mime.add_header.assert_any_call('Content-ID', f'<{CID_LOGO_SIGLA}>')
    mock_msg.attach.assert_called_once_with(mock_mime)
