"""Módulo tests/test_conteudo_html."""

from processos.utils.conteudo_html import normalizar_conteudo_html


def test_normalizar_remove_barra_aspas_duplicada():
    """Verifica normalizar remove barra aspas duplicada."""
    entrada = '<p class=\\"ql-align-center\\">Ok</p>'
    assert (
        normalizar_conteudo_html(entrada)
        == '<p class="ql-align-center">Ok</p>'
    )


def test_normalizar_json_string_dupla():
    """Verifica normalizar json string dupla."""
    entrada = '"<p>Olá</p>"'
    assert normalizar_conteudo_html(entrada) == "<p>Olá</p>"


def test_normalizar_preserva_html_correto():
    """Verifica normalizar preserva html correto."""
    entrada = '<p class="ql-align-center">Ok</p>'
    assert normalizar_conteudo_html(entrada) == entrada
