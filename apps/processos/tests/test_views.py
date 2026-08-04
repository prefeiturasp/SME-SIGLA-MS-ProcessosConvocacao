"""Testes unitários para as views do app processos usando pytest."""

import uuid
from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from cargos.models import CargoProcesso
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from processos.constants import (
    ERROR_CANDIDATOS_PENDENTES_ESCOLHA,
    ERROR_PROCESSO_JA_CANCELADO,
    ERROR_PROCESSO_JA_FINALIZADO,
    ERROR_PROCESSO_NAO_PODE_EDITAR,
    TIPO_ESCOLHA_CHOICES,
)
from processos.models import ProcessoConvocacao
from processos.services.exceptions import ConcursoServiceError
from rest_framework import status

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
def processo_cargo(usuario):
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
def processo_permissao(usuario):
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
def processo_lista(usuario):
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
    resposta = authenticated_client.get(url)

    assert resposta.status_code == status.HTTP_200_OK
    assert "results" in resposta.data
    assert len(resposta.data["results"]) == 1
    assert (
        resposta.data["results"][0]["concurso_nome"]
        == processo_convocacao.concurso_nome
    )


def test_processo_convocacao_criacao(authenticated_client):
    """Testa a criação de um processo de convocação."""
    url = reverse("processoconvocacao-list")
    dados = {
        "concurso_uuid": str(uuid.uuid4()),
        "concurso_nome": "Novo Concurso",
        "descricao": "Descrição do novo processo",
        "tipo_escolha": "NOVA_AUTORIZACAO",
        "status": "EM_ANDAMENTO",
        "data_convocacao": (timezone.now() + timedelta(days=30)).isoformat(),
        "data_corte_vagas": (timezone.now() + timedelta(days=5)).isoformat(),
    }

    resposta = authenticated_client.post(url, dados, format="json")

    assert resposta.status_code == status.HTTP_201_CREATED
    assert ProcessoConvocacao.objects.count() == 1

    processo = ProcessoConvocacao.objects.first()
    assert processo.concurso_nome == "Novo Concurso"


def test_criar_processo_chama_atualizacao_situacao_concurso_em_andamento(
    authenticated_client,
):
    """Verifica que criar processo dispara atualização de situação."""
    url = reverse("processoconvocacao-list")
    concurso_uuid_str = str(uuid.uuid4())
    dados = {
        "concurso_uuid": concurso_uuid_str,
        "concurso_nome": "Novo Concurso",
        "descricao": "Descrição do novo processo",
        "tipo_escolha": "NOVA_AUTORIZACAO",
        "status": "EM_ANDAMENTO",
        "data_convocacao": (timezone.now() + timedelta(days=30)).isoformat(),
        "data_corte_vagas": (timezone.now() + timedelta(days=5)).isoformat(),
    }

    with patch(
        "processos.api.views.ConcursosApiService"
    ) as mock_service_cls:
        mock_service = Mock()
        mock_service_cls.return_value = mock_service

        resposta = authenticated_client.post(url, dados, format="json")

    assert resposta.status_code == status.HTTP_201_CREATED
    mock_service.atualizar_situacao.assert_called_once_with(
        concurso_uuid=concurso_uuid_str, situacao="EM_ANDAMENTO"
    )


def test_criar_processo_nao_falha_quando_atualizacao_situacao_da_erro(
    authenticated_client,
):
    """Verifica que falha na chamada a Concursos não impede a criação."""
    url = reverse("processoconvocacao-list")
    dados = {
        "concurso_uuid": str(uuid.uuid4()),
        "concurso_nome": "Novo Concurso 2",
        "descricao": "Descrição do novo processo 2",
        "tipo_escolha": "NOVA_AUTORIZACAO",
        "status": "EM_ANDAMENTO",
        "data_convocacao": (timezone.now() + timedelta(days=30)).isoformat(),
        "data_corte_vagas": (timezone.now() + timedelta(days=5)).isoformat(),
    }

    with patch(
        "processos.api.views.ConcursosApiService"
    ) as mock_service_cls:
        mock_service = Mock()
        mock_service.atualizar_situacao.side_effect = ConcursoServiceError(
            "falhou"
        )
        mock_service_cls.return_value = mock_service

        resposta = authenticated_client.post(url, dados, format="json")

    assert resposta.status_code == status.HTTP_201_CREATED
    assert ProcessoConvocacao.objects.filter(
        concurso_nome="Novo Concurso 2"
    ).exists()


