"""Testes das views do app cargos."""

from uuid import uuid4

import pytest
from cargos.models import CargoProcesso
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status

pytestmark = pytest.mark.django_db


def test_cargos_de_processo_por_id_inteiro_retorna_404(
    authenticated_client, cargo_processo
):
    """Rota aninhada com o id interno responde 404, não 500."""
    url = reverse("processo-cargos-list", args=[cargo_processo.processo.id])
    resposta = authenticated_client.get(url)

    assert resposta.status_code == status.HTTP_404_NOT_FOUND


def test_cargos_de_processo_por_uuid_retorna_200(
    authenticated_client, cargo_processo
):
    """Rota aninhada pelo uuid continua listando os cargos."""
    url = reverse("processo-cargos-list", args=[cargo_processo.processo.uuid])
    resposta = authenticated_client.get(url)

    assert resposta.status_code == status.HTTP_200_OK


def test_cargo_devolve_processo_como_uuid(
    authenticated_client, cargo_processo
):
    """O processo sai como uuid e o id interno não aparece."""
    url = reverse("processo-cargos-list", args=[cargo_processo.processo.uuid])
    cargo = authenticated_client.get(url).json()[0]

    assert cargo["processo"] == str(cargo_processo.processo.uuid)
    assert "id" not in cargo


def test_lista_de_cargos_nao_cresce_em_queries(
    authenticated_client, cargo_processo, django_assert_num_queries
):
    """A quantidade de queries da listagem não depende do número de cargos."""
    processo_cargo = cargo_processo.processo
    url = reverse("processo-cargos-list", args=[processo_cargo.uuid])

    def criar_cargos(quantidade):
        for _ in range(quantidade):
            CargoProcesso.objects.create(
                processo=processo_cargo,
                cargo_nome=f"Cargo {uuid4()}",
                cargo_uuid=uuid4(),
            )

    with CaptureQueriesContext(connection) as com_um:
        authenticated_client.get(url)

    criar_cargos(2)
    with django_assert_num_queries(len(com_um)):
        resposta = authenticated_client.get(url)

    assert len(resposta.json()) == 3
