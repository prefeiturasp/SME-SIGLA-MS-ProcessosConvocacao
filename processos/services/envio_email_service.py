"""
Serviço genérico de envio de e-mails por processo (convocação, vagas, resultado).
"""
import logging
import re
from uuid import UUID

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template import Context, Template
from django.template.loader import render_to_string

from processos.models import EnvioEmail, EnvioEmailCandidato, EnvioEmailConteudo
from processos.models.envio_email import TIPO_CONVOCACAO, TIPO_RESULTADOS, TIPO_VAGAS
from processos.models.envio_email_candidato import ENVIO_STATUS_PENDENTE
from processos.services.candidatos_api_url import CandidatosApiService
from sigla_sdk.context import get_correlation_id

logger = logging.getLogger(__name__)

ASSUNTO_POR_TIPO = {
    TIPO_CONVOCACAO: 'Ciência de Convocação de Escolha de Vaga - PMSP',
    TIPO_VAGAS: 'Comunicado de Vagas - PMSP',
    TIPO_RESULTADOS: 'Comunicado de Resultados - PMSP',
}

TITULO_POR_TIPO = {
    TIPO_CONVOCACAO: 'Ciência de Convocação de Escolha de Vaga - PMSP',
    TIPO_VAGAS: 'Comunicado de Vagas - PMSP',
    TIPO_RESULTADOS: 'Comunicado de Resultados - PMSP',
}

TEMPLATE_POR_TIPO = {
    TIPO_CONVOCACAO: 'email/email_convocacao_padrao.html',
    TIPO_VAGAS: 'email/email_vagas_padrao.html',
    TIPO_RESULTADOS: 'email/email_resultados_padrao.html',
}

TEMPLATE_DINAMICO = 'email/envio_email_dinamico.html'

def _montar_contexto_convocacao(*, item: dict, data_publicacao_str: str) -> dict:
    cand = item.get('candidato') or {}
    cargo_nome = item.get('descricao_cargo') or '—'
    cat = (item.get('categoria_efetiva') or '').strip().upper()
    if cat == 'PCD' and item.get('classificacao_pcd') is not None:
        classificacao = str(item.get('classificacao_pcd'))
    elif cat == 'NNA' and item.get('classificacao_nna') is not None:
        classificacao = str(item.get('classificacao_nna'))
    else:
        classificacao = str(item.get('classificacao') or '').strip() or '—'
    return {
        'cargo': cargo_nome,
        'classificacao': classificacao,
        'data_publicacao': data_publicacao_str,
        'ms_url': getattr(settings, 'MS_URL', ''),
    }

def _preencher_template(conteudo, dados):
    # Regex para encontrar qualquer coisa entre [[ ]]
    pattern = re.compile(r'\[\[(.*?)\]\]')

    def replace_func(match):
        chave = match.group(1) # Pega o que está dentro de [[ ]]
        return str(dados.get(chave, f"[[ERRO: {chave} NÃO ENCONTRADO]]"))

    # `re.sub` exige string; templates vazios podem vir como None
    print(conteudo)
    return pattern.sub(replace_func, conteudo or "")

def _renderizar_conteudo(*, tipo: str, context: dict) -> str:
    return render_to_string(TEMPLATE_DINAMICO, context)


def iniciar_processamento_envio(
    *,
    processo_uuid: UUID | str,
    processo_nome: str,
    tipo: str,
    conteudo: str
) -> EnvioEmail:
    """
    Inicia o processamento de envio de e-mails para habilitados do processo.

    ``conteudo`` é o conteúdo HTML do e-mail.
    """
    logger.info(
        'Iniciando processamento de envio de e-mail',
        extra={
            'processo_uuid': str(processo_uuid),
            'processo_nome': processo_nome,
            'tipo': tipo,
            'correlation_id': get_correlation_id(),
        },
    )
    processo_uuid_str = str(processo_uuid)
    assunto = ASSUNTO_POR_TIPO.get(tipo, ASSUNTO_POR_TIPO[TIPO_CONVOCACAO])
    habilitados = CandidatosApiService().buscar_habilitados_por_processo(processo_uuid_str)
    quantidade = len(habilitados)
    conteudo = conteudo or ""

    envio = EnvioEmail.objects.create(
        processo_uuid=processo_uuid,
        processo_nome=processo_nome,
        tipo=tipo,
        quantidade_candidatos=quantidade,
    )

    ignorados_sem_email = 0
    for item in habilitados:
        cand = item.get('candidato') or {}
        nome = cand.get('nome') or ''
        rf = str(cand.get('registro_funcional') or '')
        email = cand.get('email') or ''

        if not email:
            ignorados_sem_email += 1
            continue

        dados_template = {
            'cargo': item.get('descricao_cargo') or '—',
            'classificacao': item.get('classificacao') or '—',
        }
        conteudo_preenchido = _preencher_template(conteudo, dados_template)
        context = {
            "email_body": conteudo_preenchido,
            "email_title": TITULO_POR_TIPO.get(tipo, TITULO_POR_TIPO[TIPO_CONVOCACAO]),
        }

        conteudo_html = render_to_string(TEMPLATE_DINAMICO, context)
        registro = EnvioEmailCandidato.objects.create(
            envio_email=envio,
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
                'envio_email_uuid': str(envio.uuid),
                'processo_uuid': processo_uuid_str,
                'processo_nome': processo_nome,
                'correlation_id': get_correlation_id(),
                'nome': nome,
                'rf': rf,
                'email': email,
            },
        )

        from config.celery import app as celery_app

        celery_app.send_task(
            'processos.tasks.enviar_email_task.enviar_email_candidato_task',
            kwargs={
                'email': email,
                'assunto': assunto,
                'conteudo': conteudo_html,
                'envio_email_candidato_id': str(registro.uuid),
                'correlation_id': get_correlation_id(),
            },
        )

    if ignorados_sem_email:
        logger.warning(
            'Candidatos ignorados por falta de e-mail: %s de %s',
            ignorados_sem_email,
            quantidade,
        )

    return envio