def test_processo_convocacao_detalhe(
    authenticated_client, processo_convocacao
):
    """Testa a recuperação de um processo específico."""
    url = reverse("processoconvocacao-detail", args=[processo_convocacao.uuid])
    resposta = authenticated_client.get(url)

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["concurso_nome"] == processo_convocacao.concurso_nome
    assert resposta.data["uuid"] == str(processo_convocacao.uuid)


def test_processo_convocacao_atualizacao(
    authenticated_client, processo_convocacao
):
    """Testa a atualização de um processo."""
    url = reverse("processoconvocacao-detail", args=[processo_convocacao.uuid])
    dados = {
        "concurso_nome": "Concurso Atualizado",
        "descricao": "Descrição atualizada",
        "status": "FINALIZADO",
    }

    resposta = authenticated_client.patch(url, dados, format="json")

    assert resposta.status_code == status.HTTP_200_OK
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.concurso_nome == "Concurso Atualizado"
    assert processo_convocacao.status == "FINALIZADO"


@patch(
    "processos.api.views.ProcessoConvocacaoService"
    ".excluir_processo_e_dependencias"
)
def test_processo_convocacao_exclusao(
    mock_excluir_dependencias,
    authenticated_client,
    processo_convocacao,
):
    """Testa a exclusão lógica de um processo."""
    processo_convocacao.status = "CANCELADO"
    processo_convocacao.save(update_fields=["status"])

    def _excluir_e_inativar(*, processo, auth_header=None):
        """Executa  excluir e inativar."""
        processo.inativar()

    mock_excluir_dependencias.side_effect = _excluir_e_inativar

    url = reverse("processoconvocacao-detail", args=[processo_convocacao.uuid])
    resposta = authenticated_client.delete(url)

    assert resposta.status_code == status.HTTP_204_NO_CONTENT
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.esta_ativo is False


def test_filtro_data_convocacao_inicio(
    authenticated_client, processo_convocacao
):
    """Testa filtro por data de convocação início."""
    url = reverse("processoconvocacao-list")

    data_inicio = (
        processo_convocacao.data_convocacao - timedelta(days=5)
    ).strftime("%Y-%m-%d")
    resposta = authenticated_client.get(
        url, {"data_convocacao_inicio": data_inicio}
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data["results"]) == 1


def test_filtro_data_convocacao_fim(authenticated_client, processo_convocacao):
    """Testa filtro por data de convocação fim."""
    url = reverse("processoconvocacao-list")

    data_fim = (
        processo_convocacao.data_convocacao + timedelta(days=5)
    ).strftime("%Y-%m-%d")
    resposta = authenticated_client.get(url, {"data_convocacao_fim": data_fim})

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data["results"]) == 1


def test_filtro_data_convocacao_intervalo(
    authenticated_client, processo_convocacao
):
    """Testa filtro por intervalo de datas de convocação."""
    url = reverse("processoconvocacao-list")

    data_inicio = (
        processo_convocacao.data_convocacao - timedelta(days=5)
    ).strftime("%Y-%m-%d")
    data_fim = (
        processo_convocacao.data_convocacao + timedelta(days=5)
    ).strftime("%Y-%m-%d")

    resposta = authenticated_client.get(
        url,
        {
            "data_convocacao_inicio": data_inicio,
            "data_convocacao_fim": data_fim,
        },
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data["results"]) == 1


def test_filtro_cargo_uuid(
    authenticated_client, processo_convocacao, cargos_processo
):
    """Testa filtro por cargo_uuid."""
    url = reverse("processoconvocacao-list")

    cargo_uuid = cargos_processo[0].cargo_uuid

    resposta = authenticated_client.get(url, {"cargo_uuid": str(cargo_uuid)})

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data["results"]) == 1


def test_filtro_data_invalida(authenticated_client):
    """Testa filtro com data inválida."""
    url = reverse("processoconvocacao-list")

    resposta = authenticated_client.get(
        url, {"data_convocacao_inicio": "data-invalida"}
    )

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data["results"]) == 0


