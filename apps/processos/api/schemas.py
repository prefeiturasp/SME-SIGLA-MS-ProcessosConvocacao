"""Documentação OpenAPI das operações de processos de convocação."""

from __future__ import annotations

from cargos.api.schemas import (
    EXEMPLO_CARGO,
    NOME_CARGO_EXEMPLO,
    UUID_CARGO_EXEMPLO,
)
from core.openapi import (
    DESCRICAO_PROCESSO_EXEMPLO,
    ERRO_REQUISICAO,
    RESPOSTA_NAO_ENCONTRADO,
    UUID_PROCESSO_EXEMPLO,
    exemplos_requisicao,
    resposta,
    respostas,
)
from core.serializers import ErroDetalheSerializer, ErrosValidacaoSerializer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    PolymorphicProxySerializer,
    extend_schema,
)
from processos.constants import (
    ERROR_CANDIDATOS_PENDENTES_ESCOLHA,
    ERROR_PROCESSO_JA_CANCELADO,
    ERROR_PROCESSO_JA_FINALIZADO,
    ERROR_PROCESSO_NAO_PODE_EDITAR,
    PROCESSO_STATUS_CHOICES,
    TIPO_ESCOLHA_CHOICES,
)
from processos.serializers import (
    FiltrosProcessosSerializer,
    HistoricoCandidatosItemSerializer,
    HistoricoCandidatosRequisicaoSerializer,
    ProcessoConvocacaoCreateSerializer,
    ProcessoConvocacaoPaginadoSerializer,
    ProcessoConvocacaoPassoSerializer,
    ProcessoConvocacaoSelectSerializer,
    ProcessoConvocacaoSerializer,
    ProcessoConvocacaoUpdateSerializer,
)
from processos.utils import TAMANHO_PAGINA_PADRAO

TAG_PROCESSOS = "Processos de convocação"

UUID_CONCURSO_EXEMPLO = "7e6d5c4b-3a2f-4e1d-9c8b-7a6f5e4d3c2b"
NOME_CONCURSO_EXEMPLO = "Concurso Professor de Educação Infantil 2025"

EXEMPLO_DADOS_PROCESSO = {
    "concurso_nome": NOME_CONCURSO_EXEMPLO,
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
    "descricao": DESCRICAO_PROCESSO_EXEMPLO,
    "tipo_escolha": "NOVA_AUTORIZACAO",
    "status": "EM_ANDAMENTO",
    "data_convocacao": "2026-09-15T09:00:00-03:00",
    "data_corte_vagas": "2026-09-10T23:59:00-03:00",
}

EXEMPLO_PROCESSO = {
    "uuid": UUID_PROCESSO_EXEMPLO,
    **EXEMPLO_DADOS_PROCESSO,
    "passo": 4,
    "cargos_processo": [EXEMPLO_CARGO],
    "criado_em": "2026-09-01T10:00:00-03:00",
    "atualizado_em": "2026-09-02T08:30:00-03:00",
}

EXEMPLO_PROCESSO_FINALIZADO = {**EXEMPLO_PROCESSO, "status": "FINALIZADO"}

EXEMPLO_PROCESSO_CRIADO = {
    "uuid": UUID_PROCESSO_EXEMPLO,
    **EXEMPLO_DADOS_PROCESSO,
    "status": "PENDENTE",
    "passo": 1,
}

EXEMPLO_PROCESSO_LISTADO = {
    "uuid": UUID_PROCESSO_EXEMPLO,
    **EXEMPLO_DADOS_PROCESSO,
    "passo": 4,
    "quantidade_cargos": 1,
    "pode_deletar": False,
    "criado_em": "2026-09-01T10:00:00-03:00",
}

EXEMPLO_PAGINA = {
    "links": {"next": None, "previous": None},
    "count": 1,
    "page": 1,
    "page_size": TAMANHO_PAGINA_PADRAO,
    "results": [EXEMPLO_PROCESSO_LISTADO],
}

EXEMPLO_OPCAO_PROCESSO = {
    "value": UUID_PROCESSO_EXEMPLO,
    "label": DESCRICAO_PROCESSO_EXEMPLO,
    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
    "status": "EM_ANDAMENTO",
}

