"""
Testes unitários para os serializers do app processos usando pytest.
"""
import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import uuid

from ..models import ProcessoConvocacao, CargoProcesso, EnvioEmail, EnvioEmailCandidato
from ..models.envio_email import TIPO_CONVOCACAO
from ..serializers import (
    ProcessoConvocacaoSerializer,
    ProcessoConvocacaoCreateSerializer,
    ProcessoConvocacaoListSerializer,
    ProcessoConvocacaoUpdateSerializer,
    CargoProcessoSerializer,
    CargoProcessoCreateSerializer,
    EnvioEmailSerializer,
    EnvioEmailCandidatoSerializer,
    EnvioEmailDetalheSerializer,
    EnvioEmailEnvioSerializer,
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
        tipo_escolha='Nova Autorização',
        status='EM_ANDAMENTO',
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
        tipo_escolha='Nova Autorização',
        status='EM_ANDAMENTO',
        data_convocacao=timezone.now() + timedelta(days=10)
    )


@pytest.fixture
def cargo_processo(processo_cargo):
    """Fixture para criar um CargoProcesso."""
    return CargoProcesso.objects.create(
        processo=processo_cargo,
        cargo_nome="Analista de Sistemas",
        cargo_uuid=uuid.uuid4()
    )


# Testes para CargoProcessoSerializer
def test_cargo_processo_serializer_fields(cargo_processo):
    """Testa os campos do CargoProcessoSerializer."""
    serializer = CargoProcessoSerializer(cargo_processo)
    data = serializer.data
    
    assert 'uuid' in data
    assert 'cargo_nome' in data
    assert 'processo' in data
    assert 'criado_em' in data
    assert 'atualizado_em' in data
    assert data['uuid'] == str(cargo_processo.uuid)
    assert data['cargo_nome'] == cargo_processo.cargo_nome
    assert str(data['processo']) == str(cargo_processo.processo.uuid)


# Testes para CargoProcessoCreateSerializer
def test_cargo_processo_create_serializer_fields():
    """Testa os campos do CargoProcessoCreateSerializer."""
    serializer = CargoProcessoCreateSerializer()
    assert 'cargo_nome' in serializer.fields


def test_cargo_processo_create_serializer_validation():
    """Testa a validação do CargoProcessoCreateSerializer."""
    data = {'cargo_nome': 'Analista de Sistemas', 'cargo_uuid': str(uuid.uuid4())}
    serializer = CargoProcessoCreateSerializer(data=data)
    assert serializer.is_valid()


def test_cargo_processo_create_serializer_validation_empty():
    """Testa validação com cargo_nome vazio."""
    data = {'cargo_nome': '', 'cargo_uuid': str(uuid.uuid4())}
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
    assert 'tipo_escolha' in data
    assert 'status' in data
    assert 'data_corte_vagas' in data
    assert 'data_convocacao' in data
    assert 'data_corte_vagas' in data
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
    assert 'tipo_escolha' in serializer.fields
    assert 'status' in serializer.fields
    assert 'data_convocacao' in serializer.fields
    assert 'data_corte_vagas' in serializer.fields


