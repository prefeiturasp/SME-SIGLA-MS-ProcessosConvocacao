"""Models do app envio_email."""

from .envio_email import (
    ASSUNTO_POR_TIPO,
    ENVIO_EMAIL_TIPO_CHOICES,
    TIPO_CONVOCACAO,
    TIPO_RESULTADOS,
    TIPO_VAGAS,
    EnvioEmail,
)
from .envio_email_candidato import (
    ENVIO_STATUS_CHOICES,
    ENVIO_STATUS_ERRO,
    ENVIO_STATUS_PENDENTE,
    ENVIO_STATUS_SUCESSO,
    EnvioEmailCandidato,
)
from .envio_email_conteudo import EnvioEmailConteudo

__all__ = [
    "EnvioEmail",
    "EnvioEmailCandidato",
    "EnvioEmailConteudo",
    "TIPO_CONVOCACAO",
    "TIPO_VAGAS",
    "TIPO_RESULTADOS",
    "ENVIO_EMAIL_TIPO_CHOICES",
    "ASSUNTO_POR_TIPO",
    "ENVIO_STATUS_PENDENTE",
    "ENVIO_STATUS_SUCESSO",
    "ENVIO_STATUS_ERRO",
    "ENVIO_STATUS_CHOICES",
]
