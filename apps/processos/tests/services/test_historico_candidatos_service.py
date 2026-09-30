"""Testes do HistoricoCandidatosService."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import Mock, patch

from processos.services.historico_candidatos_service import (
    HistoricoCandidatosService,
)

REPO_BUSCAR = (
    "processos.services.historico_candidatos_service."
    "ProcessoConvocacaoRepository.buscar_por_uuids"
)


def _bloco_categoria(total: int, uuids: list[str]) -> dict:
    return {"total": total, "candidatos_uuids": uuids}


def _bloco_situacao(uuids: list[str]) -> dict:
    return {"total": len(uuids), "candidatos_uuids": uuids}


def test_montar_contagem_candidatos_soma_categorias():
    """Soma totais de GERAL, NNA e PCD."""
    contagem = HistoricoCandidatosService._montar_contagem_candidatos(
        {
            "GERAL": {"total": 8},
            "NNA": {"total": 1},
            "PCD": {"total": 1},
        }
    )
    assert contagem == {"total": 10, "geral": 8, "nna": 1, "pcd": 1}


def test_montar_contagem_candidatos_vazio():
    """Retorna zeros quando não há dados de categoria."""
    assert HistoricoCandidatosService._montar_contagem_candidatos(None) == {
        "total": 0,
        "geral": 0,
        "nna": 0,
        "pcd": 0,
    }


def test_cruzar_situacao_intersecta_uuids_por_categoria():
    """Cruza UUIDs da situação com as categorias dos habilitados."""
    geral_uuid = str(uuid.uuid4())
    nna_uuid = str(uuid.uuid4())
    outro = str(uuid.uuid4())

    resultado = HistoricoCandidatosService._cruzar_situacao(
        _bloco_situacao([geral_uuid, nna_uuid, outro]),
        {
            "GERAL": _bloco_categoria(1, [geral_uuid]),
            "NNA": _bloco_categoria(1, [nna_uuid]),
            "PCD": _bloco_categoria(0, []),
        },
    )
    assert resultado == {"total": 2, "geral": 1, "nna": 1, "pcd": 0}


def test_cruzar_situacao_com_habilitados_vazios():
    """Sem habilitados, o cruzamento resulta em zeros."""
    resultado = HistoricoCandidatosService._cruzar_situacao(
        _bloco_situacao([str(uuid.uuid4())]),
        {},
    )
    assert resultado == {"total": 0, "geral": 0, "nna": 0, "pcd": 0}


@patch(REPO_BUSCAR)
def test_historico_candidatos_por_processos_sem_processos_retorna_lista_vazia(
    mock_buscar,
):
    """Sem processos encontrados, não chama os microsserviços."""
    mock_buscar.return_value = []
    candidatos_api = Mock()
    escolhas_api = Mock()
    service = HistoricoCandidatosService(
        candidatos_api=candidatos_api,
        escolhas_api=escolhas_api,
    )

    assert (
        service.historico_candidatos_por_processos([str(uuid.uuid4())]) == []
    )
    metodo_hab = candidatos_api.buscar_habilitados_por_processos_e_tipo_vaga
    metodo_hab.assert_not_called()
    escolhas_api.buscar_escolhas_por_convocacao.assert_not_called()


@patch(REPO_BUSCAR)
def test_historico_candidatos_por_processos_cruza_apis(mock_buscar):
    """Monta histórico cruzando respostas de candidatos e escolhas."""
    geral_uuid = str(uuid.uuid4())
    nna_uuid = str(uuid.uuid4())
    pcd_uuid = str(uuid.uuid4())
    data_convocacao = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)

    processo = Mock()
    processo.uuid = uuid.uuid4()
    processo.descricao = "Processo histórico"
    processo.data_convocacao = data_convocacao
    mock_buscar.return_value = [processo]

    pid = str(processo.uuid)
    candidatos_api = Mock()
    metodo_hab = candidatos_api.buscar_habilitados_por_processos_e_tipo_vaga
    metodo_hab.return_value = {
        pid: {
            "GERAL": _bloco_categoria(1, [geral_uuid]),
            "NNA": _bloco_categoria(1, [nna_uuid]),
            "PCD": _bloco_categoria(1, [pcd_uuid]),
        }
    }
    escolhas_api = Mock()
    escolhas_api.buscar_escolhas_por_convocacao.return_value = {
        pid: {
            "escolha": _bloco_situacao([geral_uuid, nna_uuid]),
            "nao-escolha": _bloco_situacao([pcd_uuid]),
            "reconvocacao": _bloco_situacao([]),
        }
    }

    service = HistoricoCandidatosService(
        candidatos_api=candidatos_api,
        escolhas_api=escolhas_api,
    )
    resultado = service.historico_candidatos_por_processos([pid])

    assert len(resultado) == 1
    item = resultado[0]
    assert item["descricao"] == "Processo histórico"
    assert item["data_convocacao"] == data_convocacao.isoformat()
    assert item["candidatos"] == {"total": 3, "geral": 1, "nna": 1, "pcd": 1}
    assert item["escolha"] == {"total": 2, "geral": 1, "nna": 1, "pcd": 0}
    assert item["nao-escolha"] == {"total": 1, "geral": 0, "nna": 0, "pcd": 1}
    assert item["reconvocacao"] == {"total": 0, "geral": 0, "nna": 0, "pcd": 0}

    metodo_hab.assert_called_once_with([pid])
    escolhas_api.buscar_escolhas_por_convocacao.assert_called_once_with([pid])
