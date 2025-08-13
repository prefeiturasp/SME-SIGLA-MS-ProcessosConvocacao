"""
Testes unitários para os serializers do app processos usando pytest.
"""
import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import uuid

from ..models import ProcessoConvocacao, CargoProcesso
from ..serializers import (
    ProcessoConvocacaoSerializer,
    ProcessoConvocacaoCreateSerializer,
    ProcessoConvocacaoListSerializer,
    ProcessoConvocacaoUpdateSerializer,
    CargoProcessoSerializer,
    CargoProcessoCreateSerializer
)


pytestmark = pytest.mark.django_db


@pytest.fixture
def user():
    """Fixture para criar um usuário de teste."""
    return User.objects.create_user(
        username='testuser',
        password='testpass123'
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
        tipo_processo='CONVOCACAO',
        status='EM_ANDAMENTO',
        data_publicacao=timezone.now(),
        data_convocacao=timezone.now() + timedelta(days=15),
        numero_convocados=5
    )


@pytest.fixture
def cargos_processo(processo_convocacao):
    """Fixture para criar cargos para o processo."""
    cargos = []
    nomes_cargos = ["Analista de Sistemas", "Desenvolvedor Backend"]
    
    for nome in nomes_cargos:
        cargo = CargoProcesso.objects.create(
            processo=processo_convocacao,
            nome=nome,
            cargo_uuid=uuid.uuid4()
        )
        cargos.append(cargo)
    
    return cargos


@pytest.fixture
def processo_cargo(user):
    """Fixture para processo de teste para cargos."""
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Teste",
        descricao="Descrição do processo teste",
        tipo_processo='CONVOCACAO',
        status='EM_ANDAMENTO',
        data_convocacao=timezone.now() + timedelta(days=10)
    )


@pytest.fixture
def cargo_processo(processo_cargo):
    """Fixture para criar um CargoProcesso."""
    return CargoProcesso.objects.create(
        processo=processo_cargo,
        nome="Analista de Sistemas",
        cargo_uuid=uuid.uuid4()
    )


# Testes para CargoProcessoSerializer
def test_cargo_processo_serializer_fields(cargo_processo):
    """Testa os campos do CargoProcessoSerializer."""
    serializer = CargoProcessoSerializer(cargo_processo)
    data = serializer.data
    
    assert 'uuid' in data
    assert 'nome' in data
    assert 'processo' in data
    assert 'criado_em' in data
    assert 'atualizado_em' in data
    assert data['uuid'] == str(cargo_processo.uuid)
    assert data['nome'] == cargo_processo.nome
    assert data['processo'] == cargo_processo.processo.uuid


# Testes para CargoProcessoCreateSerializer
def test_cargo_processo_create_serializer_fields():
    """Testa os campos do CargoProcessoCreateSerializer."""
    serializer = CargoProcessoCreateSerializer()
    assert 'nome' in serializer.fields


def test_cargo_processo_create_serializer_validation():
    """Testa a validação do CargoProcessoCreateSerializer."""
    data = {'nome': 'Analista de Sistemas'}
    serializer = CargoProcessoCreateSerializer(data=data)
    assert serializer.is_valid()


def test_cargo_processo_create_serializer_validation_empty():
    """Testa validação com nome vazio."""
    data = {'nome': ''}
    serializer = CargoProcessoCreateSerializer(data=data)
    assert not serializer.is_valid()


# Testes para ProcessoConvocacaoSerializer
def test_processo_convocacao_serializer_fields(processo_convocacao, cargos_processo):
    """Testa os campos do ProcessoConvocacaoSerializer."""
    serializer = ProcessoConvocacaoSerializer(processo_convocacao)
    data = serializer.data
    
    assert 'uuid' in data
    assert 'concurso_uuid' in data
    assert 'concurso_nome' in data
    assert 'descricao' in data
    assert 'tipo_processo' in data
    assert 'status' in data
    assert 'data_publicacao' in data
    assert 'data_convocacao' in data
    assert 'numero_convocados' in data
    assert 'cargos_processo' in data
    assert 'criado_em' in data
    assert 'atualizado_em' in data
    
    assert data['concurso_uuid'] == str(processo_convocacao.concurso_uuid)
    assert data['concurso_nome'] == processo_convocacao.concurso_nome
    assert data['descricao'] == processo_convocacao.descricao
    assert len(data['cargos_processo']) == 2


