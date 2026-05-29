"""
Converte <img src="data:image/...;base64,..."> em anexos inline (cid:).

Clientes de e-mail (Gmail, Outlook etc.) costumam bloquear data URI no corpo HTML.
"""
import base64
import binascii
import logging
import re

from email.mime.image import MIMEImage

logger = logging.getLogger(__name__)

_SRC_DATA_URI = re.compile(
    r'src=(?P<quote>["\'])data:image/(?P<subtype>[\w+.-]+);base64,'
    r'(?P<payload>[A-Za-z0-9+/=\r\n]+)(?P=quote)',
    re.IGNORECASE,
)

_SUBTYPE_MIME = {
    'jpg': 'jpeg',
    'jpeg': 'jpeg',
    'png': 'png',
    'gif': 'gif',
    'webp': 'webp',
}


def converter_imagens_base64_para_cid(html: str) -> tuple[str, list[MIMEImage]]:
    """
    Substitui src data URI por cid: e retorna partes MIME para anexar ao e-mail.
    """
    if not html:
        return html, []

    imagens: list[MIMEImage] = []
    contador = 0

    def substituir(match: re.Match[str]) -> str:
        nonlocal contador
        subtype_raw = match.group('subtype').lower()
        subtype = _SUBTYPE_MIME.get(subtype_raw, subtype_raw)
        if subtype not in _SUBTYPE_MIME.values():
            logger.warning(
                'Subtype de imagem não suportado no e-mail: %s; mantendo data URI',
                subtype_raw,
            )
            return match.group(0)

        payload = re.sub(r'\s+', '', match.group('payload'))
        try:
            dados = base64.b64decode(payload, validate=True)
        except (binascii.Error, ValueError):
            logger.warning('Imagem base64 inválida no HTML do e-mail; mantendo data URI')
            return match.group(0)

        cid = f'email_img_{contador}'
        contador += 1
        mime = MIMEImage(dados, _subtype=subtype)
        ext = 'jpg' if subtype == 'jpeg' else subtype
        mime.add_header('Content-Disposition', 'inline', filename=f'{cid}.{ext}')
        mime.add_header('Content-ID', f'<{cid}>')
        imagens.append(mime)
        quote = match.group('quote')
        return f'src={quote}cid:{cid}{quote}'

    html_novo = _SRC_DATA_URI.sub(substituir, html)
    return html_novo, imagens
