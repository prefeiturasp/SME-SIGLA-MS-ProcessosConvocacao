"""Módulo signals."""

from __future__ import annotations

import logging
from typing import Any

from django.db.models.signals import post_save
from django.dispatch import receiver
from sigla_sdk.context import get_correlation_id

from processos.constants import CONCURSO_SITUACAO_EM_ANDAMENTO
from processos.models import ProcessoConvocacao
from processos.services import ConcursosApiService
from processos.services.exceptions import ConcursoServiceError

logger = logging.getLogger(__name__)


@receiver(post_save, sender=ProcessoConvocacao)
def processo_convocacao_post_save(
    sender: Any, instance: ProcessoConvocacao, created: bool, **kwargs: Any
) -> None:
    """Sinaliza EM_ANDAMENTO ao MS-Concursos quando o processo é criado."""
    if not created:
        return
    try:
        ConcursosApiService().atualizar_situacao(
            concurso_uuid=str(instance.concurso_uuid),
            situacao=CONCURSO_SITUACAO_EM_ANDAMENTO,
        )
    except ConcursoServiceError:
        logger.exception(
            "Falha ao atualizar situação do concurso para EM_ANDAMENTO",
            extra={
                "concurso_uuid": str(instance.concurso_uuid),
                "processo_uuid": str(instance.uuid),
                "correlation_id": get_correlation_id(),
            },
        )
