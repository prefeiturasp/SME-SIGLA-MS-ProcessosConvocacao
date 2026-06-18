"""Testes unitários para os serializers do app processos usando pytest."""

import uuid
from datetime import timedelta

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from cargos.models import CargoProcesso
from processos.models import ProcessoConvocacao
from processos.serializers import (
    ProcessoConvocacaoCreateSerializer,
    ProcessoConvocacaoListSerializer,
    ProcessoConvocacaoSerializer,
    ProcessoConvocacaoUpdateSerializer,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def usuario():
    """Fixture para criar um usuário de teste."""
    return User.objects.create_user(
        username="testuser", password="testpass123"
    )


@pytest.fixture
def concurso_uuid():
    """Fixture para UUID do concurso."""
    return uuid.uuid4()


@pytest.fixture
def concurso_nome():
    """Fixture para nome do concurso."""
    return "Concurso Teste"


@pytest.fixture
def processo_convocacao(usuario, concurso_uuid, concurso_nome):
    """Fixture para criar um ProcessoConvocacao."""
    return ProcessoConvocacao.objects.create(
        concurso_uuid=concurso_uuid,
        concurso_nome=concurso_nome,
        descricao="Descrição do processo teste",
        tipo_escolha="Nova Autorização",
        status="EM_ANDAMENTO",
        data_corte_vagas=timezone.now(),
        data_convocacao=timezone.now() + timedelta(days=15),
    )


@pytest.fixture
def cargos_processo(processo_convocacao):
    """Fixture para criar cargos para o processo."""
    cargos = []
    nomes_cargos = ["Analista de Sistemas", "Desenvolvedor Backend"]

    for nome in nomes_cargos:
        cargo = CargoProcesso.objects.create(
            processo=processo_convocacao,
            cargo_nome=nome,
            cargo_uuid=uuid.uuid4(),
        )
        cargos.append(cargo)

    return cargos


def test_processo_convocacao_serializer_campos(
    processo_convocacao, cargos_processo
):
    """Testa os campos do ProcessoConvocacaoSerializer."""
    serializer = ProcessoConvocacaoSerializer(processo_convocacao)
    dados = serializer.data

    assert "uuid" in dados
    assert "concurso_uuid" in dados
    assert "concurso_nome" in dados
    assert "descricao" in dados
    assert "tipo_escolha" in dados
    assert "status" in dados
    assert "data_corte_vagas" in dados
    assert "data_convocacao" in dados
    assert "data_corte_vagas" in dados
    assert "cargos_processo" in dados
    assert "criado_em" in dados
    assert "atualizado_em" in dados

    assert dados["concurso_uuid"] == str(processo_convocacao.concurso_uuid)
    assert dados["concurso_nome"] == processo_convocacao.concurso_nome
    assert dados["descricao"] == processo_convocacao.descricao
    assert len(dados["cargos_processo"]) == 2


def test_processo_convocacao_serializer_campos_somente_leitura():
    """Testa que campos read_only não podem ser modificados."""
    dados = {
        "uuid": str(uuid.uuid4()),
        "concurso_uuid": str(uuid.uuid4()),
        "concurso_nome": "Concurso Teste",
        "descricao": "Descrição teste",
        "criado_em": "2024-01-01T00:00:00Z",
        "atualizado_em": "2024-01-01T00:00:00Z",
    }

    serializer = ProcessoConvocacaoSerializer(data=dados)
    assert serializer.is_valid()

    processo = serializer.save()
    assert processo.uuid != dados["uuid"]
    assert processo.concurso_nome == dados["concurso_nome"]


def test_processo_convocacao_create_serializer_campos():
    """Testa os campos do ProcessoConvocacaoCreateSerializer."""
    serializer = ProcessoConvocacaoCreateSerializer()
    assert "concurso_uuid" in serializer.fields
    assert "concurso_nome" in serializer.fields
    assert "descricao" in serializer.fields
    assert "tipo_escolha" in serializer.fields
    assert "status" in serializer.fields
    assert "data_convocacao" in serializer.fields
    assert "data_corte_vagas" in serializer.fields


def test_processo_convocacao_create_serializer_validacao():
    """Testa a validação do ProcessoConvocacaoCreateSerializer."""
    dados = {
        "concurso_uuid": str(uuid.uuid4()),
        "concurso_nome": "Concurso Teste",
        "descricao": "Descrição teste",
        "tipo_escolha": "NOVA_AUTORIZACAO",
        "status": "EM_ANDAMENTO",
        "data_convocacao": (timezone.now() + timedelta(days=30)).isoformat(),
        "data_corte_vagas": (timezone.now() + timedelta(days=5)).isoformat(),
    }
    serializer = ProcessoConvocacaoCreateSerializer(data=dados)
    assert serializer.is_valid()


def test_processo_convocacao_create_serializer_validacao_uuid():
    """Testa a validação do UUID do concurso."""
    dados = {
        "concurso_uuid": "uuid-invalido",
        "concurso_nome": "Concurso Teste",
        "descricao": "Descrição teste",
    }

    serializer = ProcessoConvocacaoCreateSerializer(data=dados)
    assert not serializer.is_valid()
    assert "concurso_uuid" in serializer.errors


def test_processo_convocacao_create_serializer_criacao(usuario):
    """Testa a criação de processo de convocação."""
    dados = {
        "concurso_uuid": str(uuid.uuid4()),
        "concurso_nome": "Concurso Teste",
        "descricao": "Descrição teste",
        "tipo_escolha": "NOVA_AUTORIZACAO",
        "status": "EM_ANDAMENTO",
        "data_convocacao": (timezone.now() + timedelta(days=30)).isoformat(),
        "data_corte_vagas": (timezone.now() + timedelta(days=5)).isoformat(),
    }
    serializer = ProcessoConvocacaoCreateSerializer(data=dados)
    assert serializer.is_valid()
    processo = serializer.save()
    assert processo.concurso_nome == "Concurso Teste"
    assert processo.tipo_escolha == "NOVA_AUTORIZACAO"


def test_processo_convocacao_list_serializer_campos(processo_convocacao):
    """Testa os campos do ProcessoConvocacaoListSerializer."""
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Analista de Sistemas",
        cargo_uuid=uuid.uuid4(),
    )
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Desenvolvedor Backend",
        cargo_uuid=uuid.uuid4(),
    )

    serializer = ProcessoConvocacaoListSerializer(processo_convocacao)
    dados = serializer.data

    assert "uuid" in dados
    assert "concurso_nome" in dados
    assert "concurso_uuid" in dados
    assert "descricao" in dados
    assert "tipo_escolha" in dados
    assert "status" in dados
    assert "data_convocacao" in dados
    assert "data_corte_vagas" in dados
    assert "quantidade_cargos" in dados
    assert "criado_em" in dados

    assert dados["concurso_nome"] == processo_convocacao.concurso_nome
    assert dados["quantidade_cargos"] == 2


