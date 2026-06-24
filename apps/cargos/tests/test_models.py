"""Testes unitários para os models do app cargos usando pytest."""

import uuid

import pytest
from cargos.models import CargoProcesso
from django.contrib.auth.models import User
from django.utils import timezone
from processos.models import ProcessoConvocacao

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
def processo_cargo(usuario):
    """Fixture para processo de teste para cargos."""
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Teste",
        descricao="Descrição do processo teste",
        tipo_escolha="NOVA_AUTORIZACAO",
        status="EM_ANDAMENTO",
        data_convocacao=timezone.now() + timezone.timedelta(days=10),
    )


@pytest.fixture
def cargo_processo(processo_cargo):
    """Fixture para criar um CargoProcesso."""
    return CargoProcesso.objects.create(
        processo=processo_cargo,
        cargo_nome="Analista de Sistemas",
        cargo_uuid=uuid.uuid4(),
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


# Testes do model CargoProcesso
def test_cargo_processo_criacao(cargo_processo, processo_cargo):
    """Testa a criação de um CargoProcesso."""
    assert cargo_processo.processo == processo_cargo
    assert cargo_processo.cargo_nome == "Analista de Sistemas"
    assert cargo_processo.cargo_uuid is not None
    assert cargo_processo.uuid is not None
    assert cargo_processo.criado_em is not None
    assert cargo_processo.atualizado_em is not None


def test_cargo_processo_representacao_str(cargo_processo, processo_cargo):
    """Testa a representação string do CargoProcesso."""
    str_esperada = f"{processo_cargo.concurso_nome} - Analista de Sistemas"
    assert str(cargo_processo) == str_esperada


def test_cargo_processo_meta_opcoes(cargo_processo):
    """Testa as opções Meta do CargoProcesso."""
    assert cargo_processo._meta.verbose_name == "Cargo do Processo"
    assert cargo_processo._meta.verbose_name_plural == "Cargos do Processo"
    assert cargo_processo._meta.db_table == "processos_cargos"
    assert cargo_processo._meta.ordering == ["cargo_nome"]


def test_cargo_processo_restricao_unicidade(processo_cargo):
    """Testa a restrição unique_together."""
    cargo2 = CargoProcesso.objects.create(
        processo=processo_cargo,
        cargo_nome="Desenvolvedor Backend",
        cargo_uuid=uuid.uuid4(),
    )
    assert cargo2 is not None

    processo2 = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso 2",
        descricao="Descrição 2",
    )
    cargo3 = CargoProcesso.objects.create(
        processo=processo2,
        cargo_nome="Analista de Sistemas",
        cargo_uuid=uuid.uuid4(),
    )
    assert cargo3 is not None


def test_cargo_processo_relacionamento(cargo_processo, processo_cargo):
    """Testa o relacionamento com ProcessoConvocacao."""
    assert cargo_processo in processo_cargo.cargos_processo.all()

    uuid_cargo = cargo_processo.uuid
    processo_cargo.delete()

    with pytest.raises(CargoProcesso.DoesNotExist):
        CargoProcesso.objects.get(uuid=uuid_cargo)


def test_cargo_processo_unicidade_uuid(cargo_processo, processo_cargo):
    """Testa a unicidade do UUID."""
    cargo2 = CargoProcesso.objects.create(
        processo=processo_cargo, cargo_nome="Cargo 2", cargo_uuid=uuid.uuid4()
    )

    assert cargo_processo.uuid != cargo2.uuid


def test_cargo_processo_unicidade_cargo_uuid(processo_cargo):
    """Testa a unicidade do cargo_uuid."""
    cargo1 = CargoProcesso.objects.create(
        processo=processo_cargo, cargo_nome="Cargo 1", cargo_uuid=uuid.uuid4()
    )

    cargo2 = CargoProcesso.objects.create(
        processo=processo_cargo, cargo_nome="Cargo 2", cargo_uuid=uuid.uuid4()
    )

    assert cargo1.cargo_uuid != cargo2.cargo_uuid


def test_cargo_processo_datas_criacao_atualizacao(processo_cargo):
    """Testa as datas de criação e atualização automáticas."""
    cargo_novo = CargoProcesso.objects.create(
        processo=processo_cargo,
        cargo_nome="Cargo Timestamp",
        cargo_uuid=uuid.uuid4(),
    )

    assert cargo_novo.criado_em is not None
    assert cargo_novo.atualizado_em is not None

    cargo_novo.cargo_nome = "Cargo Atualizado"
    cargo_novo.save()

    assert cargo_novo.criado_em == cargo_novo.criado_em
    assert cargo_novo.atualizado_em is not None


def test_processo_cargos_ordenacao(processo_integracao):
    """Testa a ordenação dos cargos."""
    CargoProcesso.objects.create(
        processo=processo_integracao,
        cargo_nome="Zebra",
        cargo_uuid=uuid.uuid4(),
    )
    CargoProcesso.objects.create(
        processo=processo_integracao,
        cargo_nome="Analista",
        cargo_uuid=uuid.uuid4(),
    )
    CargoProcesso.objects.create(
        processo=processo_integracao,
        cargo_nome="Desenvolvedor",
        cargo_uuid=uuid.uuid4(),
    )

    cargos_ordenados = list(
        processo_integracao.cargos_processo.values_list(
            "cargo_nome", flat=True
        )
    )
    ordem_esperada = ["Analista", "Desenvolvedor", "Zebra"]
    assert cargos_ordenados == ordem_esperada
