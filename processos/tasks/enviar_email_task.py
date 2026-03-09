import logging
from pathlib import Path
from uuid import UUID

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from email.mime.image import MIMEImage

from config.celery import app
from processos.models.carta_convocacao_candidato import (
    CartaConvocacaoCandidato,
    ENVIO_STATUS_ERRO,
    ENVIO_STATUS_SUCESSO,
)

logger = logging.getLogger(__name__)

# Assunto do e-mail da carta de convocação (exibido na caixa de entrada)
ASSUNTO_CARTA = 'Ciência de Convocação de Escolha de Vaga - PMSP'
# Logo do topo do e-mail (anexada como inline com cid:logo_sigla)
LOGO_EMAIL_PATH = Path(settings.BASE_DIR) / 'templates' / 'assets' / 'logo_PrefSP_sem fundo_horizontal_fundo claro (1).png'
CID_LOGO_SIGLA = 'logo_sigla'

@app.task
def enviar_email_carta_candidato_task(
    *,
    email: str,
    conteudo: str,
    carta_convocacao_candidato_id: str,
) -> None:
    """
    Envia o email com o conteúdo informado (configs do settings).
    Após o envio, atualiza o registro CartaConvocacaoCandidato: status (SUCESSO/ERRO)
    e, em caso de erro, status_detalhe.

    Args:
        email: Email do destinatário.
        conteudo: Conteúdo do email (HTML).
        carta_convocacao_candidato_id: UUID do registro CartaConvocacaoCandidato.
    """
    candidato_uuid = UUID(carta_convocacao_candidato_id)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@localhost')
    text_plain = strip_tags(conteudo) if conteudo else ''

    try:
        msg = EmailMultiAlternatives(
            subject=ASSUNTO_CARTA,
            body=text_plain,
            from_email=from_email,
            to=[email],
        )
        msg.attach_alternative(conteudo or '', 'text/html')
        if LOGO_EMAIL_PATH.is_file():
            mime_img = MIMEImage(LOGO_EMAIL_PATH.read_bytes(), _subtype='png')
            mime_img.add_header('Content-Disposition', 'inline', filename='logo_sigla.png')
            mime_img.add_header('Content-ID', f'<{CID_LOGO_SIGLA}>')
            msg.attach(mime_img)
        else:
            logger.warning('Logo do e-mail não encontrada: %s', LOGO_EMAIL_PATH)
        msg.send()
        logger.info('Email carta convocação enviado para %s (candidato_id=%s)', email, candidato_uuid)
        status = ENVIO_STATUS_SUCESSO
        status_detalhe = ''
    except Exception as exc:
        logger.exception(
            'Erro ao enviar email carta convocação para %s (candidato_id=%s): %s',
            email,
            candidato_uuid,
            exc,
        )
        status = ENVIO_STATUS_ERRO
        status_detalhe = str(exc)[:2000]  # limita tamanho

    try:
        registro = CartaConvocacaoCandidato.objects.get(uuid=candidato_uuid)
        registro.status = status
        registro.status_detalhe = status_detalhe
        registro.save(update_fields=['status', 'status_detalhe', 'atualizado_em'])
    except CartaConvocacaoCandidato.DoesNotExist:
        logger.warning('CartaConvocacaoCandidato uuid=%s não encontrado para atualizar status', candidato_uuid)
