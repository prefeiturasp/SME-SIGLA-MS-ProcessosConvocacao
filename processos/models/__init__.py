# Models module for processos app
from .base import BaseModel
from .processo_convocacao import ProcessoConvocacao
from .cargo_processo import CargoProcesso
from .envio_email import EnvioEmail
from .envio_email_candidato import EnvioEmailCandidato
from .envio_email_conteudo import EnvioEmailConteudo
from .constants import *

__all__ = [
    'BaseModel',
    'ProcessoConvocacao',
    'CargoProcesso',
    'EnvioEmail',
    'EnvioEmailCandidato',
    'EnvioEmailConteudo',
    # Constants
    'PROCESSO_STATUS_CHOICES',
    'TIPO_ESCOLHA_CHOICES',
    'MIN_PRIORIDADE',
    'MAX_PRIORIDADE',
    'MIN_VAGAS',
    'MAX_VAGAS',
]
