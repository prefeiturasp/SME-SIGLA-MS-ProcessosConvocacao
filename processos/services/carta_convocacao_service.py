"""
Serviço de envio da carta de convocação por email.
"""
import logging
from datetime import date
from uuid import UUID

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from processos.models import CartaConvocacaoCandidato, CartaConvocacaoHistorico
from processos.models.carta_convocacao_candidato import ENVIO_STATUS_PENDENTE
from processos.services.candidatos_api_url import CandidatosApiService
from sigla_sdk.context import get_correlation_id


logger = logging.getLogger(__name__)

ASSUNTO_CARTA = 'Ciência de Convocação de Escolha de Vaga - PMSP'
TEMPLATE_EMAIL = 'email/carta_convocacao.html'


def enviar_carta_convocacao(
    *,
    email_destino: str,
    cargo: str,
    classificacao: str = '',
    data_publicacao: str,
) -> bool:
    """
    Envia a carta de convocação por email usando o template HTML.

    Args:
        email_destino: Email do destinatário.
        cargo: Nome do cargo do processo.
        classificacao: Classificação do candidato (ex.: 1º, 2º).
        data_publicacao: Data da publicação no DOC (ex.: 25/02/2025).

    Returns:
        True se o envio foi disparado com sucesso.
    """
    context = {
        'cargo': cargo or '—',
        'classificacao': classificacao or '—',
        'data_publicacao': data_publicacao or '—',
        'ms_url': getattr(settings, 'MS_URL', ''),
    }
    html_content = render_to_string(TEMPLATE_EMAIL, context)
    text_plain = (
        f'Cargo: {context["cargo"]} - CLASS: {context["classificacao"]}\n\n'
        f'Consulte o Diário Oficial da Cidade de São Paulo do dia {context["data_publicacao"]}.'
    )
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@localhost')

    try:
        msg = EmailMultiAlternatives(
            subject=ASSUNTO_CARTA,
            body=text_plain,
            from_email=from_email,
            to=[email_destino],
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send()
        logger.info('Carta de convocação enviada para %s', email_destino)
        return True
    except Exception as exc:
        logger.exception('Erro ao enviar carta de convocação para %s: %s', email_destino, exc)
        raise


def iniciar_processamento_envio(
    *,
    processo_uuid: UUID | str,
    processo_nome: str,
    data: date,
) -> CartaConvocacaoHistorico:
    """
    Inicia o processamento do envio da carta de convocação: busca habilitados,
    cria histórico, para cada candidato cria registro e dispara a task de envio.

    1. Busca habilitados pelo processo_uuid (MS-Candidatos).
    2. Cria registro em CartaConvocacaoHistorico.
    3. Para cada candidato: renderiza template, cria CartaConvocacaoCandidato,
       chama enviar_email_carta_candidato_task.

    Args:
        processo_uuid: UUID do processo de convocação.
        processo_nome: Nome do processo.
        data: Data da publicação/convocacao.

    Returns:
        O registro CartaConvocacaoHistorico criado.
    """
    logger.info(
        'Iniciando processamento de envio da carta de convocação',
        extra={
            "processo_uuid": processo_uuid,
            "processo_nome": processo_nome,
            "data": data,
            "correlation_id": get_correlation_id(),
        }
    )
    processo_uuid_str = str(processo_uuid)
    data_publicacao_str = data.strftime('%d/%m/%Y') if hasattr(data, 'strftime') else str(data)

    # 1.1 Buscar habilitados pelo processo_uuid
    habilitados = CandidatosApiService().buscar_habilitados_por_processo(processo_uuid_str)
    quantidade = len(habilitados)

    # 1.2 Criar registro no CartaConvocacaoHistorico
    historico = CartaConvocacaoHistorico.objects.create(
        processo_uuid=processo_uuid,
        processo_nome=processo_nome,
        data=data,
        quantidade_candidatos=quantidade,
    )
    # 1.3 Iterar em cada candidato
    # API MS-Candidatos: candidato (objeto aninhado); descricao_cargo = cargo importado; classificacao/classificacao_pcd/classificacao_nna
    ignorados_sem_email = 0
    for item in habilitados:
        cand = item.get('candidato')
        nome = (cand.get('nome'))
        rf = str(cand.get('registro_funcional'))
        email = (cand.get('email'))
        cargo_nome = (item.get('descricao_cargo'))
        cat = (item.get('categoria_efetiva') or '').strip().upper()
        if cat == 'PCD' and item.get('classificacao_pcd') is not None:
            classificacao = str(item.get('classificacao_pcd'))
        elif cat == 'NNA' and item.get('classificacao_nna') is not None:
            classificacao = str(item.get('classificacao_nna'))
        else:
            classificacao = str(item.get('classificacao') or '').strip() or '—'

        if not email:
            ignorados_sem_email += 1
            continue

        context = {
            'cargo': cargo_nome,
            'classificacao': classificacao,
            'data_publicacao': data_publicacao_str,
            'ms_url': getattr(settings, 'MS_URL', ''),
        }
        conteudo_html = render_to_string(TEMPLATE_EMAIL, context)

        registro = CartaConvocacaoCandidato.objects.create(
            carta_convocacao_historico=historico,
            nome=nome,
            rf=rf,
            email=email,
            status=ENVIO_STATUS_PENDENTE,
            status_detalhe='',
            conteudo=conteudo_html,
        )

        logger.info(
        'Adicionando candidato na fila',
        extra={
            "historico_uuid": historico.uuid,
            "processo_uuid": processo_uuid_str,
            "processo_nome": processo_nome,
            "correlation_id": get_correlation_id(),
            "nome": nome,
            "rf": rf,
            "email": email,
            "cargo_nome": cargo_nome,
            "classificacao": classificacao,
            "data_publicacao": data_publicacao_str,
        }
    )
        # Envia a task pelo app do config para garantir o mesmo broker (KeyDB/Redis) que o worker
        from config.celery import app as celery_app
        celery_app.send_task(
            'processos.tasks.enviar_email_task.enviar_email_carta_candidato_task',
            kwargs={
                'email': email,
                'conteudo': conteudo_html,
                'carta_convocacao_candidato_id': str(registro.uuid),
                'correlation_id': get_correlation_id(),
            },
        )

    if ignorados_sem_email:
        logger.warning(
            'Habilitados ignorados por falta de e-mail: %s de %s',
            ignorados_sem_email,
            quantidade,
        )

    return historico
