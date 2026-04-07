"""
Constantes e enums para os modelos de processos de convocação.
"""

# Status dos processos
PROCESSO_STATUS_CHOICES = [
    ('PENDENTE', 'Pendente'),
    ('EM_ANDAMENTO', 'Em Andamento'),
    ('FINALIZADO', 'Concluído'),
    ('CANCELADO', 'Cancelado'),
]

# Tipos de escolha
TIPO_ESCOLHA_CHOICES = [
    ('NOVA_AUTORIZACAO', 'Nova Autorização'),
    ('REPOSICAO', 'Reposição'),
    ('RECONVOCAO', 'Reconvocação'),
]

# Constantes para validação
MIN_PRIORIDADE = 1
MAX_PRIORIDADE = 100
MIN_VAGAS = 1
MAX_VAGAS = 10000

# Mensagens de erro
ERROR_VAGAS_INVALIDAS = "Vagas disponíveis devem estar entre 0 e o total de vagas do processo."
ERROR_PRIORIDADE_INVALIDA = "Prioridade deve estar entre 1 e 100."
ERROR_CARGO_JA_EXISTE = "Este cargo já está associado ao processo."
ERROR_CARGO_NAO_ENCONTRADO = "Cargo não encontrado no processo."
ERROR_PROCESSO_JA_FINALIZADO = "Processo já está finalizado."
ERROR_PROCESSO_JA_CANCELADO = "Processo já está cancelado."
ERROR_CANDIDATOS_PENDENTES_ESCOLHA = (
    "Existem candidatos convocados que ainda não fizeram escolha."
)
ERROR_PROCESSO_NAO_PODE_EDITAR = "Processo finalizado não pode ser alterado." 