def test_processo_convocacao_list_serializer_quantidade_cargos(
    processo_convocacao,
):
    """Testa o campo calculado quantidade_cargos."""
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Analista de Sistemas",
        cargo_uuid=uuid.uuid4(),
    )
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Desenvolvedor Backend",
        cargo_uuid=uuid.uuid4(),
    )

    serializer = ProcessoConvocacaoListSerializer(processo_convocacao)
    dados = serializer.data

    assert dados["quantidade_cargos"] == 2

    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Testador",
        cargo_uuid=uuid.uuid4(),
    )

    serializer_atualizado = ProcessoConvocacaoListSerializer(
        processo_convocacao
    )
    dados_atualizado = serializer_atualizado.data

    assert dados_atualizado["quantidade_cargos"] == 3


def test_processo_convocacao_update_serializer_campos():
    """Testa os campos do ProcessoConvocacaoUpdateSerializer."""
    serializer = ProcessoConvocacaoUpdateSerializer()
    assert "concurso_nome" in serializer.fields
    assert "descricao" in serializer.fields
    assert "tipo_escolha" in serializer.fields
    assert "status" in serializer.fields
    assert "data_convocacao" in serializer.fields
    assert "data_corte_vagas" in serializer.fields


def test_processo_convocacao_update_serializer_validacao(processo_convocacao):
    """Testa a validação do ProcessoConvocacaoUpdateSerializer."""
    dados = {
        "concurso_nome": "Concurso Atualizado",
        "descricao": "Descrição atualizada",
        "status": "FINALIZADO",
    }

    serializer = ProcessoConvocacaoUpdateSerializer(
        instance=processo_convocacao, data=dados, partial=True
    )

    assert serializer.is_valid()

    processo_atualizado = serializer.save()
    assert processo_atualizado.concurso_nome == "Concurso Atualizado"
    assert processo_atualizado.descricao == "Descrição atualizada"
    assert processo_atualizado.status == "FINALIZADO"


def test_processo_convocacao_update_serializer_atualizacao_parcial(
    processo_convocacao,
):
    """Testa atualização parcial."""
    dados = {"status": "CANCELADO"}

    serializer = ProcessoConvocacaoUpdateSerializer(
        instance=processo_convocacao, data=dados, partial=True
    )

    assert serializer.is_valid()

    processo_atualizado = serializer.save()
    assert processo_atualizado.status == "CANCELADO"
    assert processo_atualizado.concurso_nome == "Concurso Teste"
    assert processo_atualizado.descricao == "Descrição do processo teste"


def test_serializer_integracao_processo_cargos(processo_convocacao):
    """Testa integração entre serializers de processo e cargos."""
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Analista",
        cargo_uuid=uuid.uuid4(),
    )
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Desenvolvedor",
        cargo_uuid=uuid.uuid4(),
    )

    serializer = ProcessoConvocacaoSerializer(processo_convocacao)
    dados = serializer.data

    assert len(dados["cargos_processo"]) == 2
    cargos_nomes = [cargo["cargo_nome"] for cargo in dados["cargos_processo"]]
    assert "Analista" in cargos_nomes
    assert "Desenvolvedor" in cargos_nomes


def test_serializer_tratamento_erros():
    """Testa o tratamento de erros nos serializers."""
    dados = {
        "concurso_uuid": "uuid-invalido",
        "concurso_nome": "",
        "descricao": "Descrição válida",
    }

    serializer = ProcessoConvocacaoCreateSerializer(data=dados)
    assert not serializer.is_valid()
    assert "concurso_uuid" in serializer.errors
    assert "concurso_nome" in serializer.errors
