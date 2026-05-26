import logging
from pathlib import Path
from uuid import UUID

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from email.mime.image import MIMEImage

from config.celery import app
from processos.utils.email_inline_images import converter_imagens_base64_para_cid
from processos.models.envio_email_candidato import (
    EnvioEmailCandidato,
    ENVIO_STATUS_ERRO,
    ENVIO_STATUS_SUCESSO,
)

logger = logging.getLogger(__name__)

LOGO_EMAIL_PATH = Path(settings.BASE_DIR) / 'templates' / 'assets' / 'logo_PrefSP_sem fundo_horizontal_fundo claro (1).png'
CID_LOGO_SIGLA = 'logo_sigla'


@app.task
def enviar_email_candidato_task(
    *,
    email: str,
    assunto: str,
    conteudo: str,
    envio_email_candidato_id: str,
    correlation_id: str,
) -> None:
    """
    Envia o e-mail com o conteúdo informado e atualiza EnvioEmailCandidato.
    """
    candidato_uuid = UUID(envio_email_candidato_id)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@localhost')
    text_plain = strip_tags(conteudo) if conteudo else ''

    logger.info(
        'Enviando e-mail',
        extra={
            'email': email,
            'candidato_uuid': str(candidato_uuid),
            'correlation_id': correlation_id,
        },
    )
    if 'example.com' not in email:
        try:
            conteudo_html, imagens_inline = converter_imagens_base64_para_cid(
                conteudo or '',
            )
            msg = EmailMultiAlternatives(
                subject=assunto,
                body=text_plain,
                from_email=from_email,
                to=[email],
            )
            if imagens_inline:
                msg.mixed_subtype = 'related'
            msg.attach_alternative(conteudo_html, 'text/html')
            for mime_img in imagens_inline:
                msg.attach(mime_img)
            msg.send()
            logger.info(
                'E-mail enviado para %s (candidato_id=%s)',
                email,
                candidato_uuid,
            )
            status = ENVIO_STATUS_SUCESSO
            status_detalhe = ''
        except Exception as exc:
            logger.exception(
                'Erro ao enviar e-mail para %s (candidato_id=%s): %s',
                email,
                candidato_uuid,
                exc,
            )
            status = ENVIO_STATUS_ERRO
            status_detalhe = str(exc)[:2000]
    else:
        status_detalhe = 'Email example.com não enviado'
        status = ENVIO_STATUS_SUCESSO

    try:
        registro = EnvioEmailCandidato.objects.get(uuid=candidato_uuid)
        registro.status = status
        registro.status_detalhe = status_detalhe
        registro.save(update_fields=['status', 'status_detalhe', 'atualizado_em'])
    except EnvioEmailCandidato.DoesNotExist:
        logger.warning(
            'EnvioEmailCandidato uuid=%s não encontrado para atualizar status',
            candidato_uuid,
        )
