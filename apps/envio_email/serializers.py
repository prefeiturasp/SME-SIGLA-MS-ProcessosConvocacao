"""Serializers do app envio_email."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from envio_email.models import (
    ENVIO_EMAIL_TIPO_CHOICES,
    EnvioEmail,
    EnvioEmailCandidato,
    EnvioEmailConteudo,
)
from envio_email.utils.conteudo_html import normalizar_conteudo_html
from processos.repository import ProcessoConvocacaoRepository
from rest_framework import serializers

MARCADORES = "Aceita os marcadores `[[cargo]]` e `[[classificacao]]`."
AJUDA_CONTEUDO = (
    f"Corpo do e-mail em HTML, salvo para o tipo de envio. {MARCADORES}"
)
AJUDA_GABARITO = (
    "Corpo padrão (gabarito) do e-mail em HTML, usado quando não há "
    f"conteúdo salvo. {MARCADORES}"
)

DESCRICOES_ENVIO = {
    "uuid": {"help_text": "Identificador único do envio (lote de e-mails)."},
    "processo_nome": {
        "help_text": "Nome do processo, exibido no histórico de envios."
    },
    "processo_uuid": {"help_text": "UUID do processo de convocação."},
    "tipo": {"help_text": "Tipo de envio."},
    "criado_em": {"help_text": "Data e hora em que o envio foi iniciado."},
    "quantidade_candidatos": {
        "help_text": (
            "Quantidade de habilitados convocados do processo no momento "
            "do envio, incluindo os que não têm e-mail cadastrado."
        )
    },
}

DESCRICOES_CANDIDATO = {
    "nome": {"help_text": "Nome do candidato."},
    "rf": {
        "help_text": "Registro funcional (RF) do candidato, quando houver."
    },
    "email": {"help_text": "E-mail de destino."},
    "status": {"help_text": "Situação do envio para o candidato."},
    "status_detalhe": {
        "help_text": "Mensagem de erro ou detalhe do envio, quando houver."
    },
    "conteudo": {
        "help_text": (
            "HTML do e-mail enviado ao candidato, já com os marcadores "
            "substituídos."
        )
    },
}

DESCRICOES_CONTEUDO = {
    "uuid": {"help_text": "Identificador único do conteúdo."},
    "tipo": {"help_text": "Tipo de envio ao qual o conteúdo se aplica."},
    "assunto": {
        "help_text": "Assunto salvo para o tipo de envio. Pode ser vazio."
    },
    "criado_em": {"help_text": "Data e hora de criação do registro."},
    "atualizado_em": {
        "help_text": "Data e hora da última atualização do registro."
    },
}


class EnvioEmailEnvioSerializer(serializers.Serializer):
    """Dados para iniciar um envio de e-mail aos convocados."""

    processo_uuid = serializers.UUIDField(
        help_text="UUID do processo de convocação."
    )
    processo_nome = serializers.CharField(
        help_text="Nome do processo, exibido no histórico de envios."
    )
    tipo = serializers.ChoiceField(
        choices=ENVIO_EMAIL_TIPO_CHOICES, help_text="Tipo de envio."
    )
    conteudo = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=(
            f"Corpo do e-mail em HTML. {MARCADORES} Se vazio, usa o "
            "conteúdo salvo para o tipo e, na falta dele, o gabarito."
        ),
    )
    assunto = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=(
            "Assunto do e-mail. Se vazio, usa o assunto padrão do tipo."
        ),
    )

    def validate_processo_uuid(self, value: UUID) -> UUID:
        if not ProcessoConvocacaoRepository.existe_por_uuid(value):
            raise serializers.ValidationError(
                "Processo de convocação não encontrado."
            )
        return value


class EnvioEmailSerializer(serializers.ModelSerializer):
    """Envio de e-mail registrado no histórico."""

    class Meta:
        model = EnvioEmail
        fields = [
            "uuid",
            "processo_nome",
            "processo_uuid",
            "tipo",
            "criado_em",
            "quantidade_candidatos",
        ]
        extra_kwargs = DESCRICOES_ENVIO


class EnvioEmailCandidatoSerializer(serializers.ModelSerializer):
    """Situação do envio de e-mail para um candidato."""

    class Meta:
        model = EnvioEmailCandidato
        fields = [
            "nome",
            "rf",
            "email",
            "status",
            "status_detalhe",
            "conteudo",
        ]
        extra_kwargs = DESCRICOES_CANDIDATO


class EnvioEmailDetalheSerializer(serializers.ModelSerializer):
    """Envio de e-mail com a situação de cada candidato."""

    candidatos = EnvioEmailCandidatoSerializer(
        many=True,
        read_only=True,
        help_text="Situação do envio para cada candidato.",
    )

    class Meta:
        model = EnvioEmail
        fields = [
            "uuid",
            "processo_nome",
            "processo_uuid",
            "tipo",
            "criado_em",
            "quantidade_candidatos",
            "candidatos",
        ]
        extra_kwargs = DESCRICOES_ENVIO


class ConteudoHtmlField(serializers.CharField):
    """Retorna e persiste HTML sem escape JSON duplicado."""

    def to_representation(self, value: str | None) -> str | None:
        if value is None:
            return value
        return normalizar_conteudo_html(value)

    def to_internal_value(self, data: Any) -> str:
        return normalizar_conteudo_html(super().to_internal_value(data))


class EnvioEmailConteudoSerializer(serializers.ModelSerializer):
    """Conteúdo de e-mail de um tipo de envio."""

    tipo_display = serializers.CharField(
        source="get_tipo_display",
        read_only=True,
        help_text="Nome legível do tipo de envio.",
    )
    conteudo = ConteudoHtmlField(help_text=AJUDA_CONTEUDO)
    conteudo_gabarito = ConteudoHtmlField(help_text=AJUDA_GABARITO)

    class Meta:
        model = EnvioEmailConteudo
        fields = [
            "uuid",
            "tipo",
            "tipo_display",
            "assunto",
            "conteudo",
            "conteudo_gabarito",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = [
            "uuid",
            "tipo",
            "tipo_display",
            "criado_em",
            "atualizado_em",
        ]
        extra_kwargs = DESCRICOES_CONTEUDO


class EnvioEmailConteudoUpdateSerializer(serializers.ModelSerializer):
    """Campos editáveis de um conteúdo de e-mail."""

    conteudo = ConteudoHtmlField(help_text=AJUDA_CONTEUDO)
    conteudo_gabarito = ConteudoHtmlField(help_text=AJUDA_GABARITO)

    class Meta:
        model = EnvioEmailConteudo
        fields = ["assunto", "conteudo", "conteudo_gabarito"]
        extra_kwargs = DESCRICOES_CONTEUDO


class EnvioEmailIniciadoSerializer(serializers.Serializer):
    """Confirmação de que o envio foi criado e os e-mails enfileirados."""

    detail = serializers.CharField(help_text="Mensagem de confirmação.")
    envio_email_uuid = serializers.UUIDField(
        help_text="UUID do envio criado, usado para consultar o andamento."
    )
    processo_uuid = serializers.UUIDField(
        help_text="UUID do processo de convocação."
    )
    processo_nome = serializers.CharField(
        help_text="Nome do processo informado na requisição."
    )
    tipo = serializers.ChoiceField(
        choices=ENVIO_EMAIL_TIPO_CHOICES, help_text="Tipo de envio."
    )
    quantidade_candidatos = serializers.IntegerField(
        help_text=(
            "Quantidade de habilitados convocados do processo, incluindo "
            "os que não têm e-mail cadastrado."
        )
    )