def test_processo_convocacao_create_serializer_validation():
    """Testa a validação do ProcessoConvocacaoCreateSerializer."""
    data = {
        'concurso_uuid': str(uuid.uuid4()),
        'concurso_nome': 'Concurso Teste',
        'descricao': 'Descrição teste',
        'tipo_escolha': 'NOVA_AUTORIZACAO',
        'status': 'EM_ANDAMENTO',
        'data_convocacao': (timezone.now() + timedelta(days=30)).isoformat(),
        'data_corte_vagas': (timezone.now() + timedelta(days=5)).isoformat(),
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


def test_processo_convocacao_create_serializer_create(user):
    """Testa a criação de processo de convocação."""
    data = {
        'concurso_uuid': str(uuid.uuid4()),
        'concurso_nome': 'Concurso Teste',
        'descricao': 'Descrição teste',
        'tipo_escolha': 'NOVA_AUTORIZACAO',
        'status': 'EM_ANDAMENTO',
        'data_convocacao': (timezone.now() + timedelta(days=30)).isoformat(),
        'data_corte_vagas': (timezone.now() + timedelta(days=5)).isoformat(),
    }
    serializer = ProcessoConvocacaoCreateSerializer(data=data)
    assert serializer.is_valid()
    processo = serializer.save()
    assert processo.concurso_nome == 'Concurso Teste'
    assert processo.tipo_escolha == 'NOVA_AUTORIZACAO'


# Testes para ProcessoConvocacaoListSerializer
def test_processo_convocacao_list_serializer_fields(processo_convocacao):
    """Testa os campos do ProcessoConvocacaoListSerializer."""
    # Criar cargos para o processo
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Analista de Sistemas",
        cargo_uuid=uuid.uuid4()
    )
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Desenvolvedor Backend",
        cargo_uuid=uuid.uuid4()
    )
    
    serializer = ProcessoConvocacaoListSerializer(processo_convocacao)
    data = serializer.data
    
    assert 'uuid' in data
    assert 'concurso_nome' in data
    assert 'concurso_uuid' in data
    assert 'descricao' in data
    assert 'tipo_escolha' in data
    assert 'status' in data
    assert 'data_convocacao' in data
    assert 'data_corte_vagas' in data
    assert 'quantidade_cargos' in data
    assert 'criado_em' in data
    
    assert data['concurso_nome'] == processo_convocacao.concurso_nome
    assert data['quantidade_cargos'] == 2


def test_processo_convocacao_list_serializer_quantidade_cargos(processo_convocacao):
    """Testa o campo calculado quantidade_cargos."""
    # Criar cargos para o processo
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Analista de Sistemas",
        cargo_uuid=uuid.uuid4()
    )
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Desenvolvedor Backend",
        cargo_uuid=uuid.uuid4()
    )
    
    serializer = ProcessoConvocacaoListSerializer(processo_convocacao)
    data = serializer.data
    
    assert data['quantidade_cargos'] == 2
    
    # Adicionar mais um cargo
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Testador",
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
    assert 'tipo_escolha' in serializer.fields
    assert 'status' in serializer.fields
    assert 'data_convocacao' in serializer.fields
    assert 'data_corte_vagas' in serializer.fields


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
        cargo_nome="Analista",
        cargo_uuid=uuid.uuid4()
    )
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Desenvolvedor",
        cargo_uuid=uuid.uuid4()
    )
    
    # Serializar processo
    serializer = ProcessoConvocacaoSerializer(processo_convocacao)
    data = serializer.data
    
    assert len(data['cargos_processo']) == 2
    cargos_nomes = [cargo['cargo_nome'] for cargo in data['cargos_processo']]
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


# --- Testes Envio Email (histórico e detalhe) ---


@pytest.fixture
def envio_email(processo_convocacao):
    """Fixture para EnvioEmail."""
    return EnvioEmail.objects.create(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        tipo=TIPO_CONVOCACAO,
        quantidade_candidatos=2,
    )


@pytest.fixture
def envio_email_candidatos(envio_email):
    """Fixture para EnvioEmailCandidato vinculados ao envio."""
    from processos.models.envio_email_candidato import ENVIO_STATUS_SUCESSO, ENVIO_STATUS_ERRO
    EnvioEmailCandidato.objects.create(
        envio_email=envio_email,
        nome="Fulano",
        rf="1234567",
        email="fulano@test.com",
        status=ENVIO_STATUS_SUCESSO,
        conteudo="<p>Conteúdo email 1</p>",
    )
    EnvioEmailCandidato.objects.create(
        envio_email=envio_email,
        nome="Ciclano",
        rf="7654321",
        email="ciclano@test.com",
        status=ENVIO_STATUS_ERRO,
        conteudo="<p>Conteúdo email 2</p>",
    )
    return list(envio_email.candidatos.all())