EXEMPLO_FILTROS = {
    "concursos": [
        {"value": UUID_CONCURSO_EXEMPLO, "label": NOME_CONCURSO_EXEMPLO}
    ],
    "cargos": [{"value": UUID_CARGO_EXEMPLO, "label": NOME_CARGO_EXEMPLO}],
    "tipos_escolha": [
        {"value": codigo, "label": rotulo}
        for codigo, rotulo in TIPO_ESCOLHA_CHOICES
    ],
}

EXEMPLO_HISTORICO = {
    "descricao": DESCRICAO_PROCESSO_EXEMPLO,
    "data_convocacao": "2026-09-15T12:00:00+00:00",
    "candidatos": {"total": 188, "geral": 150, "nna": 30, "pcd": 8},
    "escolha": {"total": 170, "geral": 138, "nna": 26, "pcd": 6},
    "nao-escolha": {"total": 12, "geral": 8, "nna": 3, "pcd": 1},
    "reconvocacao": {"total": 6, "geral": 4, "nna": 1, "pcd": 1},
}

ERRO_PROCESSO_FINALIZADO = {"detail": ERROR_PROCESSO_NAO_PODE_EDITAR}
ERRO_CAMPO_OBRIGATORIO = {"descricao": ["Este campo é obrigatório."]}

LISTAGEM_PROCESSOS = PolymorphicProxySerializer(
    component_name="ProcessoConvocacaoListagem",
    serializers=[
        ProcessoConvocacaoPaginadoSerializer,
        ProcessoConvocacaoSelectSerializer(many=True),
    ],
    resource_type_field_name=None,
    many=False,
)

PARAMETRO_UUID = OpenApiParameter(
    name="uuid",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
    description="UUID do processo de convocação.",
)

PARAMETROS_LISTAGEM = [
    OpenApiParameter(
        name="concurso_uuid",
        type=OpenApiTypes.UUID,
        description="Retorna apenas os processos do concurso informado.",
    ),
    OpenApiParameter(
        name="status",
        type=OpenApiTypes.STR,
        enum=[codigo for codigo, _ in PROCESSO_STATUS_CHOICES],
        description="Retorna apenas os processos na situação informada.",
    ),
    OpenApiParameter(
        name="cargo_uuid",
        type=OpenApiTypes.UUID,
        description=(
            "Retorna apenas os processos que têm o cargo informado "
            "(`cargo_uuid` do cargo). Um valor que não seja UUID é ignorado."
        ),
    ),
    OpenApiParameter(
        name="data_convocacao_inicio",
        type=OpenApiTypes.DATE,
        description=(
            "Data inicial da convocação, inclusive, no formato "
            "`AAAA-MM-DD`. Um valor em outro formato é ignorado."
        ),
    ),
    OpenApiParameter(
        name="data_convocacao_fim",
        type=OpenApiTypes.DATE,
        description=(
            "Data final da convocação, inclusive, no formato `AAAA-MM-DD`. "
            "Um valor em outro formato é ignorado."
        ),
    ),
    OpenApiParameter(
        name="search",
        type=OpenApiTypes.STR,
        description=(
            "Busca por trecho do nome do concurso ou da descrição do "
            "processo."
        ),
    ),
    OpenApiParameter(
        name="ordering",
        type=OpenApiTypes.STR,
        description=(
            "Campo de ordenação: `data_convocacao`, `data_corte_vagas` ou "
            "`criado_em`. Prefixe com `-` para ordem decrescente e separe "
            "vários campos por vírgula. Padrão: `-criado_em`."
        ),
    ),
    OpenApiParameter(
        name="page",
        type=OpenApiTypes.INT,
        description=(
            "Número da página, a partir de 1. Sem efeito com "
            "`formato=select`."
        ),
    ),
    OpenApiParameter(
        name="page_size",
        type=OpenApiTypes.INT,
        description=(
            "Quantidade de processos por página. Padrão: "
            f"{TAMANHO_PAGINA_PADRAO}. Sem efeito com `formato=select`."
        ),
    ),
    OpenApiParameter(
        name="formato",
        type=OpenApiTypes.STR,
        enum=["select"],
        description=(
            "Com `select`, a resposta deixa de ser paginada e traz a lista "
            "simples de `value` e `label`, para preencher campos de seleção."
        ),
    ),
]

