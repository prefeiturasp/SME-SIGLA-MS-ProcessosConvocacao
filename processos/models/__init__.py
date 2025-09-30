# Models module for processos app
from .base import BaseModel
from .processo_convocacao import ProcessoConvocacao
from .cargo_processo import CargoProcesso
from .constants import *

__all__ = [
    'BaseModel',
    'ProcessoConvocacao', 
    'CargoProcesso',
    # Constants
    'PROCESSO_STATUS_CHOICES',
    'TIPO_ESCOLHA_CHOICES',
    'MIN_PRIORIDADE',
    'MAX_PRIORIDADE',
    'MIN_VAGAS',
    'MAX_VAGAS',
] 