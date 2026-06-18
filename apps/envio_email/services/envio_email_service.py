"""Serviço genérico de envio de e-mails por processo."""

from __future__ import annotations

import logging
import re
from re import Match
from typing import Any
from uuid import UUID

from django.template.loader import render_to_string
from sigla_sdk.context import get_correlation_id

from envio_email.models import (
    EnvioEmail,
    EnvioEmailCandidato,
    EnvioEmailConteudo,
)
from envio_email.models.envio_email import (
    ASSUNTO_POR_TIPO,
    TIPO_CONVOCACAO,
    TIPO_RESULTADOS,
    TIPO_VAGAS,
)
from envio_email.models.envio_email_candidato import ENVIO_STATUS_PENDENTE
from processos.services.candidatos_api_url import CandidatosApiService

logger = logging.getLogger(__name__)

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
        Dicionário com os dados processados.

    Raises:
        Nenhuma exceção específica documentada.
    """
    cargo_nome = candidato.get("descricao_cargo") or "—"
    categoria = (candidato.get("categoria_efetiva") or "").strip().upper()
    if categoria == "PCD" and candidato.get("classificacao_pcd") is not None:
        classificacao = str(candidato.get("classificacao_pcd"))
    elif categoria == "NNA" and candidato.get("classificacao_nna") is not None:
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
        Texto resultante da operação.

    Raises:
        Nenhuma exceção específica documentada.
    """
    padrao = re.compile(r"\[\[(.*?)\]\]")

    def substituir_placeholder(match: Match[str]) -> str:
        chave = match.group(1)
        return str(dados.get(chave, f"[[ERRO: {chave} NÃO ENCONTRADO]]"))

    return padrao.sub(substituir_placeholder, conteudo or "")


def _obter_template_conteudo(tipo: str) -> EnvioEmailConteudo | None:
    """Retorna o template persistido para o tipo de envio, se existir."""
    try:
        return EnvioEmailConteudo.objects.get(tipo=tipo)
    except EnvioEmailConteudo.DoesNotExist:
        return None


def _resolver_conteudo_envio(tipo: str, conteudo: str | None) -> str:
    """Usa o conteúdo informado ou faz fallback para conteúdo salvo/gabarito."""
    if conteudo and conteudo.strip():
        return conteudo
    template = _obter_template_conteudo(tipo)
    if not template:
        return ""
    if template.conteudo and template.conteudo.strip():
        return template.conteudo
    return template.conteudo_gabarito or ""


def _resolver_assunto_envio(tipo: str, assunto: str | None) -> str:
    """Usa o assunto informado ou o padrão fixo do tipo no envio."""
    if assunto and assunto.strip():
        return assunto.strip()
    return ASSUNTO_POR_TIPO.get(tipo, ASSUNTO_POR_TIPO[TIPO_CONVOCACAO])


def _renderizar_conteudo(*, tipo: str, contexto: dict[str, Any]) -> str:
    """Renderiza corpo do e-mail no template dinâmico."""
    return render_to_string(TEMPLATE_DINAMICO, contexto)


def iniciar_processamento_envio(
    *,
    processo_uuid: UUID | str,
    processo_nome: str,
    tipo: str,
    conteudo: str | None,
    assunto: str | None = None,
) -> EnvioEmail:
    """Inicia envio assíncrono de e-mails para habilitados convocados.

    Args:
        processo_uuid: UUID do processo de convocação.
        processo_nome: nome exibido no histórico de envio.
        tipo: ``CONVOCACAO``, ``VAGAS`` ou ``RESULTADOS``.
        conteudo: HTML com placeholders ``[[cargo]]``, etc.
        assunto: Assunto do e-mail; se vazio, usa template salvo ou padrão.

    Returns:
        Resultado da operação.

    Raises:
        Nenhuma exceção específica documentada.
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
    assunto = _resolver_assunto_envio(tipo, assunto)
    habilitados = CandidatosApiService().buscar_habilitados_por_processo(
        processo_uuid_str
    )
    quantidade = len(habilitados)
    conteudo = _resolver_conteudo_envio(tipo, conteudo)

    envio = EnvioEmail.objects.create(
        processo_uuid=processo_uuid,
        processo_nome=processo_nome,
        tipo=tipo,
        quantidade_candidatos=quantidade,
    )

    ignorados_sem_email = 0
    for habilitado in habilitados:
        dados_candidato = habilitado.get("candidato") or {}
        nome = dados_candidato.get("nome") or ""
        rf = str(dados_candidato.get("registro_funcional") or "")
        email = dados_candidato.get("email") or ""

        if not email:
            ignorados_sem_email += 1
            continue

        conteudo_preenchido = _preencher_template(
            conteudo, dados_template(habilitado)
        )
        contexto = {
            "email_body": conteudo_preenchido,
            "email_title": TITULO_POR_TIPO.get(
                tipo, TITULO_POR_TIPO[TIPO_CONVOCACAO]
            ),
        }

        conteudo_html = render_to_string(TEMPLATE_DINAMICO, contexto)
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
            "envio_email.tasks.enviar_email_task.enviar_email_candidato_task",
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