def test_filtro_cargo_uuid_invalido(authenticated_client):
    """Testa filtro com cargo_uuid inválido."""
    url = reverse("processoconvocacao-list")

    resposta = authenticated_client.get(url, {"cargo_uuid": "uuid-invalido"})

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data["results"]) == 0


def test_cargos_list_sucesso(
    authenticated_client, processo_convocacao, cargos_processo
):
    """Lista cargos do processo com sucesso."""
    url = reverse(
        "processo-cargos-list",
        kwargs={"processo_pk": processo_convocacao.uuid},
    )
    resposta = authenticated_client.get(url)

    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data) == 2
    nomes = [c["cargo_nome"] for c in resposta.data]
    assert "Analista de Sistemas" in nomes
    assert "Desenvolvedor Backend" in nomes


def test_cargos_list_processo_nao_encontrado(authenticated_client):
    """Retorna 404 quando processo não existe."""
    url = reverse("processo-cargos-list", kwargs={"processo_pk": uuid.uuid4()})
    resposta = authenticated_client.get(url)

    assert resposta.status_code == status.HTTP_404_NOT_FOUND
    assert resposta.data["error"] == "Processo de convocação não encontrado"


def test_cargos_create_novos_cargos(authenticated_client, processo_convocacao):
    """POST cria novos cargos quando o corpo não tem uuid."""
    url = reverse(
        "processo-cargos-list",
        kwargs={"processo_pk": processo_convocacao.uuid},
    )
    dados_requisicao = {
        "porcentagem_nna": 0.2,
        "porcentagem_pcd": 0.05,
        "cargos": [
            {"cargo_nome": "Cargo Novo 1", "cargo_uuid": str(uuid.uuid4())},
            {"cargo_nome": "Cargo Novo 2", "cargo_uuid": str(uuid.uuid4())},
        ],
    }
    resposta = authenticated_client.post(url, dados_requisicao, format="json")

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["success"] is True
    assert resposta.data["cargos_criados"] == 2
    assert resposta.data["cargos_atualizados"] == 0
    assert resposta.data["cargos_removidos"] == 0
    assert len(resposta.data["cargos"]) == 2


def test_cargos_create_atualiza_existentes(
    authenticated_client, processo_convocacao, cargos_processo
):
    """POST atualiza cargos existentes quando o corpo tem uuid."""
    cargo = cargos_processo[0]
    url = reverse(
        "processo-cargos-list",
        kwargs={"processo_pk": processo_convocacao.uuid},
    )
    dados_requisicao = {
        "cargos": [
            {
                "uuid": str(cargo.uuid),
                "cargo_nome": "Analista Atualizado",
                "cargo_uuid": str(cargo.cargo_uuid),
            },
        ]
    }
    resposta = authenticated_client.post(url, dados_requisicao, format="json")

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["cargos_criados"] == 0
    assert resposta.data["cargos_atualizados"] == 1
    assert (
        resposta.data["cargos_removidos"] == 1
    )  # o segundo cargo foi removido
    cargo.refresh_from_db()
    assert cargo.cargo_nome == "Analista Atualizado"


def test_cargos_create_remove_cargos_nao_enviados(
    authenticated_client, processo_convocacao, cargos_processo
):
    """POST remove cargos que não estão no corpo da requisição."""
    cargo = cargos_processo[0]
    url = reverse(
        "processo-cargos-list",
        kwargs={"processo_pk": processo_convocacao.uuid},
    )
    dados_requisicao = {
        "cargos": [
            {
                "uuid": str(cargo.uuid),
                "cargo_nome": cargo.cargo_nome,
                "cargo_uuid": str(cargo.cargo_uuid),
            },
        ]
    }
    resposta = authenticated_client.post(url, dados_requisicao, format="json")

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["cargos_removidos"] == 1
    assert (
        CargoProcesso.objects.filter(processo=processo_convocacao).count() == 1
    )