RESPOSTA_PROCESSO = resposta(
    ProcessoConvocacaoSerializer,
    "Processo de convocação com os cargos vinculados.",
    {"Processo em andamento": EXEMPLO_PROCESSO},
)

RESPOSTA_PROCESSO_ATUALIZADO = resposta(
    ProcessoConvocacaoUpdateSerializer,
    "Dados do processo após a atualização.",
    {"Processo atualizado": EXEMPLO_DADOS_PROCESSO},
)

RESPOSTA_ATUALIZACAO_RECUSADA = resposta(
    ERRO_REQUISICAO,
    "Processo finalizado ou dados inválidos.",
    {
        "Processo finalizado": ERRO_PROCESSO_FINALIZADO,
        "Dados inválidos": ERRO_CAMPO_OBRIGATORIO,
    },
)

OPERACOES_PROCESSOS = {
    "list": extend_schema(
        operation_id="listar_processos_convocacao",
        summary="Listar processos de convocação",
        description=(
            "Lista os processos de convocação ativos, do mais recente para "
            "o mais antigo. Os filtros podem ser combinados.\n\n"
            "Com `formato=select` a resposta não é paginada: vem a lista "
            "simples usada para preencher campos de seleção, com os mesmos "
            "filtros aplicados."
        ),
        parameters=PARAMETROS_LISTAGEM,
        responses=respostas(
            {
                200: resposta(
                    LISTAGEM_PROCESSOS,
                    (
                        "Página de processos ou, com `formato=select`, "
                        "lista simples de opções."
                    ),
                    {
                        "Lista paginada": EXEMPLO_PAGINA,
                        "Formato select": [EXEMPLO_OPCAO_PROCESSO],
                    },
                ),
                400: resposta(
                    ErrosValidacaoSerializer,
                    "Filtro `concurso_uuid` ou `status` com valor inválido.",
                    {
                        "Situação inexistente": {
                            "status": [
                                "Faça uma escolha válida. XYZ não é uma "
                                "das escolhas disponíveis."
                            ]
                        }
                    },
                ),
                404: resposta(
                    ErroDetalheSerializer,
                    "Página além da última.",
                    {"Página inexistente": {"detail": "Página inválida."}},
                ),
            }
        ),
    ),
    "create": extend_schema(
        operation_id="criar_processo_convocacao",
        summary="Criar processo de convocação",
        description=(
            "Cria um processo de convocação para um concurso. Apenas "
            "`concurso_uuid`, `concurso_nome` e `descricao` são "
            "obrigatórios; os demais campos assumem os valores padrão.\n\n"
            "Ao criar, o serviço avisa o MS-Concursos de que o concurso "
            "está em andamento. Uma falha de comunicação nesse aviso é "
            "registrada em log e não impede a criação."
        ),
        request=ProcessoConvocacaoCreateSerializer,
        examples=exemplos_requisicao(
            {
                "Nova convocação": {
                    "concurso_uuid": UUID_CONCURSO_EXEMPLO,
                    "concurso_nome": NOME_CONCURSO_EXEMPLO,
                    "descricao": DESCRICAO_PROCESSO_EXEMPLO,
                    "tipo_escolha": "NOVA_AUTORIZACAO",
                    "data_convocacao": "2026-09-15T09:00:00-03:00",
                    "data_corte_vagas": "2026-09-10T23:59:00-03:00",
                }
            }
        ),
        responses=respostas(
            {
                201: resposta(
                    ProcessoConvocacaoCreateSerializer,
                    "Processo criado.",
                    {"Processo criado": EXEMPLO_PROCESSO_CRIADO},
                ),
                400: resposta(
                    ErrosValidacaoSerializer,
                    "Dados inválidos.",
                    {
                        "Dados inválidos": {
                            "concurso_uuid": ["Must be a valid UUID."],
                            **ERRO_CAMPO_OBRIGATORIO,
                        }
                    },
                ),
            }
        ),
    ),
    "retrieve": extend_schema(
        operation_id="detalhar_processo_convocacao",
        summary="Detalhar processo de convocação",
        description=(
            "Retorna um processo de convocação ativo com os cargos "
            "vinculados."
        ),
        parameters=[PARAMETRO_UUID],
        responses=respostas(
            {200: RESPOSTA_PROCESSO, 404: RESPOSTA_NAO_ENCONTRADO}
        ),
    ),
    "update": extend_schema(
        operation_id="atualizar_processo_convocacao",
        summary="Atualizar processo de convocação",
        description=(
            "Atualiza os dados do processo. `concurso_uuid`, "
            "`concurso_nome` e `descricao` são obrigatórios; os demais "
            "campos, se omitidos, permanecem como estão. Processos "
            "finalizados não podem ser alterados."
        ),
        parameters=[PARAMETRO_UUID],
        request=ProcessoConvocacaoUpdateSerializer,
        examples=exemplos_requisicao(
            {"Atualização completa": EXEMPLO_DADOS_PROCESSO}
        ),
        responses=respostas(
            {
                200: RESPOSTA_PROCESSO_ATUALIZADO,
                400: RESPOSTA_ATUALIZACAO_RECUSADA,
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
    "partial_update": extend_schema(
        operation_id="atualizar_parcial_processo_convocacao",
        summary="Atualizar parcialmente processo de convocação",
        description=(
            "Atualiza apenas os campos enviados. Processos finalizados não "
            "podem ser alterados."
        ),
        parameters=[PARAMETRO_UUID],
        request=ProcessoConvocacaoUpdateSerializer,
        examples=exemplos_requisicao(
            {
                "Alterar descrição e data": {
                    "descricao": "1ª convocação — retificada",
                    "data_convocacao": "2026-09-22T09:00:00-03:00",
                }
            }
        ),
        responses=respostas(
            {
                200: RESPOSTA_PROCESSO_ATUALIZADO,
                400: RESPOSTA_ATUALIZACAO_RECUSADA,
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
    "destroy": extend_schema(
        operation_id="excluir_processo_convocacao",
        summary="Excluir processo de convocação",
        description=(
            "Exclui o processo de forma lógica: ele deixa de aparecer nas "
            "consultas e seus cargos são removidos. Só é permitido para "
            "processos que não estão em andamento nem finalizados.\n\n"
            "Antes de inativar o processo, o serviço exclui as agendas no "
            "MS-Agenda, desconvoca os candidatos no MS-Candidatos e exclui "
            "os lotes de vagas no MS-Escolhas, nessa ordem. Se uma dessas "
            "chamadas falhar, a exclusão é interrompida com 400 e as etapas "
            "já concluídas não são desfeitas. Quando o concurso fica sem "
            "processos ativos, o MS-Concursos é avisado de que o concurso "
            "está completo."
        ),
        parameters=[PARAMETRO_UUID],
        responses=respostas(
            {
                204: resposta(None, "Processo excluído."),
                400: resposta(
                    ErroDetalheSerializer,
                    (
                        "Processo em andamento ou finalizado, ou falha em "
                        "um microsserviço dependente."
                    ),
                    {
                        "Processo em andamento ou finalizado": {
                            "detail": "Processo não pode ser deletado."
                        },
                        "Falha no MS-Agenda": {
                            "detail": (
                                "MS-Agenda retornou status 503 ao excluir "
                                "agendas: Service Unavailable"
                            )
                        },
                    },
                ),
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
    "finalizar": extend_schema(
        operation_id="finalizar_processo_convocacao",
        summary="Finalizar processo de convocação",
        description=(
            "Finaliza um processo em andamento. A requisição não tem "
            "corpo.\n\n"
            "A finalização só acontece quando todos os candidatos "
            "convocados nos cargos do processo têm registro no MS-Escolhas: "
            "escolha de vaga, não escolha ou reconvocação."
        ),
        parameters=[PARAMETRO_UUID],
        request=None,
        responses=respostas(
            {
                200: resposta(
                    ProcessoConvocacaoSerializer,
                    "Processo finalizado.",
                    {"Processo finalizado": EXEMPLO_PROCESSO_FINALIZADO},
                ),
                400: resposta(
                    ErroDetalheSerializer,
                    "O processo não pode ser finalizado.",
                    {
                        "Já finalizado": {
                            "detail": ERROR_PROCESSO_JA_FINALIZADO
                        },
                        "Já cancelado": {
                            "detail": ERROR_PROCESSO_JA_CANCELADO
                        },
                        "Não está em andamento": {
                            "detail": (
                                "Apenas processos em andamento podem ser "
                                "finalizados."
                            )
                        },
                        "Candidatos sem escolha": {
                            "detail": ERROR_CANDIDATOS_PENDENTES_ESCOLHA
                        },
                        "Falha ao consultar o MS-Escolhas": {
                            "detail": (
                                "Erro ao consultar escolhas dos candidatos."
                            )
                        },
                    },
                ),
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
    "atualizar_passo": extend_schema(
        operation_id="atualizar_passo_processo_convocacao",
        summary="Atualizar a etapa do processo",
        description=(
            "Registra a etapa do fluxo de criação em que o processo está. "
            "Aceita qualquer etapa de 1 a 4, inclusive anterior à atual, e "
            "não depende da situação do processo."
        ),
        parameters=[PARAMETRO_UUID],
        request=ProcessoConvocacaoPassoSerializer,
        examples=exemplos_requisicao({"Avançar para a etapa 2": {"passo": 2}}),
        responses=respostas(
            {
                200: RESPOSTA_PROCESSO,
                400: resposta(
                    ErrosValidacaoSerializer,
                    "Etapa fora do intervalo de 1 a 4.",
                    {
                        "Etapa inválida": {
                            "passo": ['"9" não é um escolha válido.']
                        }
                    },
                ),
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
    "filtros": extend_schema(
        operation_id="listar_filtros_processos_convocacao",
        summary="Listar opções de filtro",
        description=(
            "Retorna as opções para os filtros da listagem de processos: "
            "concursos que têm processo de convocação, cargos vinculados a "
            "processos e tipos de escolha."
        ),
        responses=respostas(
            {
                200: resposta(
                    FiltrosProcessosSerializer,
                    "Opções de filtro.",
                    {"Opções de filtro": EXEMPLO_FILTROS},
                )
            }
        ),
    ),
    "historico_candidatos": extend_schema(
        operation_id="consultar_historico_candidatos",
        summary="Consultar histórico de candidatos por processo",
        description=(
            "Para cada processo informado, retorna o total de habilitados "
            "convocados (MS-Candidatos) e quantos deles têm escolha de "
            "vaga, não escolha ou reconvocação registrada (MS-Escolhas), "
            "com quebra por categoria: geral, NNA e PCD.\n\n"
            "UUIDs desconhecidos ou de processos inativos são ignorados; "
            "se nenhum processo for encontrado, a resposta é uma lista "
            "vazia. Falhas nos microsserviços consultados resultam em 400."
        ),
        request=HistoricoCandidatosRequisicaoSerializer,
        examples=exemplos_requisicao(
            {
                "Dois processos": {
                    "processos_uuids": [
                        UUID_PROCESSO_EXEMPLO,
                        "a9b8c7d6-e5f4-4a3b-8c2d-1e0f9a8b7c6d",
                    ]
                }
            }
        ),
        responses=respostas(
            {
                200: resposta(
                    HistoricoCandidatosItemSerializer(many=True),
                    "Histórico de cada processo encontrado.",
                    {"Histórico de um processo": EXEMPLO_HISTORICO},
                ),
                400: resposta(
                    ErroDetalheSerializer,
                    (
                        "Lista de processos ausente ou vazia, ou falha ao "
                        "consultar os microsserviços."
                    ),
                    {
                        "Lista ausente ou vazia": {
                            "detail": (
                                "processos_uuids é obrigatório e deve ser "
                                "uma lista"
                            )
                        },
                        "Falha ao montar o histórico": {
                            "detail": (
                                "Erro ao montar histórico de candidatos."
                            )
                        },
                    },
                ),
            }
        ),
    ),
}
