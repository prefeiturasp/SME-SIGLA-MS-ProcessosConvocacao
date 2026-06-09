"""Testes unitários para os models do app processos usando pytest."""

import uuid

import pytest
from django.contrib.auth.models import User
from django.utils import timezone

from ..models import CargoProcesso, ProcessoConvocacao
from ..models.constants import PROCESSO_STATUS_CHOICES, TIPO_ESCOLHA_CHOICES

pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
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
def processo_convocacao(user, concurso_uuid, concurso_nome):
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
def processo_cargo(user):
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
def processo_integracao(user):
    """Fixture para processo de teste de integração."""
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Integração",
        descricao="Descrição integração",
        tipo_escolha="NOVA_AUTORIZACAO",
        status="EM_ANDAMENTO",
        data_convocacao=timezone.now() + timezone.timedelta(days=20),
    )


# Testes para ProcessoConvocacao Model
def test_processo_convocacao_creation(
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


def test_processo_convocacao_str_representation(
    processo_convocacao, concurso_nome
):
    """Testa a representação string do ProcessoConvocacao."""
    expected_str = f"{concurso_nome} - NOVA_AUTORIZACAO"
    assert str(processo_convocacao) == expected_str


def test_processo_convocacao_default_values():
    """Testa os valores padrão do ProcessoConvocacao."""
    processo_default = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Default",
        descricao="Descrição padrão",
    )

    assert processo_default.tipo_escolha == "NOVA_AUTORIZACAO"
    assert processo_default.status == "PENDENTE"
    assert processo_default.data_convocacao is not None
    assert processo_default.data_corte_vagas is not None


def test_processo_convocacao_choices_validation():
    """Testa a validação das choices."""
    # Teste com tipo_escolha válido
    processo_valido = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Válido",
        descricao="Descrição válida",
        tipo_escolha="REPOSICAO",
    )
    assert processo_valido.tipo_escolha in dict(TIPO_ESCOLHA_CHOICES)

    # Teste com status válido
    processo_status_valido = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Status Válido",
        descricao="Descrição status válido",
        status="FINALIZADO",
    )
    assert processo_status_valido.status in dict(PROCESSO_STATUS_CHOICES)


def test_processo_convocacao_meta_options(processo_convocacao):
    """Testa as opções Meta do ProcessoConvocacao."""
    assert processo_convocacao._meta.verbose_name == "Processo de Convocação"
    assert (
        processo_convocacao._meta.verbose_name_plural
        == "Processos de Convocação"
    )
    assert processo_convocacao._meta.db_table == "processos_convocacao"
    assert processo_convocacao._meta.ordering == ["-criado_em"]


def test_processo_convocacao_uuid_uniqueness(processo_convocacao):
    """Testa a unicidade do UUID."""
    # UUIDs devem ser únicos automaticamente
    processo2 = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso 2",
        descricao="Descrição 2",
    )

    assert processo_convocacao.uuid != processo2.uuid


def test_processo_convocacao_timestamps():
    """Testa os timestamps automáticos."""
    processo_novo = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Timestamp",
        descricao="Descrição timestamp",
    )

    assert processo_novo.criado_em is not None
    assert processo_novo.atualizado_em is not None

    # Atualizar o processo
    processo_novo.descricao = "Descrição atualizada"
    processo_novo.save()

    # criado_em não deve mudar, atualizado_em deve mudar
    assert processo_novo.criado_em == processo_novo.criado_em
    assert processo_novo.atualizado_em is not None


# Testes para CargoProcesso Model
def test_cargo_processo_creation(cargo_processo, processo_cargo):
    """Testa a criação de um CargoProcesso."""
    assert cargo_processo.processo == processo_cargo
    assert cargo_processo.cargo_nome == "Analista de Sistemas"
    assert cargo_processo.cargo_uuid is not None
    assert cargo_processo.uuid is not None
    assert cargo_processo.criado_em is not None
    assert cargo_processo.atualizado_em is not None


def test_cargo_processo_str_representation(cargo_processo, processo_cargo):
    """Testa a representação string do CargoProcesso."""
    expected_str = f"{processo_cargo.concurso_nome} - Analista de Sistemas"
    assert str(cargo_processo) == expected_str


def test_cargo_processo_meta_options(cargo_processo):
    """Testa as opções Meta do CargoProcesso."""
    assert cargo_processo._meta.verbose_name == "Cargo do Processo"
    assert cargo_processo._meta.verbose_name_plural == "Cargos do Processo"
    assert cargo_processo._meta.db_table == "processos_cargos"
    assert cargo_processo._meta.ordering == ["cargo_nome"]


