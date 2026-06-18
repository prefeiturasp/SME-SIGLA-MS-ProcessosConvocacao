"""Converte <img src="data:image/...;base64,..."> em anexos inline (cid:).

Clientes de e-mail (Gmail, Outlook etc.) costumam bloquear data URI no corpo
HTML.
"""

import base64
import binascii
import logging
import re
from email.mime.image import MIMEImage

logger = logging.getLogger(__name__)

_SRC_DATA_URI = re.compile(
    r'src=(?P<aspas>["\'])data:image/(?P<subtipo_bruto>[\w+.-]+);base64,'
    r"(?P<dados_base64>[A-Za-z0-9+/=\r\n]+)(?P=aspas)",
    re.IGNORECASE,
)

_SUBTYPE_MIME = {
    "jpg": "jpeg",
    "jpeg": "jpeg",
    "png": "png",
    "gif": "gif",
    "webp": "webp",
}


def converter_imagens_base64_para_cid(
    html: str,
) -> tuple[str, list[MIMEImage]]:
    """Substitui src data URI por cid: e retorna partes MIME para anexar ao."""
    if not html:
        return html, []

    imagens: list[MIMEImage] = []
    contador = 0

    def substituir(match: re.Match[str]) -> str:
        """Substitui src data URI por cid:."""
        nonlocal contador
        subtipo_bruto = match.group("subtipo_bruto").lower()
        subtipo_mime = _SUBTYPE_MIME.get(subtipo_bruto, subtipo_bruto)
        if subtipo_mime not in _SUBTYPE_MIME.values():
            logger.warning(
                "Subtype de imagem não suportado no e-mail: %s; mantendo data URI",  # noqa: E501
                subtipo_bruto,
            )
            return match.group(0)

        dados_base64 = re.sub(r"\s+", "", match.group("dados_base64"))
        try:
            dados = base64.b64decode(dados_base64, validate=True)
        except (binascii.Error, ValueError):
            logger.warning(
                "Imagem base64 inválida no HTML do e-mail; mantendo data URI"
            )
            return match.group(0)

        cid = f"email_img_{contador}"
        contador += 1
        imagem_mime = MIMEImage(dados, _subtype=subtipo_mime)
        ext = "jpg" if subtipo_mime == "jpeg" else subtipo_mime
        imagem_mime.add_header(
            "Content-Disposition", "inline", filename=f"{cid}.{ext}"
        )
        imagem_mime.add_header("Content-ID", f"<{cid}>")
        imagens.append(imagem_mime)
        aspas = match.group("aspas")
        return f"src={aspas}cid:{cid}{aspas}"

    html_novo = _SRC_DATA_URI.sub(substituir, html)
    return html_novo, imagens
