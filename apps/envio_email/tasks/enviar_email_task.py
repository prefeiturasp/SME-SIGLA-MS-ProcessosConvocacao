"""Task Celery para envio de e-mail a candidatos."""

import logging
from pathlib import Path
from uuid import UUID

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

from config.celery import app
from envio_email.models.envio_email_candidato import (
    ENVIO_STATUS_ERRO,
    ENVIO_STATUS_SUCESSO,
)
from envio_email.repository import EnvioEmailCandidatoRepository
from envio_email.utils.email_inline_images import (
    converter_imagens_base64_para_cid,
)

logger = logging.getLogger(__name__)

CAMINHO_LOGO_EMAIL = (
    Path(settings.BASE_DIR)
    / "templates"
    / "assets"
    / "logo_PrefSP_sem fundo_horizontal_fundo claro (1).png"
)
CID_LOGO_SIGLA = "logo_sigla"


@app.task
def enviar_email_candidato_task(
    *,
    email: str,
    assunto: str,
    conteudo: str,
    envio_email_candidato_id: str,
    correlation_id: str,
) -> None:
    """Envia o e-mail e atualiza o status do EnvioEmailCandidato."""
    candidato_uuid = UUID(envio_email_candidato_id)
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@localhost")
    texto_plano = strip_tags(conteudo) if conteudo else ""

    logger.info(
        "Enviando e-mail",
        extra={
            "email": email,
            "candidato_uuid": str(candidato_uuid),
            "correlation_id": correlation_id,
        },
    )
    if "example.com" not in email:
        try:
            conteudo_html, imagens_inline = converter_imagens_base64_para_cid(
                conteudo or "",
            )
            mensagem = EmailMultiAlternatives(
                subject=assunto,
                body=texto_plano,
                from_email=from_email,
                to=[email],
            )
            if imagens_inline:
                mensagem.mixed_subtype = "related"
            mensagem.attach_alternative(conteudo_html, "text/html")
            for imagem_mime in imagens_inline:
                mensagem.attach(imagem_mime)
            mensagem.send()
            logger.info(
                "E-mail enviado para %s (candidato_id=%s)",
                email,
                candidato_uuid,
            )
            status_envio = ENVIO_STATUS_SUCESSO
            status_detalhe = ""
        except Exception as exc:
            logger.exception(
                "Erro ao enviar e-mail para %s (candidato_id=%s): %s",
                email,
                candidato_uuid,
                exc,
            )
            status_envio = ENVIO_STATUS_ERRO
            status_detalhe = str(exc)[:2000]
    else:
        status_detalhe = "Email example.com não enviado"
        status_envio = ENVIO_STATUS_SUCESSO

    if not EnvioEmailCandidatoRepository.atualizar_status(
        candidato_uuid,
        status=status_envio,
        status_detalhe=status_detalhe,
    ):
        logger.warning(
            "EnvioEmailCandidato uuid=%s não encontrado para atualizar status",
            candidato_uuid,
        )
