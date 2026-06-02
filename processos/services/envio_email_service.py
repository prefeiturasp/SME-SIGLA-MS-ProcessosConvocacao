"""Serviço genérico de envio de e-mails por processo."""

from __future__ import annotations

import logging
import re
from re import Match
from typing import Any
from uuid import UUID

from django.template.loader import render_to_string
from sigla_sdk.context import get_correlation_id

from processos.models import (
    EnvioEmail,
    EnvioEmailCandidato,
)
from processos.models.envio_email import (
    TIPO_CONVOCACAO,
    TIPO_RESULTADOS,
    TIPO_VAGAS,
)
from processos.models.envio_email_candidato import ENVIO_STATUS_PENDENTE
from processos.services.candidatos_api_url import CandidatosApiService

logger = logging.getLogger(__name__)

ASSUNTO_POR_TIPO = {
    TIPO_CONVOCACAO: "Ciência de Convocação de Escolha de Vaga - PMSP",
    TIPO_VAGAS: "Comunicado de Vagas - PMSP",
    TIPO_RESULTADOS: "Comunicado de Resultados - PMSP",
}

TITULO_POR_TIPO = {
    TIPO_CONVOCACAO: "Ciência de Convocação de Escolha de Vaga - PMSP",
    TIPO_VAGAS: "Comunicado de Vagas - PMSP",
    TIPO_RESULTADOS: "Comunicado de Resultados - PMSP",
}

TEMPLATE_POR_TIPO = {
    TIPO_CONVOCACAO: "email/email_convocacao_padrao.html",
    TIPO_VAGAS: "email/email_vagas_padrao.html",
    TIPO_RESULTADOS: "email/email_resultados_padrao.html",
}

TEMPLATE_DINAMICO = "email/envio_email_dinamico.html"


def dados_template(candidato: dict[str, Any]) -> dict[str, str]:
    """Extrai placeholders de cargo e classificação do habilitado.

    Args:
        candidato: item retornado pelo MS-Candidatos.

    Returns:
        Dict com chaves ``cargo`` e ``classificacao`` para o template.
    """
    cargo_nome = candidato.get("descricao_cargo") or "—"
    cat = (candidato.get("categoria_efetiva") or "").strip().upper()
    if cat == "PCD" and candidato.get("classificacao_pcd") is not None:
        classificacao = str(candidato.get("classificacao_pcd"))
    elif cat == "NNA" and candidato.get("classificacao_nna") is not None:
        classificacao = str(candidato.get("classificacao_nna"))
    else:
        classificacao = (
            str(candidato.get("classificacao") or "").strip() or "—"
        )
    return {
        "cargo": cargo_nome,
        "classificacao": classificacao,
    }


def _preencher_template(
    conteudo: str | None,
    dados: dict[str, str],
) -> str:
    """Substitui placeholders ``[[chave]]`` no HTML pelo dict ``dados``.

    Args:
        conteudo: HTML do template; ``None`` é tratado como string vazia.
        dados: mapa chave → valor para substituição.

    Returns:
        HTML com placeholders preenchidos.
    """
    pattern = re.compile(r"\[\[(.*?)\]\]")

    def replace_func(match: Match[str]) -> str:
        chave = match.group(1)
        return str(dados.get(chave, f"[[ERRO: {chave} NÃO ENCONTRADO]]"))

    return pattern.sub(replace_func, conteudo or "")


def _renderizar_conteudo(*, tipo: str, context: dict[str, Any]) -> str:
    """Renderiza corpo do e-mail no template dinâmico."""
    return render_to_string(TEMPLATE_DINAMICO, context)


def iniciar_processamento_envio(
    *,
    processo_uuid: UUID | str,
    processo_nome: str,
    tipo: str,
    conteudo: str | None,
) -> EnvioEmail:
    """Inicia envio assíncrono de e-mails para habilitados convocados.

    Args:
        processo_uuid: UUID do processo de convocação.
        processo_nome: nome exibido no histórico de envio.
        tipo: ``CONVOCACAO``, ``VAGAS`` ou ``RESULTADOS``.
        conteudo: HTML com placeholders ``[[cargo]]``, etc.

    Returns:
        Registro ``EnvioEmail`` com candidatos enfileirados no Celery.
    """
    logger.info(
        "Iniciando processamento de envio de e-mail",
        extra={
            "processo_uuid": str(processo_uuid),
            "processo_nome": processo_nome,
            "tipo": tipo,
            "correlation_id": get_correlation_id(),
        },
    )
    processo_uuid_str = str(processo_uuid)
    assunto = ASSUNTO_POR_TIPO.get(tipo, ASSUNTO_POR_TIPO[TIPO_CONVOCACAO])
    habilitados = CandidatosApiService().buscar_habilitados_por_processo(
        processo_uuid_str
    )
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
        cand = item.get("candidato") or {}
        nome = cand.get("nome") or ""
        rf = str(cand.get("registro_funcional") or "")
        email = cand.get("email") or ""

        if not email:
            ignorados_sem_email += 1
            continue

        conteudo_preenchido = _preencher_template(
            conteudo, dados_template(item))
        context = {
            "email_body": conteudo_preenchido,
            "email_title": TITULO_POR_TIPO.get(
                tipo, TITULO_POR_TIPO[TIPO_CONVOCACAO]
            ),
        }

        conteudo_html = render_to_string(TEMPLATE_DINAMICO, context)
        registro = EnvioEmailCandidato.objects.create(
            envio_email=envio,
            nome=nome,
            rf=rf,
            email=email,
            status=ENVIO_STATUS_PENDENTE,
            status_detalhe="",
            conteudo=conteudo_html,
        )

        logger.info(
            "Adicionando candidato na fila",
            extra={
                "envio_email_uuid": str(envio.uuid),
                "processo_uuid": processo_uuid_str,
                "processo_nome": processo_nome,
                "correlation_id": get_correlation_id(),
                "nome": nome,
                "rf": rf,
                "email": email,
            },
        )

        from config.celery import app as celery_app

        celery_app.send_task(
            "processos.tasks.enviar_email_task.enviar_email_candidato_task",
            kwargs={
                "email": email,
                "assunto": assunto,
                "conteudo": conteudo_html,
                "envio_email_candidato_id": str(registro.uuid),
                "correlation_id": get_correlation_id(),
            },
        )

    if ignorados_sem_email:
        logger.warning(
            "Candidatos ignorados por falta de e-mail: %s de %s",
            ignorados_sem_email,
            quantidade,
        )

    return envio