def test_processo_convocacao_serializer_read_only_fields():
    """Testa que campos read_only não podem ser modificados."""
    data = {
        'uuid': str(uuid.uuid4()),
        'concurso_uuid': str(uuid.uuid4()),
        'concurso_nome': 'Concurso Teste',
        'descricao': 'Descrição teste',
        'criado_em': '2024-01-01T00:00:00Z',
        'atualizado_em': '2024-01-01T00:00:00Z'
    }
    
    serializer = ProcessoConvocacaoSerializer(data=data)
    assert serializer.is_valid()
    
    # Campos read_only devem ser ignorados na criação
    processo = serializer.save()
    assert processo.uuid != data['uuid']
    assert processo.concurso_nome == data['concurso_nome']


# Testes para ProcessoConvocacaoCreateSerializer
def test_processo_convocacao_create_serializer_fields():
    """Testa os campos do ProcessoConvocacaoCreateSerializer."""
    serializer = ProcessoConvocacaoCreateSerializer()
    assert 'concurso_uuid' in serializer.fields
    assert 'concurso_nome' in serializer.fields
    assert 'descricao' in serializer.fields
    assert 'tipo_processo' in serializer.fields
    assert 'status' in serializer.fields
    assert 'data_convocacao' in serializer.fields
    assert 'numero_convocados' in serializer.fields
    assert 'cargos' in serializer.fields


def test_processo_convocacao_create_serializer_validation():
    """Testa a validação do ProcessoConvocacaoCreateSerializer."""
    data = {
        'concurso_uuid': str(uuid.uuid4()),
        'concurso_nome': 'Concurso Teste',
        'descricao': 'Descrição teste',
        'tipo_processo': 'CONVOCACAO',
        'status': 'EM_ANDAMENTO',
        'data_convocacao': timezone.now() + timedelta(days=30),
        'numero_convocados': 5,
        'cargos': [
            {'nome': 'Analista', 'cargo_uuid': str(uuid.uuid4())},
            {'nome': 'Desenvolvedor', 'cargo_uuid': str(uuid.uuid4())}
        ]
    }
    
    serializer = ProcessoConvocacaoCreateSerializer(data=data)
    assert serializer.is_valid()


def test_processo_convocacao_create_serializer_uuid_validation():
    """Testa a validação do UUID do concurso."""
    data = {
        'concurso_uuid': 'uuid-invalido',
        'concurso_nome': 'Concurso Teste',
        'descricao': 'Descrição teste'
    }
    
    serializer = ProcessoConvocacaoCreateSerializer(data=data)
    assert not serializer.is_valid()
    assert 'concurso_uuid' in serializer.errors


def test_processo_convocacao_create_serializer_create_with_cargos(user):
    """Testa a criação de processo com cargos."""
    data = {
        'concurso_uuid': str(uuid.uuid4()),
        'concurso_nome': 'Concurso Teste',
        'descricao': 'Descrição teste',
        'tipo_processo': 'CONVOCACAO',
        'status': 'EM_ANDAMENTO',
        'data_convocacao': timezone.now() + timedelta(days=30),
        'numero_convocados': 5,
        'cargos': [
            {'nome': 'Analista', 'cargo_uuid': str(uuid.uuid4())},
            {'nome': 'Desenvolvedor', 'cargo_uuid': str(uuid.uuid4())}
        ]
    }
    
    serializer = ProcessoConvocacaoCreateSerializer(data=data)
    assert serializer.is_valid()
    
    processo = serializer.save()
    assert processo.concurso_nome == 'Concurso Teste'
    assert processo.cargos_processo.count() == 2
    
    cargos_nomes = list(processo.cargos_processo.values_list('nome', flat=True))
    assert 'Analista' in cargos_nomes
    assert 'Desenvolvedor' in cargos_nomes


# Testes para ProcessoConvocacaoListSerializer
def test_processo_convocacao_list_serializer_fields(processo_convocacao):
    """Testa os campos do ProcessoConvocacaoListSerializer."""
    # Criar cargos para o processo
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        nome="Analista de Sistemas",
        cargo_uuid=uuid.uuid4()
    )
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        nome="Desenvolvedor Backend",
        cargo_uuid=uuid.uuid4()
    )
    
    serializer = ProcessoConvocacaoListSerializer(processo_convocacao)
    data = serializer.data
    
    assert 'uuid' in data
    assert 'concurso_nome' in data
    assert 'concurso_uuid' in data
    assert 'descricao' in data
    assert 'tipo_processo' in data
    assert 'status' in data
    assert 'data_convocacao' in data
    assert 'numero_convocados' in data
    assert 'quantidade_cargos' in data
    assert 'criado_em' in data
    
    assert data['concurso_nome'] == processo_convocacao.concurso_nome
    assert data['quantidade_cargos'] == 2


