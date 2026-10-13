"""Blocos compartilhados da documentação OpenAPI do microsserviço."""

from __future__ import annotations

from typing import Any

from core.serializers import (
    ErroAcessoSerializer,
    ErroDetalheSerializer,
    ErrosValidacaoSerializer,
)
from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    Direction,
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    PolymorphicProxySerializer,
)

UUID_PROCESSO_EXEMPLO = "c1a7e0d2-4b3f-4a6e-8d9c-0f1e2d3c4b5a"
DESCRICAO_PROCESSO_EXEMPLO = "1ª convocação — Professor de Educação Infantil"

CABECALHO_CORRELACAO = "X-Correlation-ID"

PARAMETROS_CORRELACAO = [
    OpenApiParameter(
        name=CABECALHO_CORRELACAO,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.HEADER,
        required=False,
        description=(
            "Identificador de correlação da requisição, gravado nos logs e "
            "repassado aos demais microsserviços. Opcional: se ausente, o "
            "serviço gera um UUID."
        ),
    ),
    OpenApiParameter(
        name=CABECALHO_CORRELACAO,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.HEADER,
        response=True,
        description=(
            "Identificador de correlação usado no atendimento da requisição."
        ),
    ),
]


class EsquemaAutomatico(AutoSchema):
    """Schema padrão das views, com o cabeçalho de correlação."""

    def get_override_parameters(self) -> list[Any]:
        """Acrescenta ``X-Correlation-ID`` à requisição e às respostas."""
        return [*super().get_override_parameters(), *PARAMETROS_CORRELACAO]


class ErrosValidacaoExtension(OpenApiSerializerExtension):
    """Descreve ``ErrosValidacaoSerializer`` como mapa campo → mensagens."""

    target_class = ErrosValidacaoSerializer

    def map_serializer(
        self, auto_schema: AutoSchema, direction: Direction
    ) -> dict[str, Any]:
        """Retorna o schema do mapa de erros de validação."""
        return {
            "type": "object",
            "description": (
                "Erros de validação. Cada chave é o nome de um campo "
                "inválido (ou `non_field_errors`) e o valor é a lista de "
                "mensagens. Em campos que são listas de objetos, o valor é "
                "uma lista com um objeto de erros por item enviado."
            ),
            "additionalProperties": {
                "type": "array",
                "items": {
                    "oneOf": [
                        {"type": "string"},
                        {"type": "object", "additionalProperties": True},
                    ]
                },
            },
        }


ERRO_REQUISICAO = PolymorphicProxySerializer(
    component_name="ErroRequisicao",
    serializers=[ErroDetalheSerializer, ErrosValidacaoSerializer],
    resource_type_field_name=None,
)


def resposta(
    modelo: Any, descricao: str, exemplos: dict[str, Any] | None = None
) -> OpenApiResponse:
    """Monta uma resposta documentada com exemplos nomeados.

    Args:
        modelo: Serializer que descreve o corpo, ou ``None`` se não há corpo.
        descricao: Texto exibido para o código de resposta.
        exemplos: Valores de exemplo, indexados pelo nome do exemplo.

    Returns:
        Resposta pronta para o ``responses`` de ``extend_schema``.
    """
    return OpenApiResponse(
        response=modelo,
        description=descricao,
        examples=[
            OpenApiExample(nome, value=valor)
            for nome, valor in (exemplos or {}).items()
        ],
    )


def exemplos_requisicao(exemplos: dict[str, Any]) -> list[OpenApiExample]:
    """Monta exemplos nomeados para o corpo da requisição.

    Args:
        exemplos: Valores de exemplo, indexados pelo nome do exemplo.

    Returns:
        Exemplos prontos para o ``examples`` de ``extend_schema``.
    """
    return [
        OpenApiExample(nome, value=valor, request_only=True)
        for nome, valor in exemplos.items()
    ]


RESPOSTA_ACESSO_NEGADO = resposta(
    ErroAcessoSerializer,
    (
        "Credencial recusada: token JWT inválido ou expirado, usuário e "
        "senha Basic incorretos ou falha de CSRF em sessão. O serviço "
        "responde 403 nesses casos, e não 401."
    ),
    {
        "Token JWT inválido": {
            "detail": "Given token not valid for any token type",
            "code": "token_not_valid",
            "messages": [
                {
                    "token_class": "AccessToken",
                    "token_type": "access",
                    "message": "Token is invalid",
                }
            ],
        }
    },
)

RESPOSTA_NAO_ENCONTRADO = resposta(
    ErroDetalheSerializer,
    "Registro não encontrado.",
    {"Não encontrado": {"detail": "Não encontrado."}},
)

RESPOSTA_ERRO_INTERNO = resposta(
    None,
    "Erro inesperado no servidor. O corpo não segue um modelo JSON.",
)

RESPOSTAS_COMUNS = {
    403: RESPOSTA_ACESSO_NEGADO,
    500: RESPOSTA_ERRO_INTERNO,
}


def respostas(especificas: dict[int, Any]) -> dict[int, Any]:
    """Junta as respostas da operação às comuns a todo o microsserviço.

    Args:
        especificas: Respostas próprias da operação, por código HTTP.

    Returns:
        Respostas ordenadas por código, incluindo 403 e 500.
    """
    return dict(sorted({**RESPOSTAS_COMUNS, **especificas}.items()))
