"""Documentação OpenAPI das operações de cargos do processo."""

from __future__ import annotations

from cargos.serializers import (
    CargoProcessoSerializer,
    ErroMensagemSerializer,
    ProcessoCargosDadosSerializer,
    SubstituicaoCargosRespostaSerializer,
)
from core.openapi import (
    ERRO_REQUISICAO,
    RESPOSTA_NAO_ENCONTRADO,
    UUID_PROCESSO_EXEMPLO,
    exemplos_requisicao,
    resposta,
    respostas,
)
from core.serializers import ErroDetalheSerializer, ErrosValidacaoSerializer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from processos.constants import ERROR_PROCESSO_NAO_PODE_EDITAR

TAG_CARGOS = "Cargos do processo"

UUID_VINCULO_EXEMPLO = "5f0c2a4e-8b1d-4f6a-9c3e-2d7b1a0e4c55"
UUID_CARGO_EXEMPLO = "9b2f6c1e-3a4d-4e8f-b7a1-6c5d4e3f2a10"
NOME_CARGO_EXEMPLO = "Professor de Educação Infantil"
UUIDS_CANDIDATOS_EXEMPLO = [
    "0d9e8f7a-6b5c-4d3e-a2f1-b0c9d8e7f6a5",
    "3b2a1c0d-9e8f-4a7b-b6c5-d4e3f2a1b0c9",
]

EXEMPLO_CARGO = {
    "uuid": UUID_VINCULO_EXEMPLO,
    "cargo_nome": NOME_CARGO_EXEMPLO,
    "cargo_uuid": UUID_CARGO_EXEMPLO,
    "cargo_codigo": "3859",
    "processo": UUID_PROCESSO_EXEMPLO,
    "vagas": 120,
    "candidatos_geral": 150,
    "candidatos_pcd": 8,
    "candidatos_nna": 30,
    "total_candidatos": 188,
    "candidatos_uuids": UUIDS_CANDIDATOS_EXEMPLO,
    "criado_em": "2026-09-01T10:15:00-03:00",
    "atualizado_em": "2026-09-02T08:30:00-03:00",
}

EXEMPLO_DADOS_CARGO = {
    "cargo_nome": NOME_CARGO_EXEMPLO,
    "cargo_uuid": UUID_CARGO_EXEMPLO,
    "cargo_codigo": "3859",
    "vagas": 120,
    "candidatos_geral": 150,
    "candidatos_pcd": 8,
    "candidatos_nna": 30,
    "total_candidatos": 188,
    "candidatos_uuids": UUIDS_CANDIDATOS_EXEMPLO,
}

EXEMPLO_SUBSTITUICAO = {
    "success": True,
    "cargos_criados": 1,
    "cargos_atualizados": 1,
    "cargos_removidos": 0,
    "cargos": [EXEMPLO_CARGO],
}

ERRO_PROCESSO_INEXISTENTE = {"error": "Processo de convocação não encontrado"}
ERRO_CARGO_INEXISTENTE = {"error": "Cargo não encontrado para este processo"}
ERRO_PROCESSO_FINALIZADO = {"detail": ERROR_PROCESSO_NAO_PODE_EDITAR}

AVISO_BUSCA_POR_CARGO = (
    "A busca usa apenas o `cargo_uuid`: o `processo_pk` da rota não é "
    "validado nesta operação."
)

PARAMETRO_PROCESSO = OpenApiParameter(
    name="processo_pk",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
    description="UUID do processo de convocação.",
)

PARAMETRO_CARGO = OpenApiParameter(
    name="cargo_uuid",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
    description=(
        "UUID do vínculo cargo–processo (campo `uuid` do cargo). Não é o "
        "`cargo_uuid` do cadastro de cargos."
    ),
)

RESPOSTA_PROCESSO_INEXISTENTE = resposta(
    ErroMensagemSerializer,
    "Processo de convocação não encontrado.",
    {"Processo não encontrado": ERRO_PROCESSO_INEXISTENTE},
)

RESPOSTA_CARGO = resposta(
    CargoProcessoSerializer,
    "Cargo do processo.",
    {"Cargo do processo": EXEMPLO_CARGO},
)

RESPOSTA_CARGO_INVALIDO = resposta(
    ErrosValidacaoSerializer,
    "Dados do cargo inválidos.",
    {"Dados inválidos": {"vagas": ["Um número inteiro válido é exigido."]}},
)

