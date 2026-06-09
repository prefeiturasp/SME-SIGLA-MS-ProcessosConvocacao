"""Módulo tests/test_admin."""
import pytest
from django.contrib.admin.sites import site

from processos.admin import CargoProcessoInline, ProcessoConvocacaoAdmin
from processos.models import ProcessoConvocacao

pytestmark = pytest.mark.django_db


@pytest.fixture
def processo_convocacao_admin():
    """Executa processo convocacao admin.
    
    Returns:
        Resultado da operação.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    return ProcessoConvocacaoAdmin(model=ProcessoConvocacao, admin_site=site)


def test_list_display(processo_convocacao_admin):
    """Verifica list display.
    
    Args:
        processo_convocacao_admin: Parâmetro processo convocacao admin da operação.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    assert processo_convocacao_admin.list_display == (
        "concurso_nome",
        "descricao",
        "tipo_escolha",
        "status",
        "data_convocacao",
        "data_corte_vagas",
    )


def test_search_fields(processo_convocacao_admin):
    """Verifica search fields.
    
    Args:
        processo_convocacao_admin: Parâmetro processo convocacao admin da operação.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    assert processo_convocacao_admin.search_fields == (
        "concurso_nome",
        "descricao",
    )


def test_list_filter(processo_convocacao_admin):
    """Verifica list filter.
    
    Args:
        processo_convocacao_admin: Parâmetro processo convocacao admin da operação.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    assert processo_convocacao_admin.list_filter == (
        "status",
        "tipo_escolha",
        "data_convocacao",
        "data_corte_vagas",
    )


def test_readonly_fields(processo_convocacao_admin):
    """Verifica readonly fields.
    
    Args:
        processo_convocacao_admin: Parâmetro processo convocacao admin da operação.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    assert processo_convocacao_admin.readonly_fields == (
        "uuid",
        "criado_em",
        "atualizado_em",
    )


def test_inlines(processo_convocacao_admin):
    """Verifica inlines.
    
    Args:
        processo_convocacao_admin: Parâmetro processo convocacao admin da operação.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
    assert processo_convocacao_admin.inlines == (CargoProcessoInline,)


def test_fieldsets(processo_convocacao_admin):
    """Verifica fieldsets.
    
    Args:
        processo_convocacao_admin: Parâmetro processo convocacao admin da operação.
    
    Returns:
        Nenhum valor; valida comportamento via asserções.
    
    Raises:
        Nenhuma exceção específica documentada.
    """
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