def test_envio_email_serializer_fields(envio_email):
    """Testa os campos do EnvioEmailSerializer."""
    serializer = EnvioEmailSerializer(envio_email)
    data = serializer.data
    assert data["uuid"] == str(envio_email.uuid)
    assert data["processo_nome"] == envio_email.processo_nome
    assert data["processo_uuid"] == str(envio_email.processo_uuid)
    assert data["tipo"] == TIPO_CONVOCACAO
    assert "criado_em" in data
    assert data["quantidade_candidatos"] == envio_email.quantidade_candidatos


def test_envio_email_candidato_serializer_fields(envio_email_candidatos):
    """Testa os campos do EnvioEmailCandidatoSerializer."""
    dest = envio_email_candidatos[0]
    serializer = EnvioEmailCandidatoSerializer(dest)
    data = serializer.data
    assert data["nome"] == dest.nome
    assert data["rf"] == dest.rf
    assert data["email"] == dest.email
    assert data["status"] == dest.status
    assert data["conteudo"] == dest.conteudo


def test_envio_email_detalhe_serializer_fields(envio_email, envio_email_candidatos):
    """Testa os campos do EnvioEmailDetalheSerializer incluindo candidatos."""
    serializer = EnvioEmailDetalheSerializer(envio_email)
    data = serializer.data
    assert data["uuid"] == str(envio_email.uuid)
    assert data["processo_nome"] == envio_email.processo_nome
    assert data["quantidade_candidatos"] == envio_email.quantidade_candidatos
    assert "candidatos" in data
    assert len(data["candidatos"]) == 2
    nomes = [c["nome"] for c in data["candidatos"]]
    assert "Fulano" in nomes
    assert "Ciclano" in nomes


def test_envio_email_envio_serializer_valid(processo_convocacao):
    """Testa EnvioEmailEnvioSerializer com dados válidos."""
    data = {
        "processo_uuid": str(processo_convocacao.uuid),
        "processo_nome": "Processo Teste",
        "tipo": TIPO_CONVOCACAO,
        "data_publicacao": "25-12-2024",
    }
    serializer = EnvioEmailEnvioSerializer(data=data)
    assert serializer.is_valid()
    assert serializer.validated_data["processo_nome"] == "Processo Teste"
    assert serializer.validated_data["processo_uuid"] == processo_convocacao.uuid


def test_envio_email_envio_serializer_processo_nao_encontrado():
    """Testa EnvioEmailEnvioSerializer quando processo não existe."""
    data = {
        "processo_uuid": str(uuid.uuid4()),
        "processo_nome": "Processo Inexistente",
        "tipo": TIPO_CONVOCACAO,
        "data_publicacao": "25-12-2024",
    }
    serializer = EnvioEmailEnvioSerializer(data=data)
    assert not serializer.is_valid()
    assert "processo_uuid" in serializer.errors


def test_envio_email_envio_serializer_convocacao_sem_data_publicacao(processo_convocacao):
    """Convocação exige data_publicacao."""
    data = {
        "processo_uuid": str(processo_convocacao.uuid),
        "processo_nome": "Processo Teste",
        "tipo": TIPO_CONVOCACAO,
    }
    serializer = EnvioEmailEnvioSerializer(data=data)
    assert not serializer.is_valid()
    assert "data_publicacao" in serializer.errors


def test_envio_email_envio_serializer_data_publicacao_invalida(processo_convocacao):
    """Testa formato de data_publicacao inválido."""
    data = {
        "processo_uuid": str(processo_convocacao.uuid),
        "processo_nome": "Processo Teste",
        "tipo": TIPO_CONVOCACAO,
        "data_publicacao": "2024-12-25",
    }
    serializer = EnvioEmailEnvioSerializer(data=data)
    assert not serializer.is_valid()
    assert "data_publicacao" in serializer.errors