def test_cargo_processo_unique_together(processo_cargo):
    """Testa a restrição unique_together."""
    # Deve permitir criar cargo com nome diferente
    cargo2 = CargoProcesso.objects.create(
        processo=processo_cargo,
        cargo_nome="Desenvolvedor Backend",
        cargo_uuid=uuid.uuid4(),
    )
    assert cargo2 is not None

    # Deve permitir criar cargo com mesmo nome em processo diferente
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


def test_cargo_processo_relationship(cargo_processo, processo_cargo):
    """Testa o relacionamento com ProcessoConvocacao."""
    # Testar related_name
    assert cargo_processo in processo_cargo.cargos_processo.all()

    # Testar que o cargo é removido quando o processo é removido
    cargo_uuid = cargo_processo.uuid
    processo_cargo.delete()

    with pytest.raises(CargoProcesso.DoesNotExist):
        CargoProcesso.objects.get(uuid=cargo_uuid)


def test_cargo_processo_uuid_uniqueness(cargo_processo, processo_cargo):
    """Testa a unicidade do UUID."""
    cargo2 = CargoProcesso.objects.create(
        processo=processo_cargo, cargo_nome="Cargo 2", cargo_uuid=uuid.uuid4()
    )

    assert cargo_processo.uuid != cargo2.uuid


def test_cargo_processo_cargo_uuid_uniqueness(processo_cargo):
    """Testa a unicidade do cargo_uuid."""
    cargo1 = CargoProcesso.objects.create(
        processo=processo_cargo, cargo_nome="Cargo 1", cargo_uuid=uuid.uuid4()
    )

    cargo2 = CargoProcesso.objects.create(
        processo=processo_cargo, cargo_nome="Cargo 2", cargo_uuid=uuid.uuid4()
    )

    assert cargo1.cargo_uuid != cargo2.cargo_uuid


def test_cargo_processo_timestamps(processo_cargo):
    """Testa os timestamps automáticos."""
    cargo_novo = CargoProcesso.objects.create(
        processo=processo_cargo,
        cargo_nome="Cargo Timestamp",
        cargo_uuid=uuid.uuid4(),
    )

    assert cargo_novo.criado_em is not None
    assert cargo_novo.atualizado_em is not None

    # Atualizar o cargo
    cargo_novo.cargo_nome = "Cargo Atualizado"
    cargo_novo.save()

    # criado_em não deve mudar, atualizado_em deve mudar
    assert cargo_novo.criado_em == cargo_novo.criado_em
    assert cargo_novo.atualizado_em is not None


# Testes de Integração entre Models
def test_processo_cargos_relationship(processo_integracao):
    """Testa o relacionamento entre processo e cargos."""
    # Criar múltiplos cargos
    cargos_nomes = ["Analista", "Desenvolvedor", "Testador"]

    for nome in cargos_nomes:
        CargoProcesso.objects.create(
            processo=processo_integracao,
            cargo_nome=nome,
            cargo_uuid=uuid.uuid4(),
        )

    # Verificar relacionamento
    assert processo_integracao.cargos_processo.count() == 3

    cargos_list = list(
        processo_integracao.cargos_processo.values_list(
            "cargo_nome", flat=True
        )
    )
    assert set(cargos_list) == set(cargos_nomes)


def test_processo_cascade_delete(processo_integracao):
    """Testa que cargos são removidos quando processo é removido."""
    # Criar cargos
    CargoProcesso.objects.create(
        processo=processo_integracao,
        cargo_nome="Cargo Teste",
        cargo_uuid=uuid.uuid4(),
    )

    # Verificar que cargo existe
    assert CargoProcesso.objects.count() == 1

    # Remover processo
    processo_integracao.delete()

    # Verificar que cargo foi removido
    assert CargoProcesso.objects.count() == 0


def test_processo_cargos_ordering(processo_integracao):
    """Testa a ordenação dos cargos."""
    # Criar cargos em ordem aleatória (CargoProcesso.ordering = ['cargo_nome'])
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

    # Verificar ordenação alfabética por cargo_nome
    cargos_ordenados = list(
        processo_integracao.cargos_processo.values_list(
            "cargo_nome", flat=True
        )
    )
    expected_order = ["Analista", "Desenvolvedor", "Zebra"]
    assert cargos_ordenados == expected_order
