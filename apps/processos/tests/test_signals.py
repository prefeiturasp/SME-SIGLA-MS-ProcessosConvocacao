"""Módulo tests/test_signals."""

from __future__ import annotations

import uuid
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from django.utils import timezone

from processos.models import ProcessoConvocacao
from processos.services.exceptions import ConcursoServiceError

pytestmark = pytest.mark.django_db


def _dados_processo(**overrides: object) -> dict:
    dados = {
        "concurso_uuid": uuid.uuid4(),
        "concurso_nome": "Concurso Teste",
        "descricao": "Descrição do processo teste",
        "tipo_escolha": "NOVA_AUTORIZACAO",
        "status": "EM_ANDAMENTO",
        "data_convocacao": timezone.now() + timedelta(days=30),
        "data_corte_vagas": timezone.now() + timedelta(days=5),
    }
    dados.update(overrides)
    return dados


def test_signal_chama_atualizacao_situacao_concurso_em_andamento_ao_criar():
    """Verifica que criar processo dispara atualização de situação."""
    concurso_uuid = uuid.uuid4()

    with patch("processos.signals.ConcursosApiService") as mock_service_cls:
        mock_service = Mock()
        mock_service_cls.return_value = mock_service

        ProcessoConvocacao.objects.create(
            **_dados_processo(concurso_uuid=concurso_uuid)
        )

    mock_service.atualizar_situacao.assert_called_once_with(
        concurso_uuid=str(concurso_uuid), situacao="EM_ANDAMENTO"
    )


def test_signal_nao_falha_quando_atualizacao_situacao_da_erro():
    """Verifica que falha na chamada a Concursos não impede a criação."""
    with patch("processos.signals.ConcursosApiService") as mock_service_cls:
        mock_service = Mock()
        mock_service.atualizar_situacao.side_effect = ConcursoServiceError(
            "falhou"
        )
        mock_service_cls.return_value = mock_service

        processo = ProcessoConvocacao.objects.create(
            **_dados_processo(concurso_nome="Novo Concurso 2")
        )

    assert ProcessoConvocacao.objects.filter(pk=processo.pk).exists()


def test_signal_nao_chama_atualizacao_situacao_em_update():
    """Verifica que salvar update não dispara nova chamada ao concurso."""
    with patch("processos.signals.ConcursosApiService") as mock_service_cls:
        mock_service = Mock()
        mock_service_cls.return_value = mock_service
        processo = ProcessoConvocacao.objects.create(**_dados_processo())
        mock_service.atualizar_situacao.reset_mock()

        processo.descricao = "Descrição atualizada"
        processo.save()

    mock_service.atualizar_situacao.assert_not_called()
