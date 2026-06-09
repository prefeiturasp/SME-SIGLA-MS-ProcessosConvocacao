"""Módulo tests/services/test_processo_service."""
from unittest.mock import Mock

import pytest

from processos.services.agenda_api_service import AgendaApiService
from processos.services.candidatos_api_url import CandidatosApiService
from processos.services.escolhas_service import EscolhasApiService
from processos.services.exceptions import (
    AgendaServiceError,
    CandidatosServiceError,
    EscolhasServiceError,
    ProcessoServiceError,
)
from processos.services.processo_service import ProcessoConvocacaoService


def _processo_mock(
    uuid_value: str = "11111111-1111-1111-1111-111111111111",
) -> Mock:
    """Executa  processo mock.
    
    Args:
        uuid_value: Parâmetro uuid value da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    processo = Mock()
    processo.uuid = uuid_value
    processo.inativar = Mock()
    return processo


def test_excluir_processo_e_dependencias_sucesso_chama_integracoes_e_inativa():
    """Verifica excluir processo e dependencias sucesso chama integracoes e inativa.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    agenda = Mock(spec=AgendaApiService)
    candidatos = Mock(spec=CandidatosApiService)
    escolhas = Mock(spec=EscolhasApiService)
    processo = _processo_mock("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    service = ProcessoConvocacaoService(
        agenda_api=agenda,
        candidatos_api=candidatos,
        escolhas_api=escolhas,
    )

    service.excluir_processo_e_dependencias(processo=processo)

    agenda.excluir_agendas_por_processo.assert_called_once_with(
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    )
    candidatos.desconvocar_por_processo.assert_called_once_with(
        processo_uuid="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    )
    escolhas.excluir_lotes_vagas_por_processo.assert_called_once_with(
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    )
    processo.inativar.assert_called_once_with()


def test_excluir_processo_e_dependencias_quando_agenda_falha_retorna_processo_service_error_e_nao_chama_outros():  # noqa: E501
    """Verifica excluir processo e dependencias quando agenda falha retorna processo service error e nao chama outros.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    agenda = Mock(spec=AgendaApiService)
    candidatos = Mock(spec=CandidatosApiService)
    escolhas = Mock(spec=EscolhasApiService)
    processo = _processo_mock()

    agenda.excluir_agendas_por_processo.side_effect = AgendaServiceError(
        "agenda caiu"
    )

    service = ProcessoConvocacaoService(
        agenda_api=agenda,
        candidatos_api=candidatos,
        escolhas_api=escolhas,
    )

    with pytest.raises(ProcessoServiceError) as exc:
        service.excluir_processo_e_dependencias(processo=processo)

    assert "agenda caiu" in str(exc.value)
    candidatos.desconvocar_por_processo.assert_not_called()
    escolhas.excluir_lotes_vagas_por_processo.assert_not_called()
    processo.inativar.assert_not_called()


def test_excluir_processo_e_dependencias_quando_candidatos_falha_retorna_processo_service_error_e_nao_chama_escolhas():  # noqa: E501
    """Verifica excluir processo e dependencias quando candidatos falha retorna processo service error e nao chama escolhas.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    agenda = Mock(spec=AgendaApiService)
    candidatos = Mock(spec=CandidatosApiService)
    escolhas = Mock(spec=EscolhasApiService)
    processo = _processo_mock()

    candidatos.desconvocar_por_processo.side_effect = CandidatosServiceError(
        "candidatos caiu"
    )

    service = ProcessoConvocacaoService(
        agenda_api=agenda,
        candidatos_api=candidatos,
        escolhas_api=escolhas,
    )

    with pytest.raises(ProcessoServiceError) as exc:
        service.excluir_processo_e_dependencias(processo=processo)

    assert "candidatos caiu" in str(exc.value)
    agenda.excluir_agendas_por_processo.assert_called_once()
    escolhas.excluir_lotes_vagas_por_processo.assert_not_called()
    processo.inativar.assert_not_called()


def test_excluir_processo_e_dependencias_quando_escolhas_falha_retorna_processo_service_error_e_nao_inativa():  # noqa: E501
    """Verifica excluir processo e dependencias quando escolhas falha retorna processo service error e nao inativa.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    agenda = Mock(spec=AgendaApiService)
    candidatos = Mock(spec=CandidatosApiService)
    escolhas = Mock(spec=EscolhasApiService)
    processo = _processo_mock()

    escolhas.excluir_lotes_vagas_por_processo.side_effect = (
        EscolhasServiceError("escolhas caiu")
    )

    service = ProcessoConvocacaoService(
        agenda_api=agenda,
        candidatos_api=candidatos,
        escolhas_api=escolhas,
    )

    with pytest.raises(ProcessoServiceError) as exc:
        service.excluir_processo_e_dependencias(processo=processo)

    assert "escolhas caiu" in str(exc.value)
    agenda.excluir_agendas_por_processo.assert_called_once()
    candidatos.desconvocar_por_processo.assert_called_once()
    processo.inativar.assert_not_called()