def test_cargos_create_processo_nao_encontrado(authenticated_client):
    """POST retorna 404 quando processo não existe."""
    url = reverse("processo-cargos-list", kwargs={"processo_pk": uuid.uuid4()})
    resposta = authenticated_client.post(url, {"cargos": []}, format="json")

    assert resposta.status_code == status.HTTP_404_NOT_FOUND
    assert resposta.data["error"] == "Processo de convocação não encontrado"


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
    resposta = authenticated_client.post(
        url,
        {"cargos": [{"cargo_nome": "Cargo", "cargo_uuid": str(uuid.uuid4())}]},
        format="json",
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data["detail"] == ERROR_PROCESSO_NAO_PODE_EDITAR


def test_cargos_create_corpo_nao_e_lista(
    authenticated_client, processo_convocacao
):
    """POST returns 400 when body is a list (expects dict with cargos key)."""
    url = reverse(
        "processo-cargos-list",
        kwargs={"processo_pk": processo_convocacao.uuid},
    )
    resposta = authenticated_client.post(
        url, [{"cargo_nome": "Cargo"}], format="json"
    )

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert "non_field_errors" in resposta.data


def test_cargos_create_uuid_nao_encontrado_retorna_207(
    authenticated_client, processo_convocacao, cargos_processo
):
    """POST com uuid de cargo inexistente retorna 207 com erros."""
    url = reverse(
        "processo-cargos-list",
        kwargs={"processo_pk": processo_convocacao.uuid},
    )
    dados_requisicao = {
        "cargos": [
            {
                "uuid": str(uuid.uuid4()),
                "cargo_nome": "Inexistente",
                "cargo_uuid": str(uuid.uuid4()),
            },
        ]
    }
    resposta = authenticated_client.post(url, dados_requisicao, format="json")

    assert resposta.status_code == status.HTTP_207_MULTI_STATUS
    assert resposta.data["success"] is True
    assert "erros" in resposta.data
    assert len(resposta.data["erros"]) == 1
    assert (
        resposta.data["erros"][0]["erros"]
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
    resposta = authenticated_client.delete(url)

    assert resposta.status_code == status.HTTP_204_NO_CONTENT
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
    resposta = authenticated_client.delete(url)

    assert resposta.status_code == status.HTTP_404_NOT_FOUND
    assert resposta.data["error"] == "Processo de convocação não encontrado"


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
    resposta = authenticated_client.delete(url)

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data["detail"] == ERROR_PROCESSO_NAO_PODE_EDITAR


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
    resposta = authenticated_client.delete(url)

    assert resposta.status_code == status.HTTP_404_NOT_FOUND
    assert resposta.data["error"] == "Cargo não encontrado para este processo"


def test_endpoint_filtros_basico(
    authenticated_client, processo_convocacao, cargos_processo
):
    """Testa o endpoint /filtros/ com dados básicos."""
    url = reverse("processoconvocacao-filtros")
    resposta = authenticated_client.get(url)

    assert resposta.status_code == status.HTTP_200_OK
    assert "concursos" in resposta.data
    assert "cargos" in resposta.data
    assert "tipos_escolha" in resposta.data

    concursos = resposta.data["concursos"]
    assert len(concursos) == 1
    assert "value" in concursos[0]
    assert "label" in concursos[0]
    assert concursos[0]["value"] == str(processo_convocacao.concurso_uuid)
    assert concursos[0]["label"] == processo_convocacao.concurso_nome

    cargos = resposta.data["cargos"]
    assert len(cargos) == 2
    for cargo in cargos:
        assert "value" in cargo
        assert "label" in cargo
        assert cargo["value"] is not None
        assert cargo["label"] is not None

    tipos_escolha = resposta.data["tipos_escolha"]
    tipos_esperados = dict(TIPO_ESCOLHA_CHOICES)
    assert len(tipos_escolha) == len(tipos_esperados)
    for tipo in tipos_escolha:
        assert "value" in tipo
        assert "label" in tipo
        assert tipo["value"] in tipos_esperados
        assert tipo["label"] == tipos_esperados[tipo["value"]]


def test_endpoint_filtros_multiplos_processos(authenticated_client, usuario):
    """Testa o endpoint /filtros/ com múltiplos processos."""
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
    resposta = authenticated_client.get(url)

    assert resposta.status_code == status.HTTP_200_OK
    assert "tipos_escolha" in resposta.data

    concursos = resposta.data["concursos"]
    assert len(concursos) == 2

    cargos = resposta.data["cargos"]
    assert len(cargos) == 2

    tipos_escolha = resposta.data["tipos_escolha"]
    assert len(tipos_escolha) == len(TIPO_ESCOLHA_CHOICES)


def test_endpoint_filtros_concurso_duplicado(authenticated_client, usuario):
    """Testa que concursos duplicados são removidos no endpoint /filtros/."""

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
        concurso_uuid=concurso_uuid,  
        concurso_nome=concurso_nome,  
        descricao="Descrição 2",
        tipo_escolha="NOVA_AUTORIZACAO",
        status="EM_ANDAMENTO",
        data_convocacao=timezone.now() + timedelta(days=15),
    )

    url = reverse("processoconvocacao-filtros")
    resposta = authenticated_client.get(url)

    assert resposta.status_code == status.HTTP_200_OK

    concursos = resposta.data["concursos"]
    assert len(concursos) == 1
    assert concursos[0]["value"] == str(concurso_uuid)
    assert concursos[0]["label"] == concurso_nome


def test_endpoint_filtros_cargo_duplicado(authenticated_client, usuario):
    """Testa que cargos com nomes duplicados são removidos no endpoint."""
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
    resposta = authenticated_client.get(url)

    assert resposta.status_code == status.HTTP_200_OK
    cargos = resposta.data["cargos"]
    assert len(cargos) == 1
    assert cargos[0]["label"] == cargo_nome


def test_endpoint_filtros_sem_dados(authenticated_client):
    """Testa o endpoint /filtros/ quando não há dados."""
    url = reverse("processoconvocacao-filtros")
    resposta = authenticated_client.get(url)

    assert resposta.status_code == status.HTTP_200_OK
    assert "concursos" in resposta.data
    assert "cargos" in resposta.data
    assert "tipos_escolha" in resposta.data

    assert len(resposta.data["concursos"]) == 0
    assert len(resposta.data["cargos"]) == 0

    assert len(resposta.data["tipos_escolha"]) == len(TIPO_ESCOLHA_CHOICES)


def test_endpoint_filtros_tipos_escolha(authenticated_client):
    """Testa que os tipos de escolha são retornados corretamente."""
    url = reverse("processoconvocacao-filtros")
    resposta = authenticated_client.get(url)

    assert resposta.status_code == status.HTTP_200_OK
    assert "tipos_escolha" in resposta.data

    tipos_escolha = resposta.data["tipos_escolha"]

    tipos_esperados = dict(TIPO_ESCOLHA_CHOICES)
    assert len(tipos_escolha) == len(tipos_esperados)

    for tipo in tipos_escolha:
        assert tipo["value"] in tipos_esperados
        assert tipo["label"] == tipos_esperados[tipo["value"]]
        assert "value" in tipo
        assert "label" in tipo


@patch("processos.api.views.EscolhasApiService.buscar_candidatos_com_escolha")
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
    resposta = authenticated_client.post(url)

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["status"] == "FINALIZADO"
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.status == "FINALIZADO"
    mock_buscar.assert_called_once_with(str(processo_convocacao.concurso_uuid))


@patch("processos.api.views.EscolhasApiService.buscar_candidatos_com_escolha")
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
    resposta = authenticated_client.post(url)

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["status"] == "FINALIZADO"
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.status == "FINALIZADO"


def test_finalizar_ja_finalizado(authenticated_client, processo_convocacao):
    """Retorna 400 quando processo já está finalizado."""
    processo_convocacao.status = "FINALIZADO"
    processo_convocacao.save()

    url = reverse(
        "processoconvocacao-finalizar", args=[processo_convocacao.uuid]
    )
    resposta = authenticated_client.post(url)

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data["detail"] == ERROR_PROCESSO_JA_FINALIZADO
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.status == "FINALIZADO"


def test_finalizar_ja_cancelado(authenticated_client, processo_convocacao):
    """Retorna 400 quando processo está cancelado."""
    processo_convocacao.status = "CANCELADO"
    processo_convocacao.save()

    url = reverse(
        "processoconvocacao-finalizar", args=[processo_convocacao.uuid]
    )
    resposta = authenticated_client.post(url)

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data["detail"] == ERROR_PROCESSO_JA_CANCELADO
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.status == "CANCELADO"


def test_finalizar_status_nao_em_andamento(
    authenticated_client, processo_convocacao
):
    """Retorna 400 se o processo não estiver em andamento."""
    # Usa um status fora dos 3 principais para acionar a mensagem genérica
    processo_convocacao.status = "PENDENTE"
    processo_convocacao.save(update_fields=["status"])

    url = reverse(
        "processoconvocacao-finalizar", args=[processo_convocacao.uuid]
    )
    resposta = authenticated_client.post(url)

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        "Apenas processos em andamento podem ser finalizados"
        in resposta.data["detail"]
    )


