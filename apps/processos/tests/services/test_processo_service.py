"""Módulo tests/services/test_processo_service."""

from unittest.mock import Mock, patch

import pytest
from processos.services.agenda_api_service import AgendaApiService
from processos.services.candidatos_api_url import CandidatosApiService
from processos.services.concursos_api_service import ConcursosApiService
from processos.services.escolhas_service import EscolhasApiService
from processos.services.exceptions import (
    AgendaServiceError,
    CandidatosServiceError,
    ConcursoServiceError,
    EscolhasServiceError,
    ProcessoServiceError,
)
from processos.services.processo_service import ProcessoConvocacaoService


def _processo_mock(
    uuid_value: str = "11111111-1111-1111-1111-111111111111",
) -> Mock:
    """Cria mock de ProcessoConvocacao."""
    processo = Mock()
    processo.uuid = uuid_value
    processo.inativar = Mock()
    return processo


def test_excluir_processo_e_dependencias_sucesso_chama_integracoes_e_inativa():
    """Verifica exclusão com integrações e inativação local."""
    agenda = Mock(spec=AgendaApiService)
    candidatos = Mock(spec=CandidatosApiService)
    escolhas = Mock(spec=EscolhasApiService)
    processo = _processo_mock("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")

    service = ProcessoConvocacaoService(
        agenda_api=agenda,
        candidatos_api=candidatos,
        escolhas_api=escolhas,
    )

    with patch(
        "processos.services.processo_service.ProcessoConvocacaoRepository"
        ".contar_ativos_por_concurso",
        return_value=1,
    ):
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
    """Verifica falha na agenda sem chamar demais integrações."""
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
    """Verifica falha em candidatos sem chamar escolhas."""
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
    """Verifica falha em escolhas sem inativar processo."""
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


def test_excluir_processo_sem_convocacoes_ativas_restantes_atualiza_concurso_para_completo():  # noqa: E501
    """Reverte concurso para COMPLETO quando não sobra convocação ativa."""
    agenda = Mock(spec=AgendaApiService)
    candidatos = Mock(spec=CandidatosApiService)
    escolhas = Mock(spec=EscolhasApiService)
    concursos = Mock(spec=ConcursosApiService)
    processo = _processo_mock("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    processo.concurso_uuid = "cccccccc-cccc-cccc-cccc-cccccccccccc"

    service = ProcessoConvocacaoService(
        agenda_api=agenda,
        candidatos_api=candidatos,
        escolhas_api=escolhas,
        concursos_api=concursos,
    )

    with patch(
        "processos.services.processo_service.ProcessoConvocacaoRepository"
        ".contar_ativos_por_concurso",
        return_value=0,
    ):
        service.excluir_processo_e_dependencias(processo=processo)

    concursos.atualizar_situacao.assert_called_once_with(
        concurso_uuid="cccccccc-cccc-cccc-cccc-cccccccccccc",
        situacao="COMPLETO",
    )


def test_excluir_processo_com_convocacoes_ativas_restantes_nao_atualiza_concurso():  # noqa: E501
    """Não altera o concurso quando ainda há convocação ativa restante."""
    agenda = Mock(spec=AgendaApiService)
    candidatos = Mock(spec=CandidatosApiService)
    escolhas = Mock(spec=EscolhasApiService)
    concursos = Mock(spec=ConcursosApiService)
    processo = _processo_mock()
    processo.concurso_uuid = "cccccccc-cccc-cccc-cccc-cccccccccccc"

    service = ProcessoConvocacaoService(
        agenda_api=agenda,
        candidatos_api=candidatos,
        escolhas_api=escolhas,
        concursos_api=concursos,
    )

    with patch(
        "processos.services.processo_service.ProcessoConvocacaoRepository"
        ".contar_ativos_por_concurso",
        return_value=1,
    ):
        service.excluir_processo_e_dependencias(processo=processo)

    concursos.atualizar_situacao.assert_not_called()


def test_excluir_processo_quando_atualizar_situacao_concurso_falha_nao_propaga_erro():  # noqa: E501
    """Falha ao atualizar situação do concurso não aborta a exclusão."""
    agenda = Mock(spec=AgendaApiService)
    candidatos = Mock(spec=CandidatosApiService)
    escolhas = Mock(spec=EscolhasApiService)
    concursos = Mock(spec=ConcursosApiService)
    concursos.atualizar_situacao.side_effect = ConcursoServiceError("falhou")
    processo = _processo_mock()
    processo.concurso_uuid = "cccccccc-cccc-cccc-cccc-cccccccccccc"

    service = ProcessoConvocacaoService(
        agenda_api=agenda,
        candidatos_api=candidatos,
        escolhas_api=escolhas,
        concursos_api=concursos,
    )

    with patch(
        "processos.services.processo_service.ProcessoConvocacaoRepository"
        ".contar_ativos_por_concurso",
        return_value=0,
    ):
        service.excluir_processo_e_dependencias(processo=processo)

    processo.inativar.assert_called_once_with()
