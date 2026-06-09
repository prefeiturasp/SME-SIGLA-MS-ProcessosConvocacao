"""Configuração para testes do app processos."""

import uuid

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient

from ..models import CargoProcesso, ProcessoConvocacao


@pytest.fixture
def user():
    """Fixture para criar um usuário de teste.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return User.objects.create_user(
        username="testuser", password="testpass123"
    )


@pytest.fixture
def admin_user():
    """Fixture para criar um usuário admin de teste.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return User.objects.create_superuser(
        username="admin", email="admin@test.com", password="adminpass123"
    )


@pytest.fixture
def processo_convocacao(user):
    """Fixture para criar um processo de convocação de teste.
    
    Args:
        user: Parâmetro user da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Teste",
        descricao="Descrição do processo teste",
        tipo_escolha="Nova Autorização",
        status="EM_ANDAMENTO",
        data_convocacao=timezone.now(),
        data_corte_vagas=timezone.now(),
    )


@pytest.fixture
def cargo_processo(processo_convocacao):
    """Fixture para criar um cargo de teste.
    
    Args:
        processo_convocacao: Parâmetro processo convocacao da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Analista de Sistemas",
        cargo_uuid=uuid.uuid4(),
    )


@pytest.fixture
def processo_com_cargos(processo_convocacao):
    """Fixture para criar um processo com múltiplos cargos.
    
    Args:
        processo_convocacao: Parâmetro processo convocacao da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    cargos = [
        "Analista de Sistemas",
        "Desenvolvedor Backend",
        "Desenvolvedor Frontend",
    ]

    for nome in cargos:
        CargoProcesso.objects.create(
            processo=processo_convocacao,
            cargo_nome=nome,
            cargo_uuid=uuid.uuid4(),
        )

    return processo_convocacao


@pytest.fixture
def processos_multiplos(user):
    """Fixture para criar múltiplos processos de teste.
    
    Args:
        user: Parâmetro user da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    processos = []

    for i in range(3):
        processo = ProcessoConvocacao.objects.create(
            concurso_uuid=uuid.uuid4(),
            concurso_nome=f"Concurso Teste {i+1}",
            descricao=f"Descrição do processo teste {i+1}",
            tipo_escolha="Nova Autorização",
            status="EM_ANDAMENTO",
            data_convocacao=timezone.now(),
            data_corte_vagas=timezone.now(),
        )

        # Adicionar cargos para cada processo
        for j in range(2):
            CargoProcesso.objects.create(
                processo=processo,
                cargo_nome=f"Cargo {j+1} do Processo {i+1}",
                cargo_uuid=uuid.uuid4(),
            )

        processos.append(processo)

    return processos


@pytest.fixture
def processo_finalizado(user):
    """Fixture para criar um processo finalizado.
    
    Args:
        user: Parâmetro user da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Finalizado",
        descricao="Processo já finalizado",
        tipo_escolha="Reposição",
        status="FINALIZADO",
        data_convocacao=timezone.now(),
        data_corte_vagas=timezone.now(),
    )


@pytest.fixture
def processo_cancelado(user):
    """Fixture para criar um processo cancelado.
    
    Args:
        user: Parâmetro user da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Cancelado",
        descricao="Processo cancelado",
        tipo_escolha="Reconvocação",
        status="CANCELADO",
        data_convocacao=timezone.now(),
        data_corte_vagas=timezone.now(),
    )


@pytest.fixture
def processo_selecao(user):
    """Fixture para criar um processo de seleção.
    
    Args:
        user: Parâmetro user da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Processo de Seleção",
        descricao="Processo seletivo",
        tipo_escolha="Reposição",
        status="EM_ANDAMENTO",
        data_convocacao=timezone.now(),
        data_corte_vagas=timezone.now(),
    )


@pytest.fixture
def processo_avaliacao(user):
    """Fixture para criar um processo de avaliação.
    
    Args:
        user: Parâmetro user da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Processo de Avaliação",
        descricao="Processo de avaliação técnica",
        tipo_escolha="Reconvocação",
        status="EM_ANDAMENTO",
        data_convocacao=timezone.now(),
        data_corte_vagas=timezone.now(),
    )


@pytest.fixture
def authenticated_client(user):
    """Fixture para cliente API autenticado.
    
    Args:
        user: Parâmetro user da operação.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    client = APIClient()
    client.force_authenticate(user=user)
    return client
