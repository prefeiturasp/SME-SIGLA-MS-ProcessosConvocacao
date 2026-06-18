"""Módulo tests/test_admin."""

import pytest
from django.contrib.admin.sites import site

from cargos.admin import CargoProcessoInline
from processos.admin import ProcessoConvocacaoAdmin
from processos.models import ProcessoConvocacao

pytestmark = pytest.mark.django_db


@pytest.fixture
def processo_convocacao_admin():
    """Fixture do admin de ProcessoConvocacao."""
    return ProcessoConvocacaoAdmin(model=ProcessoConvocacao, admin_site=site)


def test_colunas_listagem(processo_convocacao_admin):
    """Verifica colunas da listagem do admin."""
    assert processo_convocacao_admin.list_display == (
        "concurso_nome",
        "descricao",
        "tipo_escolha",
        "status",
        "data_convocacao",
        "data_corte_vagas",
    )


def test_campos_busca(processo_convocacao_admin):
    """Verifica campos de busca do admin."""
    assert processo_convocacao_admin.search_fields == (
        "concurso_nome",
        "descricao",
    )


def test_filtros_listagem(processo_convocacao_admin):
    """Verifica filtros da listagem do admin."""
    assert processo_convocacao_admin.list_filter == (
        "status",
        "tipo_escolha",
        "data_convocacao",
        "data_corte_vagas",
    )


def test_campos_somente_leitura(processo_convocacao_admin):
    """Verifica campos somente leitura do admin."""
    assert processo_convocacao_admin.readonly_fields == (
        "uuid",
        "criado_em",
        "atualizado_em",
    )


def test_inlines_admin(processo_convocacao_admin):
    """Verifica inlines do admin."""
    assert processo_convocacao_admin.inlines == (CargoProcessoInline,)


def test_fieldsets_admin(processo_convocacao_admin):
    """Verifica fieldsets do admin."""
    assert processo_convocacao_admin.fieldsets == (
        (
            "Informações do Concurso",
            {"fields": ("concurso_uuid", "concurso_nome")},
        ),
        (
            "Dados do Processo",
            {"fields": ("descricao", "tipo_escolha", "status")},
        ),
        ("Datas", {"fields": ("data_convocacao", "data_corte_vagas")}),
        (
            "Metadados",
            {
                "fields": ("uuid", "criado_em", "atualizado_em"),
                "classes": ("collapse",),
            },
        ),
    )
