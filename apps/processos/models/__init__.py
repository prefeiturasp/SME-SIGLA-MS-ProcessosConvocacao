"""Models do app processos."""

from core.models import BaseModel
from .constants import *
from .processo_convocacao import ProcessoConvocacao

__all__ = [
    "BaseModel",
    "ProcessoConvocacao",
    "PROCESSO_STATUS_CHOICES",
    "TIPO_ESCOLHA_CHOICES",
    "MIN_PRIORIDADE",
    "MAX_PRIORIDADE",
    "MIN_VAGAS",
    "MAX_VAGAS",
]
