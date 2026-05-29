"""Testes para conversão de imagens base64 em anexos inline (cid:)."""

from processos.utils.email_inline_images import (
    converter_imagens_base64_para_cid,
)

# PNG 1x1 transparente
PNG_1X1_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQ"
    "DwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def test_converter_imagem_base64_para_cid():
    html = f'<p class="ql-align-center"><img src="data:image/png;base64,{PNG_1X1_B64}"></p>'  # noqa: E501
    novo_html, partes = converter_imagens_base64_para_cid(html)

    assert "data:image" not in novo_html
    assert 'src="cid:email_img_0"' in novo_html
    assert len(partes) == 1
    assert partes[0]["Content-ID"] == "<email_img_0>"


def test_converter_varias_imagens():
    html = (
        f'<img src="data:image/png;base64,{PNG_1X1_B64}">'
        f'<img src="data:image/png;base64,{PNG_1X1_B64}">'
    )
    novo_html, partes = converter_imagens_base64_para_cid(html)

    assert "cid:email_img_0" in novo_html
    assert "cid:email_img_1" in novo_html
    assert len(partes) == 2


def test_html_sem_imagem_retorna_inalterado():
    html = "<p>texto</p>"
    novo_html, partes = converter_imagens_base64_para_cid(html)
    assert novo_html == html
    assert partes == []


def test_base64_invalido_mantem_data_uri():
    html = '<img src="data:image/png;base64,!!!invalido!!!">'
    novo_html, partes = converter_imagens_base64_para_cid(html)
    assert "data:image/png" in novo_html
    assert partes == []
