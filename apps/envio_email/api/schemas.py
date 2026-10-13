"""Documentação OpenAPI das operações de envio e conteúdo de e-mail."""

from __future__ import annotations

from core.openapi import (
    DESCRICAO_PROCESSO_EXEMPLO,
    RESPOSTA_NAO_ENCONTRADO,
    UUID_PROCESSO_EXEMPLO,
    exemplos_requisicao,
    resposta,
    respostas,
)
from core.serializers import ErroDetalheSerializer, ErrosValidacaoSerializer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from envio_email.models.envio_email import (
    ASSUNTO_POR_TIPO,
    ENVIO_EMAIL_TIPO_CHOICES,
    TIPO_CONVOCACAO,
)
from envio_email.serializers import (
    EnvioEmailConteudoSerializer,
    EnvioEmailConteudoUpdateSerializer,
    EnvioEmailDetalheSerializer,
    EnvioEmailEnvioSerializer,
    EnvioEmailIniciadoSerializer,
    EnvioEmailSerializer,
)

TAG_ENVIO_EMAIL = "Envio de e-mail"
TAG_CONTEUDO_EMAIL = "Conteúdo de e-mail"

UUID_ENVIO_EXEMPLO = "2c9a1f7e-5d3b-4a8c-9e6f-1b0d2c3e4f5a"
MENSAGEM_ENVIO_INICIADO = "Processamento de envio iniciado com sucesso."

CORPO_EXEMPLO = (
    "<p>Você foi convocado(a) para o cargo [[cargo]], classificação "
    "[[classificacao]].</p>"
)
CORPO_ENVIADO_EXEMPLO = (
    "<p>Você foi convocado(a) para o cargo Professor de Educação "
    "Infantil, classificação 12.</p>"
)

EXEMPLO_ENVIO = {
    "uuid": UUID_ENVIO_EXEMPLO,
    "processo_nome": DESCRICAO_PROCESSO_EXEMPLO,
    "processo_uuid": UUID_PROCESSO_EXEMPLO,
    "tipo": TIPO_CONVOCACAO,
    "criado_em": "2026-09-12T14:20:00-03:00",
    "quantidade_candidatos": 188,
}

EXEMPLO_ENVIO_DETALHE = {
    **EXEMPLO_ENVIO,
    "candidatos": [
        {
            "nome": "Maria Aparecida da Silva",
            "rf": "1234567",
            "email": "maria.silva@exemplo.test",
            "status": "SUCESSO",
            "status_detalhe": "",
            "conteudo": CORPO_ENVIADO_EXEMPLO,
        },
        {
            "nome": "João Pereira dos Santos",
            "rf": "",
            "email": "joao.santos@exemplo.test",
            "status": "PENDENTE",
            "status_detalhe": "",
            "conteudo": CORPO_ENVIADO_EXEMPLO,
        },
    ],
}

EXEMPLO_REQUISICAO_ENVIO = {
    "processo_uuid": UUID_PROCESSO_EXEMPLO,
    "processo_nome": DESCRICAO_PROCESSO_EXEMPLO,
    "tipo": TIPO_CONVOCACAO,
}

EXEMPLO_CONTEUDO = {
    "uuid": "8a7b6c5d-4e3f-4a2b-9c1d-0e9f8a7b6c5d",
    "tipo": TIPO_CONVOCACAO,
    "tipo_display": "Convocação",
    "assunto": ASSUNTO_POR_TIPO[TIPO_CONVOCACAO],
    "conteudo": CORPO_EXEMPLO,
    "conteudo_gabarito": CORPO_EXEMPLO,
    "criado_em": "2026-08-20T09:00:00-03:00",
    "atualizado_em": "2026-09-05T16:45:00-03:00",
}

EXEMPLO_CONTEUDO_ATUALIZADO = {
    "assunto": ASSUNTO_POR_TIPO[TIPO_CONVOCACAO],
    "conteudo": CORPO_EXEMPLO,
    "conteudo_gabarito": CORPO_EXEMPLO,
}

PARAMETRO_UUID_ENVIO = OpenApiParameter(
    name="uuid",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
    description="UUID do envio.",
)

PARAMETRO_UUID_CONTEUDO = OpenApiParameter(
    name="uuid",
    type=OpenApiTypes.UUID,
    location=OpenApiParameter.PATH,
    description="UUID do conteúdo de e-mail.",
)

PARAMETRO_TIPO = OpenApiParameter(
    name="tipo",
    type=OpenApiTypes.STR,
    enum=[codigo for codigo, _ in ENVIO_EMAIL_TIPO_CHOICES],
    description="Retorna apenas o conteúdo do tipo de envio informado.",
)

RESPOSTA_CONTEUDO = resposta(
    EnvioEmailConteudoSerializer,
    "Conteúdo de e-mail.",
    {"Conteúdo de convocação": EXEMPLO_CONTEUDO},
)

