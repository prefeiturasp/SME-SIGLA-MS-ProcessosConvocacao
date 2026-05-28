"""
Testes unitários para as views do app processos usando pytest.
"""

import uuid
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from ..models import (
    CargoProcesso,
    EnvioEmail,
    EnvioEmailCandidato,
    ProcessoConvocacao,
)
from ..models.constants import (
    ERROR_CANDIDATOS_PENDENTES_ESCOLHA,
    ERROR_PROCESSO_JA_CANCELADO,
    ERROR_PROCESSO_JA_FINALIZADO,
    ERROR_PROCESSO_NAO_PODE_EDITAR,
)
from ..models.envio_email import TIPO_CONVOCACAO

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
            cargo_nome=nome,
            cargo_uuid=uuid.uuid4(),
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
        tipo_escolha="NOVA_AUTORIZACAO",
        status="EM_ANDAMENTO",
        data_convocacao=timezone.now() + timedelta(days=10),
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
def processo_permissao(user):
    """Fixture para processo de teste de permissões."""
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Permissões",
        descricao="Descrição para teste de permissões",
        tipo_escolha="NOVA_AUTORIZACAO",
        status="EM_ANDAMENTO",
        data_convocacao=timezone.now() + timedelta(days=20),
    )


@pytest.fixture
def processo_lista(user):
    """Fixture para processo de teste para listagem."""
    return ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso Lista",
        descricao="Descrição 2",
        tipo_escolha="NOVA_AUTORIZACAO",
        status="EM_ANDAMENTO",
        data_convocacao=timezone.now() + timedelta(days=25),
    )


# Testes para ProcessoConvocacaoViewSet
def test_processo_convocacao_list(authenticated_client, processo_convocacao):
    """Testa a listagem de processos de convocação."""
    url = reverse("processoconvocacao-list")
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "results" in response.data
    assert len(response.data["results"]) == 1
    assert (
        response.data["results"][0]["concurso_nome"]
        == processo_convocacao.concurso_nome
    )


def test_processo_convocacao_create(authenticated_client):
    """Testa a criação de um processo de convocação."""
    url = reverse("processoconvocacao-list")
    data = {
        "concurso_uuid": str(uuid.uuid4()),
        "concurso_nome": "Novo Concurso",
        "descricao": "Descrição do novo processo",
        "tipo_escolha": "NOVA_AUTORIZACAO",
        "status": "EM_ANDAMENTO",
        "data_convocacao": (timezone.now() + timedelta(days=30)).isoformat(),
        "data_corte_vagas": (timezone.now() + timedelta(days=5)).isoformat(),
    }

    response = authenticated_client.post(url, data, format="json")

    assert response.status_code == status.HTTP_201_CREATED
    assert ProcessoConvocacao.objects.count() == 1

    processo = ProcessoConvocacao.objects.first()
    assert processo.concurso_nome == "Novo Concurso"


def test_processo_convocacao_retrieve(
    authenticated_client, processo_convocacao
):
    """Testa a recuperação de um processo específico."""
    url = reverse("processoconvocacao-detail", args=[processo_convocacao.uuid])
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["concurso_nome"] == processo_convocacao.concurso_nome
    assert response.data["uuid"] == str(processo_convocacao.uuid)


def test_processo_convocacao_update(authenticated_client, processo_convocacao):
    """Testa a atualização de um processo."""
    url = reverse("processoconvocacao-detail", args=[processo_convocacao.uuid])
    data = {
        "concurso_nome": "Concurso Atualizado",
        "descricao": "Descrição atualizada",
        "status": "FINALIZADO",
    }

    response = authenticated_client.patch(url, data, format="json")

    assert response.status_code == status.HTTP_200_OK
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.concurso_nome == "Concurso Atualizado"
    assert processo_convocacao.status == "FINALIZADO"


@patch(
    "processos.views.processos.ProcessoConvocacaoService.excluir_processo_e_dependencias"
)
def test_processo_convocacao_delete(
    mock_excluir_dependencias,
    authenticated_client,
    processo_convocacao,
):
    """Testa a exclusão lógica de um processo."""
    # Para poder deletar, o status não pode ser EM_ANDAMENTO nem FINALIZADO
    processo_convocacao.status = "CANCELADO"
    processo_convocacao.save(update_fields=["status"])

    def _excluir_e_inativar(*, processo, auth_header=None):
        processo.inativar()

    mock_excluir_dependencias.side_effect = _excluir_e_inativar

    url = reverse("processoconvocacao-detail", args=[processo_convocacao.uuid])
    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.esta_ativo is False