def test_processo_convocacao_list_serializer_quantidade_cargos(processo_convocacao):
    """Testa o campo calculado quantidade_cargos."""
    # Criar cargos para o processo
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        nome="Analista de Sistemas",
        cargo_uuid=uuid.uuid4()
    )
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        nome="Desenvolvedor Backend",
        cargo_uuid=uuid.uuid4()
    )
    
    serializer = ProcessoConvocacaoListSerializer(processo_convocacao)
    data = serializer.data
    
    assert data['quantidade_cargos'] == 2
    
    # Adicionar mais um cargo
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        nome="Testador",
        cargo_uuid=uuid.uuid4()
    )
    
    # Recarregar o serializer
    serializer_atualizado = ProcessoConvocacaoListSerializer(processo_convocacao)
    data_atualizado = serializer_atualizado.data
    
    assert data_atualizado['quantidade_cargos'] == 3


# Testes para ProcessoConvocacaoUpdateSerializer
def test_processo_convocacao_update_serializer_fields():
    """Testa os campos do ProcessoConvocacaoUpdateSerializer."""
    serializer = ProcessoConvocacaoUpdateSerializer()
    assert 'concurso_nome' in serializer.fields
    assert 'descricao' in serializer.fields
    assert 'tipo_processo' in serializer.fields
    assert 'status' in serializer.fields
    assert 'data_convocacao' in serializer.fields
    assert 'numero_convocados' in serializer.fields


def test_processo_convocacao_update_serializer_validation(processo_convocacao):
    """Testa a validação do ProcessoConvocacaoUpdateSerializer."""
    # Dados válidos para atualização
    data = {
        'concurso_nome': 'Concurso Atualizado',
        'descricao': 'Descrição atualizada',
        'status': 'FINALIZADO'
    }
    
    serializer = ProcessoConvocacaoUpdateSerializer(
        instance=processo_convocacao,
        data=data,
        partial=True
    )
    
    assert serializer.is_valid()
    
    processo_atualizado = serializer.save()
    assert processo_atualizado.concurso_nome == 'Concurso Atualizado'
    assert processo_atualizado.descricao == 'Descrição atualizada'
    assert processo_atualizado.status == 'FINALIZADO'


def test_processo_convocacao_update_serializer_partial_update(processo_convocacao):
    """Testa atualização parcial."""
    # Atualizar apenas o status
    data = {'status': 'CANCELADO'}
    
    serializer = ProcessoConvocacaoUpdateSerializer(
        instance=processo_convocacao,
        data=data,
        partial=True
    )
    
    assert serializer.is_valid()
    
    processo_atualizado = serializer.save()
    assert processo_atualizado.status == 'CANCELADO'
    # Outros campos devem permanecer inalterados
    assert processo_atualizado.concurso_nome == 'Concurso Teste'
    assert processo_atualizado.descricao == 'Descrição do processo teste'


# Testes de Integração
def test_serializer_integration_processo_cargos(processo_convocacao):
    """Testa integração entre serializers de processo e cargos."""
    # Criar cargos
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        nome="Analista",
        cargo_uuid=uuid.uuid4()
    )
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        nome="Desenvolvedor",
        cargo_uuid=uuid.uuid4()
    )
    
    # Serializar processo
    serializer = ProcessoConvocacaoSerializer(processo_convocacao)
    data = serializer.data
    
    assert len(data['cargos_processo']) == 2
    cargos_nomes = [cargo['nome'] for cargo in data['cargos_processo']]
    assert 'Analista' in cargos_nomes
    assert 'Desenvolvedor' in cargos_nomes


def test_serializer_error_handling():
    """Testa o tratamento de erros nos serializers."""
    # Testar serializer com dados inválidos
    data = {
        'concurso_uuid': 'uuid-invalido',
        'concurso_nome': '',  # Campo obrigatório vazio
        'descricao': 'Descrição válida'
    }
    
    serializer = ProcessoConvocacaoCreateSerializer(data=data)
    assert not serializer.is_valid()
    assert 'concurso_uuid' in serializer.errors
    assert 'concurso_nome' in serializer.errors 