OPERACOES_ENVIO_EMAIL = {
    "list": extend_schema(
        operation_id="listar_envios_email",
        summary="Listar envios de e-mail",
        description=(
            "Retorna o histórico de envios, do mais recente para o mais "
            "antigo. A lista não é paginada."
        ),
        filters=False,
        responses=respostas(
            {
                200: resposta(
                    EnvioEmailSerializer(many=True),
                    "Envios realizados.",
                    {"Envio de convocação": EXEMPLO_ENVIO},
                )
            }
        ),
    ),
    "create": extend_schema(
        operation_id="iniciar_envio_email",
        summary="Iniciar envio de e-mail aos convocados",
        description=(
            "Registra o envio e enfileira um e-mail para cada habilitado "
            "convocado do processo que tenha e-mail cadastrado, a partir "
            "dos dados do MS-Candidatos. A resposta volta assim que os "
            "e-mails são enfileirados: o envio é assíncrono e o resultado "
            "por candidato fica disponível no detalhe do envio.\n\n"
            "`conteudo` aceita os marcadores `[[cargo]]` e "
            "`[[classificacao]]`, substituídos pelos dados de cada "
            "candidato. Sem `conteudo`, vale o conteúdo salvo para o tipo "
            "e, na falta dele, o gabarito. Sem `assunto`, vale o assunto "
            "padrão do tipo."
        ),
        request=EnvioEmailEnvioSerializer,
        examples=exemplos_requisicao(
            {
                "Com o conteúdo salvo": EXEMPLO_REQUISICAO_ENVIO,
                "Com assunto e corpo próprios": {
                    **EXEMPLO_REQUISICAO_ENVIO,
                    "assunto": "Convocação para escolha de vaga",
                    "conteudo": CORPO_EXEMPLO,
                },
            }
        ),
        responses=respostas(
            {
                200: resposta(
                    EnvioEmailIniciadoSerializer,
                    "Envio registrado e e-mails enfileirados.",
                    {
                        "Envio iniciado": {
                            "detail": MENSAGEM_ENVIO_INICIADO,
                            "envio_email_uuid": UUID_ENVIO_EXEMPLO,
                            **EXEMPLO_REQUISICAO_ENVIO,
                            "quantidade_candidatos": 188,
                        }
                    },
                ),
                400: resposta(
                    ErrosValidacaoSerializer,
                    "Dados inválidos ou processo inexistente.",
                    {
                        "Dados inválidos": {
                            "processo_nome": ["Este campo é obrigatório."],
                            "tipo": ['"X" não é um escolha válido.'],
                        },
                        "Processo inexistente": {
                            "processo_uuid": [
                                "Processo de convocação não encontrado."
                            ]
                        },
                    },
                ),
                500: resposta(
                    ErroDetalheSerializer,
                    (
                        "Falha ao iniciar o envio, por exemplo ao consultar "
                        "os habilitados no MS-Candidatos. `detail` traz a "
                        "mensagem do erro."
                    ),
                    {
                        "MS-Candidatos indisponível": {
                            "detail": (
                                "503 Server Error: Service Unavailable for "
                                "url: <URL do MS-Candidatos>"
                            )
                        }
                    },
                ),
            }
        ),
    ),
    "retrieve": extend_schema(
        operation_id="detalhar_envio_email",
        summary="Detalhar envio de e-mail",
        description=(
            "Retorna um envio com a situação por candidato: `PENDENTE` "
            "enquanto o e-mail está na fila, `SUCESSO` ou `ERRO` depois da "
            "tentativa de envio. Em caso de erro, `status_detalhe` traz o "
            "motivo."
        ),
        parameters=[PARAMETRO_UUID_ENVIO],
        responses=respostas(
            {
                200: resposta(
                    EnvioEmailDetalheSerializer,
                    "Envio com a situação de cada candidato.",
                    {"Envio em andamento": EXEMPLO_ENVIO_DETALHE},
                ),
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
}

OPERACOES_CONTEUDO_EMAIL = {
    "list": extend_schema(
        operation_id="listar_conteudos_email",
        summary="Listar conteúdos de e-mail",
        description=(
            "Retorna o conteúdo de e-mail de cada tipo de envio, ordenado "
            "pelo tipo. Existe no máximo um conteúdo por tipo e a lista "
            "não é paginada."
        ),
        filters=False,
        parameters=[PARAMETRO_TIPO],
        responses=respostas(
            {
                200: resposta(
                    EnvioEmailConteudoSerializer(many=True),
                    "Conteúdos de e-mail.",
                    {"Conteúdo de convocação": EXEMPLO_CONTEUDO},
                )
            }
        ),
    ),
    "retrieve": extend_schema(
        operation_id="detalhar_conteudo_email",
        summary="Detalhar conteúdo de e-mail",
        description="Retorna o conteúdo de e-mail de um tipo de envio.",
        parameters=[PARAMETRO_UUID_CONTEUDO],
        responses=respostas(
            {200: RESPOSTA_CONTEUDO, 404: RESPOSTA_NAO_ENCONTRADO}
        ),
    ),
    "partial_update": extend_schema(
        operation_id="atualizar_conteudo_email",
        summary="Atualizar conteúdo de e-mail",
        description=(
            "Atualiza o assunto, o corpo salvo e o gabarito de um conteúdo "
            "de e-mail. Apenas os campos enviados são alterados; o tipo de "
            "envio não muda."
        ),
        parameters=[PARAMETRO_UUID_CONTEUDO],
        request=EnvioEmailConteudoUpdateSerializer,
        examples=exemplos_requisicao(
            {
                "Alterar assunto e corpo": {
                    "assunto": ASSUNTO_POR_TIPO[TIPO_CONVOCACAO],
                    "conteudo": CORPO_EXEMPLO,
                }
            }
        ),
        responses=respostas(
            {
                200: resposta(
                    EnvioEmailConteudoUpdateSerializer,
                    "Conteúdo após a atualização.",
                    {"Conteúdo atualizado": EXEMPLO_CONTEUDO_ATUALIZADO},
                ),
                400: resposta(
                    ErrosValidacaoSerializer,
                    "Dados inválidos.",
                    {
                        "Corpo em branco": {
                            "conteudo": ["Este campo não pode ser em branco."]
                        }
                    },
                ),
                404: RESPOSTA_NAO_ENCONTRADO,
            }
        ),
    ),
}