def test_filtro_data_convocacao_inicio(
    authenticated_client, processo_convocacao
):
    """Testa filtro por data de convocação início."""
    url = reverse("processoconvocacao-list")

    # Data de início antes da data de convocação do processo
    data_inicio = (
        processo_convocacao.data_convocacao - timedelta(days=5)
    ).strftime("%Y-%m-%d")
    response = authenticated_client.get(
        url, {"data_convocacao_inicio": data_inicio}
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1


def test_filtro_data_convocacao_fim(authenticated_client, processo_convocacao):
    """Testa filtro por data de convocação fim."""
    url = reverse("processoconvocacao-list")

    # Data de fim após a data de convocação do processo
    data_fim = (
        processo_convocacao.data_convocacao + timedelta(days=5)
    ).strftime("%Y-%m-%d")
    response = authenticated_client.get(url, {"data_convocacao_fim": data_fim})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1


def test_filtro_data_convocacao_range(
    authenticated_client, processo_convocacao
):
    """Testa filtro por range de datas de convocação."""
    url = reverse("processoconvocacao-list")

    # Range que inclui a data de convocação do processo
    data_inicio = (
        processo_convocacao.data_convocacao - timedelta(days=5)
    ).strftime("%Y-%m-%d")
    data_fim = (
        processo_convocacao.data_convocacao + timedelta(days=5)
    ).strftime("%Y-%m-%d")

    response = authenticated_client.get(
        url,
        {
            "data_convocacao_inicio": data_inicio,
            "data_convocacao_fim": data_fim,
        },
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1


def test_filtro_cargo_uuid(
    authenticated_client, processo_convocacao, cargos_processo
):
    """Testa filtro por cargo_uuid."""
    url = reverse("processoconvocacao-list")

    # Usar o UUID do primeiro cargo
    cargo_uuid = cargos_processo[0].cargo_uuid

    response = authenticated_client.get(url, {"cargo_uuid": str(cargo_uuid)})

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1


def test_filtro_data_invalida(authenticated_client):
    """Testa filtro com data inválida."""
    url = reverse("processoconvocacao-list")

    response = authenticated_client.get(
        url, {"data_convocacao_inicio": "data-invalida"}
    )

    assert response.status_code == status.HTTP_200_OK
    # Deve retornar lista vazia devido ao tratamento de erro
    assert len(response.data["results"]) == 0


def test_filtro_cargo_uuid_invalido(authenticated_client):
    """Testa filtro com cargo_uuid inválido."""
    url = reverse("processoconvocacao-list")

    response = authenticated_client.get(url, {"cargo_uuid": "uuid-invalido"})

    assert response.status_code == status.HTTP_200_OK
    # Deve retornar lista vazia devido ao tratamento de erro
    assert len(response.data["results"]) == 0


# Testes para CargoProcessoViewSet
def test_cargos_list_sucesso(
    authenticated_client, processo_convocacao, cargos_processo
):
    """Lista cargos do processo com sucesso."""
    url = reverse(
        "processo-cargos-list",
        kwargs={"processo_pk": processo_convocacao.uuid},
    )
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2
    nomes = [c["cargo_nome"] for c in response.data]
    assert "Analista de Sistemas" in nomes
    assert "Desenvolvedor Backend" in nomes


def test_cargos_list_processo_nao_encontrado(authenticated_client):
    """Retorna 404 quando processo não existe."""
    url = reverse("processo-cargos-list", kwargs={"processo_pk": uuid.uuid4()})
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["error"] == "Processo de convocação não encontrado"


def test_cargos_create_novos_cargos(authenticated_client, processo_convocacao):
    """POST cria novos cargos quando payload não tem uuid."""
    url = reverse(
        "processo-cargos-list",
        kwargs={"processo_pk": processo_convocacao.uuid},
    )
    payload = {
        "porcentagem_nna": 0.2,
        "porcentagem_pcd": 0.05,
        "cargos": [
            {"cargo_nome": "Cargo Novo 1", "cargo_uuid": str(uuid.uuid4())},
            {"cargo_nome": "Cargo Novo 2", "cargo_uuid": str(uuid.uuid4())},
        ],
    }
    response = authenticated_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["success"] is True
    assert response.data["cargos_criados"] == 2
    assert response.data["cargos_atualizados"] == 0
    assert response.data["cargos_removidos"] == 0
    assert len(response.data["cargos"]) == 2


def test_cargos_create_atualiza_existentes(
    authenticated_client, processo_convocacao, cargos_processo
):
    """POST atualiza cargos existentes quando payload tem uuid."""
    cargo = cargos_processo[0]
    url = reverse(
        "processo-cargos-list",
        kwargs={"processo_pk": processo_convocacao.uuid},
    )
    payload = {
        "cargos": [
            {
                "uuid": str(cargo.uuid),
                "cargo_nome": "Analista Atualizado",
                "cargo_uuid": str(cargo.cargo_uuid),
            },
        ]
    }
    response = authenticated_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["cargos_criados"] == 0
    assert response.data["cargos_atualizados"] == 1
    assert (
        response.data["cargos_removidos"] == 1
    )  # o segundo cargo foi removido
    cargo.refresh_from_db()
    assert cargo.cargo_nome == "Analista Atualizado"


def test_cargos_create_remove_cargos_nao_enviados(
    authenticated_client, processo_convocacao, cargos_processo
):
    """POST remove cargos que não estão no payload."""
    cargo = cargos_processo[0]
    url = reverse(
        "processo-cargos-list",
        kwargs={"processo_pk": processo_convocacao.uuid},
    )
    payload = {
        "cargos": [
            {
                "uuid": str(cargo.uuid),
                "cargo_nome": cargo.cargo_nome,
                "cargo_uuid": str(cargo.cargo_uuid),
            },
        ]
    }
    response = authenticated_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["cargos_removidos"] == 1
    assert (
        CargoProcesso.objects.filter(processo=processo_convocacao).count() == 1
    )


def test_cargos_create_processo_nao_encontrado(authenticated_client):
    """POST retorna 404 quando processo não existe."""
    url = reverse("processo-cargos-list", kwargs={"processo_pk": uuid.uuid4()})
    response = authenticated_client.post(url, {"cargos": []}, format="json")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["error"] == "Processo de convocação não encontrado"


def test_cargos_create_processo_finalizado(
    authenticated_client, processo_convocacao
):
    """POST retorna 400 quando processo está finalizado."""
    processo_convocacao.status = "FINALIZADO"
    processo_convocacao.save()

    url = reverse(
        "processo-cargos-list",
        kwargs={"processo_pk": processo_convocacao.uuid},
    )
    response = authenticated_client.post(
        url,
        {"cargos": [{"cargo_nome": "Cargo", "cargo_uuid": str(uuid.uuid4())}]},
        format="json",
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["detail"] == ERROR_PROCESSO_NAO_PODE_EDITAR


def test_cargos_create_payload_nao_e_lista(
    authenticated_client, processo_convocacao
):
    """POST retorna 400 quando payload é lista (espera dict com chave
    cargos)."""
    url = reverse(
        "processo-cargos-list",
        kwargs={"processo_pk": processo_convocacao.uuid},
    )
    response = authenticated_client.post(
        url, [{"cargo_nome": "Cargo"}], format="json"
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "non_field_errors" in response.data


def test_cargos_create_uuid_nao_encontrado_retorna_207(
    authenticated_client, processo_convocacao, cargos_processo
):
    """POST com uuid de cargo inexistente retorna 207 com erros."""
    url = reverse(
        "processo-cargos-list",
        kwargs={"processo_pk": processo_convocacao.uuid},
    )
    payload = {
        "cargos": [
            {
                "uuid": str(uuid.uuid4()),
                "cargo_nome": "Inexistente",
                "cargo_uuid": str(uuid.uuid4()),
            },
        ]
    }
    response = authenticated_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_207_MULTI_STATUS
    assert response.data["success"] is True
    assert "erros" in response.data
    assert len(response.data["erros"]) == 1
    assert (
        response.data["erros"][0]["erros"]
        == "Cargo não encontrado para este processo"
    )


def test_cargos_destroy_sucesso(
    authenticated_client, processo_cargo, cargo_processo
):
    """DELETE remove cargo do processo."""
    url = reverse(
        "processo-cargos-detail",
        kwargs={
            "processo_pk": processo_cargo.uuid,
            "cargo_uuid": cargo_processo.uuid,
        },
    )
    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not CargoProcesso.objects.filter(uuid=cargo_processo.uuid).exists()


def test_cargos_destroy_processo_nao_encontrado(
    authenticated_client, cargo_processo
):
    """DELETE retorna 404 quando processo não existe."""
    processo_inexistente = uuid.uuid4()
    url = reverse(
        "processo-cargos-detail",
        kwargs={
            "processo_pk": processo_inexistente,
            "cargo_uuid": cargo_processo.uuid,
        },
    )
    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["error"] == "Processo de convocação não encontrado"


def test_cargos_destroy_processo_finalizado(
    authenticated_client, processo_cargo, cargo_processo
):
    """DELETE retorna 400 quando processo está finalizado."""
    processo_cargo.status = "FINALIZADO"
    processo_cargo.save()

    url = reverse(
        "processo-cargos-detail",
        kwargs={
            "processo_pk": processo_cargo.uuid,
            "cargo_uuid": cargo_processo.uuid,
        },
    )
    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["detail"] == ERROR_PROCESSO_NAO_PODE_EDITAR


def test_cargos_destroy_cargo_nao_encontrado(
    authenticated_client, processo_convocacao
):
    """DELETE retorna 404 quando cargo não pertence ao processo."""
    cargo_uuid_outro_processo = uuid.uuid4()
    url = reverse(
        "processo-cargos-detail",
        kwargs={
            "processo_pk": processo_convocacao.uuid,
            "cargo_uuid": cargo_uuid_outro_processo,
        },
    )
    response = authenticated_client.delete(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.data["error"] == "Cargo não encontrado para este processo"


# Testes para o endpoint /filtros/
def test_endpoint_filtros_basic(
    authenticated_client, processo_convocacao, cargos_processo
):
    """Testa o endpoint /filtros/ com dados básicos."""
    url = reverse("processoconvocacao-filtros")
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "concursos" in response.data
    assert "cargos" in response.data
    assert "tipos_escolha" in response.data

    # Verificar estrutura dos concursos
    concursos = response.data["concursos"]
    assert len(concursos) == 1
    assert "value" in concursos[0]
    assert "label" in concursos[0]
    assert concursos[0]["value"] == processo_convocacao.concurso_uuid
    assert concursos[0]["label"] == processo_convocacao.concurso_nome

    # Verificar estrutura dos cargos
    cargos = response.data["cargos"]
    assert len(cargos) == 2
    for cargo in cargos:
        assert "value" in cargo
        assert "label" in cargo
        assert cargo["value"] is not None
        assert cargo["label"] is not None

    # Verificar estrutura dos tipos de escolha
    tipos_escolha = response.data["tipos_escolha"]
    assert len(tipos_escolha) == 3
    for tipo in tipos_escolha:
        assert "value" in tipo
        assert "label" in tipo
        assert tipo["value"] in ["NOVA_AUTORIZACAO", "REPOSICAO", "RECONVOCAO"]
        assert tipo["label"] in [
            "Nova Autorização",
            "Reposição",
            "Reconvocação",
        ]


def test_endpoint_filtros_multiplos_processos(authenticated_client, user):
    """Testa o endpoint /filtros/ com múltiplos processos."""
    # Criar múltiplos processos com concursos diferentes
    processo1 = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso A",
        descricao="Descrição A",
        tipo_escolha="NOVA_AUTORIZACAO",
        status="EM_ANDAMENTO",
        data_convocacao=timezone.now() + timedelta(days=10),
    )

    processo2 = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso B",
        descricao="Descrição B",
        tipo_escolha="NOVA_AUTORIZACAO",
        status="EM_ANDAMENTO",
        data_convocacao=timezone.now() + timedelta(days=15),
    )

    # Criar cargos para cada processo
    CargoProcesso.objects.create(
        processo=processo1, cargo_nome="Analista A", cargo_uuid=uuid.uuid4()
    )

    CargoProcesso.objects.create(
        processo=processo2, cargo_nome="Analista B", cargo_uuid=uuid.uuid4()
    )

    url = reverse("processoconvocacao-filtros")
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "tipos_escolha" in response.data

    # Verificar que há 2 concursos únicos
    concursos = response.data["concursos"]
    assert len(concursos) == 2

    # Verificar que há 2 cargos únicos
    cargos = response.data["cargos"]
    assert len(cargos) == 2

    # Verificar tipos de escolha
    tipos_escolha = response.data["tipos_escolha"]
    assert len(tipos_escolha) == 3


def test_endpoint_filtros_concurso_duplicado(authenticated_client, user):
    """Testa que concursos duplicados são removidos no endpoint /filtros/."""
    # Criar dois processos com o mesmo concurso
    concurso_uuid = uuid.uuid4()
    concurso_nome = "Concurso Duplicado"

    ProcessoConvocacao.objects.create(
        concurso_uuid=concurso_uuid,
        concurso_nome=concurso_nome,
        descricao="Descrição 1",
        tipo_escolha="NOVA_AUTORIZACAO",
        status="EM_ANDAMENTO",
        data_convocacao=timezone.now() + timedelta(days=10),
    )

    ProcessoConvocacao.objects.create(
        concurso_uuid=concurso_uuid,  # Mesmo UUID
        concurso_nome=concurso_nome,  # Mesmo nome
        descricao="Descrição 2",
        tipo_escolha="NOVA_AUTORIZACAO",
        status="EM_ANDAMENTO",
        data_convocacao=timezone.now() + timedelta(days=15),
    )

    url = reverse("processoconvocacao-filtros")
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK

    # Deve haver apenas 1 concurso único
    concursos = response.data["concursos"]
    assert len(concursos) == 1
    assert concursos[0]["value"] == concurso_uuid
    assert concursos[0]["label"] == concurso_nome


def test_endpoint_filtros_cargo_duplicado(authenticated_client, user):
    """Testa que cargos com nomes duplicados são removidos no endpoint
    /filtros/."""
    # Criar dois processos
    processo1 = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso 1",
        descricao="Descrição 1",
        tipo_escolha="NOVA_AUTORIZACAO",
        status="EM_ANDAMENTO",
        data_convocacao=timezone.now() + timedelta(days=10),
    )

    processo2 = ProcessoConvocacao.objects.create(
        concurso_uuid=uuid.uuid4(),
        concurso_nome="Concurso 2",
        descricao="Descrição 2",
        tipo_escolha="NOVA_AUTORIZACAO",
        status="EM_ANDAMENTO",
        data_convocacao=timezone.now() + timedelta(days=15),
    )

    # Criar cargos com o mesmo nome em processos diferentes
    cargo_nome = "Analista"

    CargoProcesso.objects.create(
        processo=processo1, cargo_nome=cargo_nome, cargo_uuid=uuid.uuid4()
    )

    CargoProcesso.objects.create(
        processo=processo2,
        cargo_nome=cargo_nome,  # Mesmo nome
        cargo_uuid=uuid.uuid4(),
    )

    url = reverse("processoconvocacao-filtros")
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK

    # Deve haver apenas 1 cargo único (por nome)
    cargos = response.data["cargos"]
    assert len(cargos) == 1
    assert cargos[0]["label"] == cargo_nome


def test_endpoint_filtros_sem_dados(authenticated_client):
    """Testa o endpoint /filtros/ quando não há dados."""
    url = reverse("processoconvocacao-filtros")
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "concursos" in response.data
    assert "cargos" in response.data
    assert "tipos_escolha" in response.data

    # Deve retornar listas vazias para concursos e cargos
    assert len(response.data["concursos"]) == 0
    assert len(response.data["cargos"]) == 0

    # Tipos de escolha devem sempre estar presentes (vêm dos choices)
    assert len(response.data["tipos_escolha"]) == 3


def test_endpoint_filtros_tipos_escolha(authenticated_client):
    """Testa que os tipos de escolha são retornados corretamente."""
    url = reverse("processoconvocacao-filtros")
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert "tipos_escolha" in response.data

    tipos_escolha = response.data["tipos_escolha"]
    assert len(tipos_escolha) == 3

    # Verificar que todos os tipos esperados estão presentes
    tipos_esperados = {
        "NOVA_AUTORIZACAO": "Nova Autorização",
        "REPOSICAO": "Reposição",
        "RECONVOCAO": "Reconvocação",
    }

    for tipo in tipos_escolha:
        assert tipo["value"] in tipos_esperados
        assert tipo["label"] == tipos_esperados[tipo["value"]]
        assert "value" in tipo
        assert "label" in tipo


# Testes para a action finalizar
@patch(
    "processos.views.processos.EscolhasApiService.buscar_candidatos_com_escolha"
)
def test_finalizar_sucesso_todos_com_escolha(
    mock_buscar, authenticated_client, processo_convocacao
):
    """Finaliza processo quando todos os candidatos fizeram escolha."""
    cand1 = uuid.uuid4()
    cand2 = uuid.uuid4()
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Cargo A",
        cargo_uuid=uuid.uuid4(),
        candidatos_uuids=[cand1, cand2],
    )
    mock_buscar.return_value = [str(cand1), str(cand2)]

    url = reverse(
        "processoconvocacao-finalizar", args=[processo_convocacao.uuid]
    )
    response = authenticated_client.post(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "FINALIZADO"
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.status == "FINALIZADO"
    mock_buscar.assert_called_once_with(str(processo_convocacao.concurso_uuid))


@patch(
    "processos.views.processos.EscolhasApiService.buscar_candidatos_com_escolha"
)
def test_finalizar_sucesso_sem_candidatos(
    mock_buscar, authenticated_client, processo_convocacao
):
    """Finaliza processo quando não há candidatos (habilitados vazio)."""
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Cargo A",
        cargo_uuid=uuid.uuid4(),
        candidatos_uuids=[],
    )
    mock_buscar.return_value = []

    url = reverse(
        "processoconvocacao-finalizar", args=[processo_convocacao.uuid]
    )
    response = authenticated_client.post(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "FINALIZADO"
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.status == "FINALIZADO"


def test_finalizar_ja_finalizado(authenticated_client, processo_convocacao):
    """Retorna 400 quando processo já está finalizado."""
    processo_convocacao.status = "FINALIZADO"
    processo_convocacao.save()

    url = reverse(
        "processoconvocacao-finalizar", args=[processo_convocacao.uuid]
    )
    response = authenticated_client.post(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["detail"] == ERROR_PROCESSO_JA_FINALIZADO
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.status == "FINALIZADO"


def test_finalizar_ja_cancelado(authenticated_client, processo_convocacao):
    """Retorna 400 quando processo está cancelado."""
    processo_convocacao.status = "CANCELADO"
    processo_convocacao.save()

    url = reverse(
        "processoconvocacao-finalizar", args=[processo_convocacao.uuid]
    )
    response = authenticated_client.post(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["detail"] == ERROR_PROCESSO_JA_CANCELADO
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.status == "CANCELADO"


def test_finalizar_status_nao_em_andamento(
    authenticated_client, processo_convocacao
):
    """Retorna 400 quando processo não está em andamento (status diferente de
    EM_ANDAMENTO)."""
    # Usa um status fora dos 3 principais para acionar a mensagem genérica
    processo_convocacao.status = "PENDENTE"
    processo_convocacao.save(update_fields=["status"])

    url = reverse(
        "processoconvocacao-finalizar", args=[processo_convocacao.uuid]
    )
    response = authenticated_client.post(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        "Apenas processos em andamento podem ser finalizados"
        in response.data["detail"]
    )


@patch(
    "processos.views.processos.EscolhasApiService.buscar_candidatos_com_escolha"
)
def test_finalizar_candidatos_pendentes(
    mock_buscar, authenticated_client, processo_convocacao
):
    """Retorna 400 quando existem candidatos sem escolha."""
    cand1 = uuid.uuid4()
    cand2 = uuid.uuid4()
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Cargo A",
        cargo_uuid=uuid.uuid4(),
        candidatos_uuids=[cand1, cand2],
    )
    # Apenas cand1 fez escolha; cand2 está pendente
    mock_buscar.return_value = [str(cand1)]

    url = reverse(
        "processoconvocacao-finalizar", args=[processo_convocacao.uuid]
    )
    response = authenticated_client.post(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["detail"] == ERROR_CANDIDATOS_PENDENTES_ESCOLHA
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.status == "EM_ANDAMENTO"


@patch(
    "processos.views.processos.EscolhasApiService.buscar_candidatos_com_escolha"
)
def test_finalizar_erro_ao_buscar_escolhas(
    mock_buscar, authenticated_client, processo_convocacao
):
    """Retorna 400 quando buscar_candidatos_com_escolha levanta exceção."""
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Cargo A",
        cargo_uuid=uuid.uuid4(),
        candidatos_uuids=[uuid.uuid4()],
    )
    mock_buscar.side_effect = Exception("Erro de conexão com MS-Escolha")

    url = reverse(
        "processoconvocacao-finalizar", args=[processo_convocacao.uuid]
    )
    response = authenticated_client.post(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        response.data["detail"] == "Erro ao consultar escolhas dos candidatos."
    )
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.status == "EM_ANDAMENTO"


@patch(
    "processos.views.processos.EscolhasApiService.buscar_candidatos_com_escolha"
)
def test_finalizar_multiplos_cargos_todos_com_escolha(
    mock_buscar, authenticated_client, processo_convocacao
):
    """Finaliza processo com múltiplos cargos quando todos fizeram escolha."""
    cand1 = uuid.uuid4()
    cand2 = uuid.uuid4()
    cand3 = uuid.uuid4()
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Cargo A",
        cargo_uuid=uuid.uuid4(),
        candidatos_uuids=[cand1, cand2],
    )
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Cargo B",
        cargo_uuid=uuid.uuid4(),
        candidatos_uuids=[cand3],
    )
    mock_buscar.return_value = [str(cand1), str(cand2), str(cand3)]

    url = reverse(
        "processoconvocacao-finalizar", args=[processo_convocacao.uuid]
    )
    response = authenticated_client.post(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == "FINALIZADO"
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.status == "FINALIZADO"


@patch(
    "processos.views.processos.EscolhasApiService.buscar_candidatos_com_escolha"
)
def test_finalizar_multiplos_cargos_um_pendente(
    mock_buscar, authenticated_client, processo_convocacao
):
    """Retorna 400 quando um cargo tem candidato pendente."""
    cand1 = uuid.uuid4()
    cand2 = uuid.uuid4()
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Cargo A",
        cargo_uuid=uuid.uuid4(),
        candidatos_uuids=[cand1],
    )
    CargoProcesso.objects.create(
        processo=processo_convocacao,
        cargo_nome="Cargo B",
        cargo_uuid=uuid.uuid4(),
        candidatos_uuids=[cand2],
    )
    mock_buscar.return_value = [str(cand1)]  # cand2 pendente

    url = reverse(
        "processoconvocacao-finalizar", args=[processo_convocacao.uuid]
    )
    response = authenticated_client.post(url)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data["detail"] == ERROR_CANDIDATOS_PENDENTES_ESCOLHA


# Testes de Filtros e Ordenação
def test_processo_convocacao_filters(
    authenticated_client, processo_convocacao
):
    """Testa filtros básicos dos processos."""
    url = reverse("processoconvocacao-list")

    # Filtro por status
    response = authenticated_client.get(url, {"status": "EM_ANDAMENTO"})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1

    # Filtro por tipo_escolha
    response = authenticated_client.get(
        url, {"tipo_escolha": "NOVA_AUTORIZACAO"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1

    # Filtro por concurso_uuid
    response = authenticated_client.get(
        url, {"concurso_uuid": str(processo_convocacao.concurso_uuid)}
    )
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1


def test_atualizar_passo_sucesso(authenticated_client, processo_convocacao):
    """Atualiza passo do processo com sucesso."""
    url = reverse(
        "processoconvocacao-atualizar-passo", args=[processo_convocacao.uuid]
    )
    response = authenticated_client.patch(url, {"passo": 2}, format="json")

    assert response.status_code == status.HTTP_200_OK
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.passo == 2


def test_atualizar_passo_nao_regrede(
    authenticated_client, processo_convocacao
):
    """Permite regressão de passo no comportamento atual da API."""
    processo_convocacao.passo = 3
    processo_convocacao.save(update_fields=["passo"])

    url = reverse(
        "processoconvocacao-atualizar-passo", args=[processo_convocacao.uuid]
    )
    response = authenticated_client.patch(url, {"passo": 2}, format="json")

    assert response.status_code == status.HTTP_200_OK
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.passo == 2


def test_atualizar_passo_invalido(authenticated_client, processo_convocacao):
    """Retorna 400 para passo inválido."""
    url = reverse(
        "processoconvocacao-atualizar-passo", args=[processo_convocacao.uuid]
    )
    response = authenticated_client.patch(url, {"passo": 5}, format="json")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_atualizar_passo_processo_finalizado(
    authenticated_client, processo_convocacao
):
    """Permite atualização de passo mesmo com processo finalizado no
    comportamento
    atual da API."""
    processo_convocacao.status = "FINALIZADO"
    processo_convocacao.save(update_fields=["status"])

    url = reverse(
        "processoconvocacao-atualizar-passo", args=[processo_convocacao.uuid]
    )
    response = authenticated_client.patch(url, {"passo": 2}, format="json")

    assert response.status_code == status.HTTP_200_OK
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.passo == 2


# Testes de Busca
def test_processo_convocacao_search(authenticated_client, processo_convocacao):
    """Testa busca por texto nos processos."""
    url = reverse("processoconvocacao-list")

    # Busca por nome do concurso
    response = authenticated_client.get(url, {"search": "Concurso"})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1

    # Busca por descrição
    response = authenticated_client.get(url, {"search": "Descrição"})
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 1


# --- Testes Envio Email (list, retrieve, create) ---


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
    from processos.models.envio_email_candidato import (
        ENVIO_STATUS_ERRO,
        ENVIO_STATUS_SUCESSO,
    )

    EnvioEmailCandidato.objects.create(
        envio_email=envio_email,
        nome="Fulano",
        rf="1234567",
        email="fulano@test.com",
        status=ENVIO_STATUS_SUCESSO,
        conteudo="<p>Conteúdo 1</p>",
    )
    EnvioEmailCandidato.objects.create(
        envio_email=envio_email,
        nome="Ciclano",
        rf="7654321",
        email="ciclano@test.com",
        status=ENVIO_STATUS_ERRO,
        conteudo="<p>Conteúdo 2</p>",
    )
    return list(envio_email.candidatos.all())


def test_envio_email_list(authenticated_client, envio_email):
    """Testa GET /api/v1/envio-email/ (listagem do histórico)."""
    url = reverse("envio-email-list")
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) >= 1
    assert response.data[0]["uuid"] == str(envio_email.uuid)
    assert response.data[0]["processo_nome"] == envio_email.processo_nome
    assert (
        response.data[0]["quantidade_candidatos"]
        == envio_email.quantidade_candidatos
    )
    assert response.data[0]["tipo"] == TIPO_CONVOCACAO


def test_envio_email_retrieve(
    authenticated_client, envio_email, envio_email_candidatos
):
    """Testa GET /api/v1/envio-email/<uuid>/ (detalhe com candidatos)."""
    url = reverse("envio-email-detail", args=[envio_email.uuid])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["uuid"] == str(envio_email.uuid)
    assert response.data["processo_nome"] == envio_email.processo_nome
    assert "candidatos" in response.data
    assert len(response.data["candidatos"]) == 2
    nomes = [c["nome"] for c in response.data["candidatos"]]
    assert "Fulano" in nomes
    assert "Ciclano" in nomes


def test_envio_email_retrieve_not_found(authenticated_client):
    """Testa GET detalhe com UUID inexistente."""
    url = reverse("envio-email-detail", args=[uuid.uuid4()])
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_404_NOT_FOUND


@patch("processos.views.envio_email.iniciar_processamento_envio")
def test_envio_email_create(
    mock_iniciar, authenticated_client, processo_convocacao
):
    """Testa POST /api/v1/envio-email/ (inicia processamento de envio)."""
    mock_envio = EnvioEmail.objects.create(
        processo_uuid=processo_convocacao.uuid,
        processo_nome=processo_convocacao.concurso_nome,
        tipo=TIPO_CONVOCACAO,
        quantidade_candidatos=0,
    )
    mock_iniciar.return_value = mock_envio

    url = reverse("envio-email-list")
    payload = {
        'processo_uuid': str(processo_convocacao.uuid),
        'processo_nome': processo_convocacao.concurso_nome,
        'tipo': TIPO_CONVOCACAO,
        'conteudo': '<p>Conteúdo</p>',
    }
    response = authenticated_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert "detail" in response.data
    assert "envio_email_uuid" in response.data
    assert response.data["envio_email_uuid"] == str(mock_envio.uuid)
    mock_iniciar.assert_called_once()
    call_kwargs = mock_iniciar.call_args[1]
    assert call_kwargs["processo_nome"] == processo_convocacao.concurso_nome
    assert call_kwargs["tipo"] == TIPO_CONVOCACAO


@patch("processos.views.envio_email.iniciar_processamento_envio")
def test_envio_email_create_invalid_payload(
    mock_iniciar, authenticated_client
):
    """Testa POST com payload inválido (processo não encontrado)."""
    url = reverse("envio-email-list")
    payload = {
        'processo_uuid': str(uuid.uuid4()),
        'processo_nome': 'Inexistente',
        'tipo': TIPO_CONVOCACAO,
        'conteudo': '<p>Conteúdo</p>',
    }
    response = authenticated_client.post(url, payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    mock_iniciar.assert_not_called()


@patch("processos.views.envio_email.iniciar_processamento_envio")
def test_envio_email_create_quando_servico_levanta_excecao_retorna_500(
    mock_iniciar, authenticated_client, processo_convocacao
):
    """Quando iniciar_processamento_envio levanta exceção, a view retorna 500
    com
    detail."""
    mock_iniciar.side_effect = Exception(
        "Email duplicado entre candidatos: duplicado@test.com"
    )

    url = reverse("envio-email-list")
    payload = {
        'processo_uuid': str(processo_convocacao.uuid),
        'processo_nome': processo_convocacao.concurso_nome,
        'tipo': TIPO_CONVOCACAO,
        'conteudo': '<p>Conteúdo</p>',
    }
    response = authenticated_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "detail" in response.data
    assert "duplicado@test.com" in response.data["detail"]