OPERACOES_CARGOS = {
    "list": extend_schema(
        operation_id="listar_cargos_processo",
        summary="Listar cargos do processo",
        description=(
            "Retorna todos os cargos vinculados ao processo, com vagas e "
            "quantitativos de candidatos, ordenados pelo nome do cargo. A "
            "lista não é paginada."
        ),
        filters=False,
        responses=respostas(
            {
                200: resposta(
                    CargoProcessoSerializer(many=True),
                    "Cargos do processo.",
                    {"Cargo do processo": EXEMPLO_CARGO},
                ),
                404: RESPOSTA_PROCESSO_INEXISTENTE,
            }
        ),
    ),
    "create": extend_schema(
        operation_id="substituir_cargos_processo",
        summary="Substituir os cargos do processo",
        description=(
            "Recebe a lista completa de cargos do processo e a aplica em "
            "uma única transação: itens com `uuid` atualizam o cargo já "
            "vinculado, itens sem `uuid` criam um cargo, e cargos "
            "vinculados que não constarem na lista são removidos. "
            "`porcentagem_nna` e `porcentagem_pcd`, quando enviadas, "
            "atualizam o processo.\n\n"
            "Se algum item não puder ser processado, por exemplo um `uuid` "
            "que não pertence ao processo, os demais são gravados e a "
            "resposta vem com status **207** e a lista `erros`. Processos "
            "finalizados não aceitam alteração de cargos."
        ),
        request=ProcessoCargosDadosSerializer,
        examples=exemplos_requisicao(
            {
                "Criar um cargo e atualizar outro": {
                    "porcentagem_nna": 0.2,
                    "porcentagem_pcd": 0.05,
                    "cargos": [
                        {"uuid": UUID_VINCULO_EXEMPLO, **EXEMPLO_DADOS_CARGO},
                        {
                            "cargo_nome": "Auxiliar Técnico de Educação",
                            "cargo_uuid": (
                                "4e5f6a7b-8c9d-4e0f-a1b2-c3d4e5f6a7b8"
                            ),
                            "vagas": 40,
                        },
                    ],
                }
            }
        ),
        responses=respostas(
            {
                200: resposta(
                    SubstituicaoCargosRespostaSerializer,
                    "Todos os cargos enviados foram processados.",
                    {"Substituição concluída": EXEMPLO_SUBSTITUICAO},
                ),
                207: resposta(
                    SubstituicaoCargosRespostaSerializer,
                    (
                        "Parte dos cargos não pôde ser processada. Os "
                        "demais foram gravados."
                    ),
                    {
                        "Cargo que não pertence ao processo": {
                            **EXEMPLO_SUBSTITUICAO,
                            "cargos_criados": 0,
                            "erros": [
                                {
                                    "uuid": (
                                        "7a6b5c4d-3e2f-4a1b-8c9d-0e1f2a3b4c5d"
                                    ),
                                    "erros": ERRO_CARGO_INEXISTENTE["error"],
                                }
                            ],
                        }
                    },
                ),
                400: resposta(
                    ERRO_REQUISICAO,
                    "Processo finalizado ou corpo da requisição inválido.",
                    {
                        "Processo finalizado": ERRO_PROCESSO_FINALIZADO,
                        "Corpo inválido": {
                            "cargos": ["Este campo é obrigatório."]
                        },
                    },
                ),
                404: RESPOSTA_PROCESSO_INEXISTENTE,
            }
        ),
    ),
    "retrieve": extend_schema(
        operation_id="detalhar_cargo_processo",
        summary="Detalhar um cargo do processo",
        description=f"Retorna um cargo vinculado. {AVISO_BUSCA_POR_CARGO}",
        parameters=[PARAMETRO_CARGO],
        responses=respostas(
            {200: RESPOSTA_CARGO, 404: RESPOSTA_NAO_ENCONTRADO}
        ),
    ),
    "update": extend_schema(
        operation_id="atualizar_cargo_processo",
        summary="Atualizar um cargo do processo",
        description=(
            "Atualiza os dados de um cargo vinculado. `processo`, "
            "`cargo_nome` e `cargo_uuid` são obrigatórios; os demais "
            "campos, se omitidos, permanecem como estão. "
            f"{AVISO_BUSCA_POR_CARGO}"
        ),
        parameters=[PARAMETRO_CARGO],
        request=CargoProcessoSerializer,
        examples=exemplos_requisicao(
            {
                "Atualização completa": {
                    "processo": UUID_PROCESSO_EXEMPLO,
                    **EXEMPLO_DADOS_CARGO,
                }
            }
        ),
        responses=respostas(
            {
                200: RESPOSTA_CARGO,
                400: RESPOSTA_CARGO_INVALIDO,
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
    "partial_update": extend_schema(
        operation_id="atualizar_parcial_cargo_processo",
        summary="Atualizar parcialmente um cargo do processo",
        description=(
            "Atualiza apenas os campos enviados de um cargo vinculado. "
            f"{AVISO_BUSCA_POR_CARGO}"
        ),
        parameters=[PARAMETRO_CARGO],
        request=CargoProcessoSerializer,
        examples=exemplos_requisicao({"Ajustar as vagas": {"vagas": 135}}),
        responses=respostas(
            {
                200: RESPOSTA_CARGO,
                400: RESPOSTA_CARGO_INVALIDO,
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
    "destroy": extend_schema(
        operation_id="excluir_cargo_processo",
        summary="Remover um cargo do processo",
        description=(
            "Remove o vínculo do cargo com o processo. Processos "
            "finalizados não aceitam alteração de cargos."
        ),
        parameters=[PARAMETRO_CARGO],
        responses=respostas(
            {
                204: resposta(None, "Cargo removido do processo."),
                400: resposta(
                    ErroDetalheSerializer,
                    "Processo finalizado.",
                    {"Processo finalizado": ERRO_PROCESSO_FINALIZADO},
                ),
                404: resposta(
                    ErroMensagemSerializer,
                    "Processo ou cargo não encontrado.",
                    {
                        "Processo não encontrado": ERRO_PROCESSO_INEXISTENTE,
                        "Cargo não encontrado": ERRO_CARGO_INEXISTENTE,
                    },
                ),
            }
        ),
    ),
}