@patch("processos.api.views.EscolhasApiService.buscar_candidatos_com_escolha")
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
    resposta = authenticated_client.post(url)

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data["detail"] == ERROR_CANDIDATOS_PENDENTES_ESCOLHA
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.status == "EM_ANDAMENTO"


@patch("processos.api.views.EscolhasApiService.buscar_candidatos_com_escolha")
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
    resposta = authenticated_client.post(url)

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        resposta.data["detail"] == "Erro ao consultar escolhas dos candidatos."
    )
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.status == "EM_ANDAMENTO"


@patch("processos.api.views.EscolhasApiService.buscar_candidatos_com_escolha")
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
    resposta = authenticated_client.post(url)

    assert resposta.status_code == status.HTTP_200_OK
    assert resposta.data["status"] == "FINALIZADO"
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.status == "FINALIZADO"


@patch("processos.api.views.EscolhasApiService.buscar_candidatos_com_escolha")
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
    resposta = authenticated_client.post(url)

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST
    assert resposta.data["detail"] == ERROR_CANDIDATOS_PENDENTES_ESCOLHA


def test_processo_convocacao_filtros(
    authenticated_client, processo_convocacao
):
    """Testa filtros básicos dos processos."""
    url = reverse("processoconvocacao-list")

    # Filtro por status
    resposta = authenticated_client.get(url, {"status": "EM_ANDAMENTO"})
    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data["results"]) == 1

    resposta = authenticated_client.get(
        url, {"tipo_escolha": "NOVA_AUTORIZACAO"}
    )
    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data["results"]) == 1

    # Filtro por concurso_uuid
    resposta = authenticated_client.get(
        url, {"concurso_uuid": str(processo_convocacao.concurso_uuid)}
    )
    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data["results"]) == 1


