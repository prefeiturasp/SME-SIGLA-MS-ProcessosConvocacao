"""
Testes unitários para as views do app processos usando pytest.
"""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from django.db.models import Q
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
def authenticated_client(user):
    """Fixture para cliente API autenticado."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


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
        data_convocacao=timezone.now() + timedelta(days=15),  # Data futura
    )


@pytest.fixture
def cargos_processo(processo_convocacao):
    """Fixture para criar cargos para o processo."""
    cargos = []
    nomes = ["Analista de Sistemas", "Desenvolvedor Backend"]

    for nome in nomes:
        cargo = CargoProcesso.objects.create(
            processo=processo_convocacao,
            nome=nome,
            cargo_uuid=uuid.uuid4()  # Adicionar cargo_uuid
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
        nome="Analista de Sistemas",
        cargo_uuid=uuid.uuid4()  # Adicionar cargo_uuid
    )


@pytest.fixture
def processo_permissao(user):
    """Fixture para processo de teste de permissões."""
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Permissões",
        descricao="Descrição para teste de permissões",
        tipo_escolha='Nova Autorização',
        status='EM_ANDAMENTO',
        data_convocacao=timezone.now() + timedelta(days=20)
    )


@pytest.fixture
def processo_lista(user):
    """Fixture para processo de teste para listagem."""
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Lista",
        descricao="Descrição 2",
        tipo_escolha='Nova Autorização',
        status='EM_ANDAMENTO',
        data_convocacao=timezone.now() + timedelta(days=25)
    )


# Testes para ProcessoConvocacaoViewSet
def test_processo_convocacao_list(authenticated_client, processo_convocacao):
    """Testa a listagem de processos de convocação."""
    url = reverse('processoconvocacao-list')
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert 'results' in response.data
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['concurso_nome'] == processo_convocacao.concurso_nome


def test_processo_convocacao_create(authenticated_client):
    """Testa a criação de um processo de convocação."""
    url = reverse('processoconvocacao-list')
    data = {
        'concurso_uuid': str(uuid.uuid4()),
        'concurso_nome': 'Novo Concurso',
        'descricao': 'Descrição do novo processo',
        'tipo_escolha': 'Nova Autorização',
        'status': 'EM_ANDAMENTO',
        'data_convocacao': (timezone.now() + timedelta(days=30)).isoformat(),
        'cargos': [
            {'nome': 'Analista', 'cargo_uuid': str(uuid.uuid4())},
            {'nome': 'Desenvolvedor', 'cargo_uuid': str(uuid.uuid4())}
        ]
    }

    response = authenticated_client.post(url, data, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert ProcessoConvocacao.objects.count() == 1

    processo = ProcessoConvocacao.objects.first()
    assert processo.concurso_nome == 'Novo Concurso'
    assert processo.cargos_processo.count() == 2


def test_processo_convocacao_retrieve(authenticated_client, processo_convocacao):
    """Testa a recuperação de um processo específico."""
    url = reverse('processoconvocacao-detail', args=[processo_convocacao.uuid])
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data['concurso_nome'] == processo_convocacao.concurso_nome
    assert response.data['uuid'] == str(processo_convocacao.uuid)


def test_processo_convocacao_update(authenticated_client, processo_convocacao):
    """Testa a atualização de um processo."""
    url = reverse('processoconvocacao-detail', args=[processo_convocacao.uuid])
    data = {
        'concurso_nome': 'Concurso Atualizado',
        'descricao': 'Descrição atualizada',
        'status': 'FINALIZADO'
    }

    response = authenticated_client.patch(url, data, format='json')

    assert response.status_code == status.HTTP_200_OK
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.concurso_nome == 'Concurso Atualizado'
    assert processo_convocacao.status == 'FINALIZADO'


def test_processo_convocacao_delete(authenticated_client, processo_convocacao):
    """Testa a exclusão de um processo."""
    url = reverse('processoconvocacao-detail', args=[processo_convocacao.uuid])
    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert ProcessoConvocacao.objects.count() == 0


# Testes para filtros customizados
def test_filtro_data_convocacao_inicio(authenticated_client, processo_convocacao):
    """Testa filtro por data de convocação início."""
    url = reverse('processoconvocacao-list')

    # Data de início antes da data de convocação do processo
    data_inicio = (processo_convocacao.data_convocacao - timedelta(days=5)).strftime('%Y-%m-%d')
    response = authenticated_client.get(url, {'data_convocacao_inicio': data_inicio})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1


def test_filtro_data_convocacao_fim(authenticated_client, processo_convocacao):
    """Testa filtro por data de convocação fim."""
    url = reverse('processoconvocacao-list')

    # Data de fim após a data de convocação do processo
    data_fim = (processo_convocacao.data_convocacao + timedelta(days=5)).strftime('%Y-%m-%d')
    response = authenticated_client.get(url, {'data_convocacao_fim': data_fim})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1


def test_filtro_data_convocacao_range(authenticated_client, processo_convocacao):
    """Testa filtro por range de datas de convocação."""
    url = reverse('processoconvocacao-list')

    # Range que inclui a data de convocação do processo
    data_inicio = (processo_convocacao.data_convocacao - timedelta(days=5)).strftime('%Y-%m-%d')
    data_fim = (processo_convocacao.data_convocacao + timedelta(days=5)).strftime('%Y-%m-%d')

    response = authenticated_client.get(url, {
        'data_convocacao_inicio': data_inicio,
        'data_convocacao_fim': data_fim
    })

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1


def test_filtro_cargo_uuid(authenticated_client, processo_convocacao, cargos_processo):
    """Testa filtro por cargo_uuid."""
    url = reverse('processoconvocacao-list')

    # Usar o UUID do primeiro cargo
    cargo_uuid = cargos_processo[0].cargo_uuid

    response = authenticated_client.get(url, {'cargo_uuid': str(cargo_uuid)})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1


def test_filtro_data_invalida(authenticated_client):
    """Testa filtro com data inválida."""
    url = reverse('processoconvocacao-list')

    response = authenticated_client.get(url, {'data_convocacao_inicio': 'data-invalida'})

    assert response.status_code == status.HTTP_200_OK
    # Deve retornar lista vazia devido ao tratamento de erro
    assert len(response.data['results']) == 0


def test_filtro_cargo_uuid_invalido(authenticated_client):
    """Testa filtro com cargo_uuid inválido."""
    url = reverse('processoconvocacao-list')

    response = authenticated_client.get(url, {'cargo_uuid': 'uuid-invalido'})

    assert response.status_code == status.HTTP_200_OK
    # Deve retornar lista vazia devido ao tratamento de erro
    assert len(response.data['results']) == 0


# Testes para o endpoint /filtros/
def test_endpoint_filtros_basic(authenticated_client, processo_convocacao, cargos_processo):
    """Testa o endpoint /filtros/ com dados básicos."""
    url = reverse('processoconvocacao-filtros')
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert 'concursos' in response.data
    assert 'cargos' in response.data
    assert 'tipos_processos' in response.data

    # Verificar estrutura dos concursos
    concursos = response.data['concursos']
    assert len(concursos) == 1
    assert 'value' in concursos[0]
    assert 'label' in concursos[0]
    assert concursos[0]['value'] == processo_convocacao.concurso_uuid
    assert concursos[0]['label'] == processo_convocacao.concurso_nome

    # Verificar estrutura dos cargos
    cargos = response.data['cargos']
    assert len(cargos) == 2
    for cargo in cargos:
        assert 'value' in cargo
        assert 'label' in cargo
        assert cargo['value'] is not None
        assert cargo['label'] is not None

    # Verificar estrutura dos tipos de processo
    tipos_processos = response.data['tipos_processos']
    assert len(tipos_processos) == 3  # CONVOCACAO, SELECAO, AVALIACAO
    for tipo in tipos_processos:
        assert 'value' in tipo
        assert 'label' in tipo
        assert tipo['value'] in ['Nova Autorização', 'SELECAO', 'AVALIACAO']
        assert tipo['label'] in ['Convocação', 'Seleção', 'Avaliação']


def test_endpoint_filtros_multiplos_processos(authenticated_client, user):
    """Testa o endpoint /filtros/ com múltiplos processos."""
    # Criar múltiplos processos com concursos diferentes
    processo1 = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso A",
        descricao="Descrição A",
        tipo_escolha='Nova Autorização',
        status='EM_ANDAMENTO',
        data_convocacao=timezone.now() + timedelta(days=10)
    )

    processo2 = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso B",
        descricao="Descrição B",
        tipo_escolha='Nova Autorização',
        status='EM_ANDAMENTO',
        data_convocacao=timezone.now() + timedelta(days=15)
    )

    # Criar cargos para cada processo
    CargoProcesso.objects.create(
        processo=processo1,
        nome="Analista A",
        cargo_uuid=uuid.uuid4()
    )

    CargoProcesso.objects.create(
        processo=processo2,
        nome="Analista B",
        cargo_uuid=uuid.uuid4()
    )

    url = reverse('processoconvocacao-filtros')
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert 'tipos_processos' in response.data

    # Verificar que há 2 concursos únicos
    concursos = response.data['concursos']
    assert len(concursos) == 2

    # Verificar que há 2 cargos únicos
    cargos = response.data['cargos']
    assert len(cargos) == 2

    # Verificar tipos de processo
    tipos_processos = response.data['tipos_processos']
    assert len(tipos_processos) == 3


def test_endpoint_filtros_concurso_duplicado(authenticated_client, user):
    """Testa que concursos duplicados são removidos no endpoint /filtros/."""
    # Criar dois processos com o mesmo concurso
    concurso_uuid = uuid.uuid4()
    concurso_nome = "Concurso Duplicado"

    processo1 = ProcessoConvocacao.objects.create(
        concurso_uuid=concurso_uuid,
        concurso_nome=concurso_nome,
        descricao="Descrição 1",
        tipo_escolha='Nova Autorização',
        status='EM_ANDAMENTO',
        data_convocacao=timezone.now() + timedelta(days=10)
    )

    processo2 = ProcessoConvocacao.objects.create(
        concurso_uuid=concurso_uuid,  # Mesmo UUID
        concurso_nome=concurso_nome,  # Mesmo nome
        descricao="Descrição 2",
        tipo_escolha='Nova Autorização',
        status='EM_ANDAMENTO',
        data_convocacao=timezone.now() + timedelta(days=15)
    )

    url = reverse('processoconvocacao-filtros')
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK

    # Deve haver apenas 1 concurso único
    concursos = response.data['concursos']
    assert len(concursos) == 1
    assert concursos[0]['value'] == concurso_uuid
    assert concursos[0]['label'] == concurso_nome


def test_endpoint_filtros_cargo_duplicado(authenticated_client, user):
    """Testa que cargos com nomes duplicados são removidos no endpoint /filtros/."""
    # Criar dois processos
    processo1 = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso 1",
        descricao="Descrição 1",
        tipo_escolha='Nova Autorização',
        status='EM_ANDAMENTO',
        data_convocacao=timezone.now() + timedelta(days=10)
    )

    processo2 = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso 2",
        descricao="Descrição 2",
        tipo_escolha='Nova Autorização',
        status='EM_ANDAMENTO',
        data_convocacao=timezone.now() + timedelta(days=15)
    )

    # Criar cargos com o mesmo nome em processos diferentes
    cargo_nome = "Analista"

    CargoProcesso.objects.create(
        processo=processo1,
        nome=cargo_nome,
        cargo_uuid=uuid.uuid4()
    )

    CargoProcesso.objects.create(
        processo=processo2,
        nome=cargo_nome,  # Mesmo nome
        cargo_uuid=uuid.uuid4()
    )

    url = reverse('processoconvocacao-filtros')
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK

    # Deve haver apenas 1 cargo único (por nome)
    cargos = response.data['cargos']
    assert len(cargos) == 1
    assert cargos[0]['label'] == cargo_nome


def test_endpoint_filtros_sem_dados(authenticated_client):
    """Testa o endpoint /filtros/ quando não há dados."""
    url = reverse('processoconvocacao-filtros')
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert 'concursos' in response.data
    assert 'cargos' in response.data
    assert 'tipos_processos' in response.data

    # Deve retornar listas vazias para concursos e cargos
    assert len(response.data['concursos']) == 0
    assert len(response.data['cargos']) == 0

    # Tipos de processo devem sempre estar presentes (vêm dos choices)
    assert len(response.data['tipos_processos']) == 3


def test_endpoint_filtros_tipos_processo(authenticated_client):
    """Testa que os tipos de processo são retornados corretamente."""
    url = reverse('processoconvocacao-filtros')
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert 'tipos_processos' in response.data

    tipos_processos = response.data['tipos_processos']
    assert len(tipos_processos) == 3

    # Verificar que todos os tipos esperados estão presentes
    tipos_esperados = {
        'Nova Autorização': 'Convocação',
        'SELECAO': 'Seleção',
        'AVALIACAO': 'Avaliação'
    }

    for tipo in tipos_processos:
        assert tipo['value'] in tipos_esperados
        assert tipo['label'] == tipos_esperados[tipo['value']]
        assert 'value' in tipo
        assert 'label' in tipo


# Testes de Filtros e Ordenação
def test_processo_convocacao_filters(authenticated_client, processo_convocacao):
    """Testa filtros básicos dos processos."""
    url = reverse('processoconvocacao-list')

    # Filtro por status
    response = authenticated_client.get(url, {'status': 'EM_ANDAMENTO'})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1

    # Filtro por tipo_escolha
    response = authenticated_client.get(url, {'tipo_escolha': 'Nova Autorização'})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1

    # Filtro por concurso_uuid
    response = authenticated_client.get(url, {'concurso_uuid': str(processo_convocacao.concurso_uuid)})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1


# Testes de Busca
def test_processo_convocacao_search(authenticated_client, processo_convocacao):
    """Testa busca por texto nos processos."""
    url = reverse('processoconvocacao-list')

    # Busca por nome do concurso
    response = authenticated_client.get(url, {'search': 'Concurso'})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1

    # Busca por descrição
    response = authenticated_client.get(url, {'search': 'Descrição'})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data['results']) == 1
