class AgendaServiceError(Exception):
    """Erro ao chamar o MS-Agenda."""


class CandidatosServiceError(Exception):
    """Erro ao chamar o MS-Candidatos."""


class EscolhasServiceError(Exception):
    """Erro ao chamar o MS-Escolha."""


class ProcessoServiceError(Exception):
    """Erro ao executar operações do processo envolvendo integrações."""