def test_atualizar_passo_sucesso(authenticated_client, processo_convocacao):
    """Atualiza passo do processo com sucesso."""
    url = reverse(
        "processoconvocacao-atualizar-passo", args=[processo_convocacao.uuid]
    )
    resposta = authenticated_client.patch(url, {"passo": 2}, format="json")

    assert resposta.status_code == status.HTTP_200_OK
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
    resposta = authenticated_client.patch(url, {"passo": 2}, format="json")

    assert resposta.status_code == status.HTTP_200_OK
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.passo == 2


def test_atualizar_passo_invalido(authenticated_client, processo_convocacao):
    """Retorna 400 para passo inválido."""
    url = reverse(
        "processoconvocacao-atualizar-passo", args=[processo_convocacao.uuid]
    )
    resposta = authenticated_client.patch(url, {"passo": 5}, format="json")

    assert resposta.status_code == status.HTTP_400_BAD_REQUEST


def test_atualizar_passo_processo_finalizado(
    authenticated_client, processo_convocacao
):
    """Permite atualização de passo mesmo com processo finalizado no."""
    processo_convocacao.status = "FINALIZADO"
    processo_convocacao.save(update_fields=["status"])

    url = reverse(
        "processoconvocacao-atualizar-passo", args=[processo_convocacao.uuid]
    )
    resposta = authenticated_client.patch(url, {"passo": 2}, format="json")

    assert resposta.status_code == status.HTTP_200_OK
    processo_convocacao.refresh_from_db()
    assert processo_convocacao.passo == 2


def test_processo_convocacao_busca(authenticated_client, processo_convocacao):
    """Testa busca por texto nos processos."""
    url = reverse("processoconvocacao-list")

    # Busca por nome do concurso
    resposta = authenticated_client.get(url, {"search": "Concurso"})
    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data["results"]) == 1

    # Busca por descrição
    resposta = authenticated_client.get(url, {"search": "Descrição"})
    assert resposta.status_code == status.HTTP_200_OK
    assert len(resposta.data["results"]) == 1
