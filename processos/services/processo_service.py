"""
Regras de negócio do ProcessoConvocacao.

Centraliza operações que envolvem múltiplos microsserviços.
"""
import logging

from sigla_sdk.context import get_correlation_id
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
    """
    Orquestra chamadas aos MS dependentes na exclusão lógica do processo.
    """

    def __init__(
        self,
        *,
        agenda_api: AgendaApiService | None = None,
        candidatos_api: CandidatosApiService | None = None,
        escolhas_api: EscolhasApiService | None = None,
    ) -> None:
        self._agenda = agenda_api or AgendaApiService()
        self._candidatos = candidatos_api or CandidatosApiService()
        self._escolhas = escolhas_api or EscolhasApiService()

    def excluir_processo_e_dependencias(self, *, processo) -> None:
        """
        Executa a limpeza nos MS dependentes e faz a deleção lógica do processo.

        - MS-Agenda: excluir agendas do processo
        - MS-Candidatos: desconvocar candidatos do processo
        - MS-Escolha: excluir lotes de vagas-escolas do processo
        - Local: processo.inativar() (marca esta_ativo=False e remove cargos)
        """
        processo_uuid = str(processo.uuid)

        try:
            self._agenda.excluir_agendas_por_processo(processo_uuid)
        except AgendaServiceError as exc:
            logger.exception(
                'Falha ao excluir agendas do processo',
                extra={
                    "processo_uuid": processo_uuid,
                    "correlation_id": get_correlation_id(),
                    "error": str(exc),
                },
            )
            raise ProcessoServiceError(str(exc)) from exc

        try:
            self._candidatos.desconvocar_por_processo(processo_uuid=processo_uuid)
        except CandidatosServiceError as exc:
            logger.exception(
                'Falha ao desconvocar candidatos do processo',
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
                'Falha ao excluir lotes de vagas do processo',
                extra={
                    "processo_uuid": processo_uuid,
                    "correlation_id": get_correlation_id(),
                },
            )
            raise ProcessoServiceError(str(exc)) from exc

        processo.inativar()
