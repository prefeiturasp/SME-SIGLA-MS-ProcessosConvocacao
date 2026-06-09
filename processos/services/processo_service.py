"""Regras de negócio do ProcessoConvocacao."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sigla_sdk.context import get_correlation_id

if TYPE_CHECKING:
    from processos.models import ProcessoConvocacao

from processos.services.agenda_api_service import AgendaApiService
from processos.services.candidatos_api_url import CandidatosApiService
from processos.services.escolhas_service import EscolhasApiService
from processos.services.exceptions import (
    AgendaServiceError,
    CandidatosServiceError,
    EscolhasServiceError,
    ProcessoServiceError,
)

logger = logging.getLogger(__name__)


class ProcessoConvocacaoService:
    """Orquestra chamadas aos MS dependentes na exclusão lógica do processo."""

    def __init__(
        self,
        *,
        agenda_api: AgendaApiService | None = None,
        candidatos_api: CandidatosApiService | None = None,
        escolhas_api: EscolhasApiService | None = None,
    ) -> None:
        """Inicializa a instância com dependências configuráveis.

        Args:
            self: Instância do objeto.
            agenda_api: Cliente do MS-Agenda (opcional).
            candidatos_api: Cliente do MS-Candidatos (opcional).
            escolhas_api: Cliente do MS-Escolhas (opcional).

        Raises:
            Nenhuma exceção específica documentada.
        """
        self._agenda = agenda_api or AgendaApiService()
        self._candidatos = candidatos_api or CandidatosApiService()
        self._escolhas = escolhas_api or EscolhasApiService()

    def excluir_processo_e_dependencias(
        self,
        *,
        processo: ProcessoConvocacao,
    ) -> None:
        """Limpa dependências nos MS e inativa o processo localmente.

        Args:
            self: Instância do objeto.
            processo: Processo de convocação a ser inativado.

        Returns:
            Não retorna valor.

        Raises:
            ProcessoServiceError: Se a operação no processo falhar.
        """
        processo_uuid = str(processo.uuid)

        try:
            self._agenda.excluir_agendas_por_processo(processo_uuid)
        except AgendaServiceError as exc:
            logger.exception(
                "Falha ao excluir agendas do processo",
                extra={
                    "processo_uuid": processo_uuid,
                    "correlation_id": get_correlation_id(),
                    "error": str(exc),
                },
            )
            raise ProcessoServiceError(str(exc)) from exc

        try:
            self._candidatos.desconvocar_por_processo(
                processo_uuid=processo_uuid
            )
        except CandidatosServiceError as exc:
            logger.exception(
                "Falha ao desconvocar candidatos do processo",
                extra={
                    "processo_uuid": processo_uuid,
                    "correlation_id": get_correlation_id(),
                },
            )
            raise ProcessoServiceError(str(exc)) from exc

        try:
            self._escolhas.excluir_lotes_vagas_por_processo(processo_uuid)
        except EscolhasServiceError as exc:
            logger.exception(
                "Falha ao excluir lotes de vagas do processo",
                extra={
                    "processo_uuid": processo_uuid,
                    "correlation_id": get_correlation_id(),
                },
            )
            raise ProcessoServiceError(str(exc)) from exc

        processo.inativar()
