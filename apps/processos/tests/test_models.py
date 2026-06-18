"""Testes unitários para os models do app processos usando pytest."""

import uuid

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from cargos.models import CargoProcesso
from processos.models import ProcessoConvocacao
from processos.models.constants import PROCESSO_STATUS_CHOICES, TIPO_ESCOLHA_CHOICES

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
        tipo_escolha="NOVA_AUTORIZACAO",
        status="EM_ANDAMENTO",
        data_corte_vagas=timezone.now(),
        data_convocacao=timezone.now() + timezone.timedelta(days=15),
    )


@pytest.fixture
def processo_integracao(usuario):
    """Fixture para processo de teste de integração."""
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Integração",
        descricao="Descrição integração",
        tipo_escolha="NOVA_AUTORIZACAO",
        status="EM_ANDAMENTO",
        data_convocacao=timezone.now() + timezone.timedelta(days=20),
    )


# Testes do model ProcessoConvocacao
def test_processo_convocacao_criacao(
    processo_convocacao, concurso_uuid, concurso_nome
):
    """Testa a criação de um ProcessoConvocacao."""
    assert processo_convocacao.concurso_uuid == concurso_uuid
    assert processo_convocacao.concurso_nome == concurso_nome
    assert processo_convocacao.descricao == "Descrição do processo teste"
    assert processo_convocacao.tipo_escolha == "NOVA_AUTORIZACAO"
    assert processo_convocacao.status == "EM_ANDAMENTO"
    assert processo_convocacao.uuid is not None
    assert processo_convocacao.criado_em is not None
    assert processo_convocacao.atualizado_em is not None


def test_processo_convocacao_representacao_str(
    processo_convocacao, concurso_nome
):
    """Testa a representação string do ProcessoConvocacao."""
    str_esperada = f"{concurso_nome} - NOVA_AUTORIZACAO"
    assert str(processo_convocacao) == str_esperada


def test_processo_convocacao_valores_padrao():
    """Testa os valores padrão do ProcessoConvocacao."""
    processo_padrao = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Padrão",
        descricao="Descrição padrão",
    )

    assert processo_padrao.tipo_escolha == "NOVA_AUTORIZACAO"
    assert processo_padrao.status == "PENDENTE"
    assert processo_padrao.data_convocacao is not None
    assert processo_padrao.data_corte_vagas is not None


def test_processo_convocacao_validacao_choices():
    """Testa a validação das choices."""
    processo_valido = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Válido",
        descricao="Descrição válida",
        tipo_escolha="REPOSICAO",
    )
    assert processo_valido.tipo_escolha in dict(TIPO_ESCOLHA_CHOICES)

    processo_status_valido = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Status Válido",
        descricao="Descrição status válido",
        status="FINALIZADO",
    )
    assert processo_status_valido.status in dict(PROCESSO_STATUS_CHOICES)


def test_processo_convocacao_meta_opcoes(processo_convocacao):
    """Testa as opções Meta do ProcessoConvocacao."""
    assert processo_convocacao._meta.verbose_name == "Processo de Convocação"
    assert (
        processo_convocacao._meta.verbose_name_plural
        == "Processos de Convocação"
    )
    assert processo_convocacao._meta.db_table == "processos_convocacao"
    assert processo_convocacao._meta.ordering == ["-criado_em"]


def test_processo_convocacao_unicidade_uuid(processo_convocacao):
    """Testa a unicidade do UUID."""
    processo2 = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso 2",
        descricao="Descrição 2",
    )

    assert processo_convocacao.uuid != processo2.uuid


def test_processo_convocacao_datas_criacao_atualizacao():
    """Testa as datas de criação e atualização automáticas."""
    processo_novo = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Timestamp",
        descricao="Descrição timestamp",
    )

    assert processo_novo.criado_em is not None
    assert processo_novo.atualizado_em is not None

    processo_novo.descricao = "Descrição atualizada"
    processo_novo.save()

    assert processo_novo.criado_em == processo_novo.criado_em
    assert processo_novo.atualizado_em is not None


# Testes de integração ProcessoConvocacao ↔ CargoProcesso
def test_processo_cargos_relacionamento(processo_integracao):
    """Testa o relacionamento entre processo e cargos."""
    cargos_nomes = ["Analista", "Desenvolvedor", "Testador"]

    for nome in cargos_nomes:
        CargoProcesso.objects.create(
            processo=processo_integracao,
            cargo_nome=nome,
            cargo_uuid=uuid.uuid4(),
        )

    assert processo_integracao.cargos_processo.count() == 3

    lista_cargos = list(
        processo_integracao.cargos_processo.values_list(
            "cargo_nome", flat=True
        )
    )
    assert set(lista_cargos) == set(cargos_nomes)


def test_processo_exclusao_em_cascata(processo_integracao):
    """Testa que cargos são removidos quando processo é removido."""
    CargoProcesso.objects.create(
        processo=processo_integracao,
        cargo_nome="Cargo Teste",
        cargo_uuid=uuid.uuid4(),
    )

    assert CargoProcesso.objects.count() == 1

    processo_integracao.delete()

    assert CargoProcesso.objects.count() == 0
