"""Testes unitários para os serializers do app cargos."""

import uuid

import pytest

from cargos.serializers import (
    CargoProcessoCreateSerializer,
    CargoProcessoSerializer,
)

pytestmark = pytest.mark.django_db


def test_cargo_processo_serializer_campos(cargo_processo):
    """Testa os campos do CargoProcessoSerializer."""
    serializer = CargoProcessoSerializer(cargo_processo)
    dados = serializer.data

    assert "uuid" in dados
    assert "cargo_nome" in dados
    assert "processo" in dados
    assert "criado_em" in dados
    assert "atualizado_em" in dados
    assert dados["uuid"] == str(cargo_processo.uuid)
    assert dados["cargo_nome"] == cargo_processo.cargo_nome
    assert str(dados["processo"]) == str(cargo_processo.processo.uuid)


def test_cargo_processo_create_serializer_campos():
    """Testa os campos do CargoProcessoCreateSerializer."""
    serializer = CargoProcessoCreateSerializer()
    assert "cargo_nome" in serializer.fields


def test_cargo_processo_create_serializer_validacao():
    """Testa a validação do CargoProcessoCreateSerializer."""
    dados = {
        "cargo_nome": "Analista de Sistemas",
        "cargo_uuid": str(uuid.uuid4()),
    }
    serializer = CargoProcessoCreateSerializer(data=dados)
    assert serializer.is_valid()


def test_cargo_processo_create_serializer_validacao_vazio():
    """Testa validação com cargo_nome vazio."""
    dados = {"cargo_nome": "", "cargo_uuid": str(uuid.uuid4())}
    serializer = CargoProcessoCreateSerializer(data=dados)
    assert not serializer.is_valid()
