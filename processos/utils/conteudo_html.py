r"""Normalização de HTML armazenado em EnvioEmailConteudo.conteudo.

Editores (ex.: Quill) ou clientes podem enviar o texto com escape JSON
duplicado,
gravando no banco sequências literais como \\" em vez de aspas normais.
"""

import json


def normalizar_conteudo_html(valor: str | None) -> str:
    """Remove escape JSON duplicado de HTML armazenado no banco.

    Args:
        valor: conteúdo HTML bruto ou None.

    Returns:
        Texto resultante da operação.
    """
    if not valor:
        return valor or ""

    texto = str(valor).strip()

    if len(texto) >= 2 and texto[0] == '"' and texto.endswith('"'):
        try:
            decodificado = json.loads(texto)
            if isinstance(decodificado, str):
                texto = decodificado
        except json.JSONDecodeError:
            pass

    anterior = None
    while anterior != texto and '\\"' in texto:
        anterior = texto
        texto = texto.replace('\\"', '"')

    return texto.replace("\\'", "'")
