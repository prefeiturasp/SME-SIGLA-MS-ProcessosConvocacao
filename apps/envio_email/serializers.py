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


class EnvioEmailEnvioSerializer(serializers.Serializer):
    """Valida o payload do endpoint de envio de e-mail."""

    processo_uuid = serializers.UUIDField(
        help_text="UUID do processo de convocação"
    )
    processo_nome = serializers.CharField(help_text="Nome do processo")
    tipo = serializers.ChoiceField(
        choices=ENVIO_EMAIL_TIPO_CHOICES, help_text="Tipo de envio"
    )
    conteudo = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Conteúdo do e-mail (HTML); se vazio, usa conteúdo\
             salvo ou gabarito",
    )
    assunto = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Assunto do e-mail; se vazio, usa assunto salvo ou\
             padrão do tipo",
    )

    def validate_processo_uuid(self, value: UUID) -> UUID:
        if not ProcessoConvocacaoRepository.existe_por_uuid(value):
            raise serializers.ValidationError(
                "Processo de convocação não encontrado."
            )
        return value


class EnvioEmailSerializer(serializers.ModelSerializer):
    """Serializer para listagem do histórico de envios."""

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


class EnvioEmailCandidatoSerializer(serializers.ModelSerializer):
    """Serializer para candidatos no detalhe do envio."""

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


class EnvioEmailDetalheSerializer(serializers.ModelSerializer):
    """Serializer de detalhe de envio de e-mail com candidatos."""

    candidatos = EnvioEmailCandidatoSerializer(many=True, read_only=True)

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


class ConteudoHtmlField(serializers.CharField):
    """Retorna e persiste HTML sem escape JSON duplicado."""

    def to_representation(self, value: str | None) -> str | None:
        if value is None:
            return value
        return normalizar_conteudo_html(value)

    def to_internal_value(self, data: Any) -> str:
        return normalizar_conteudo_html(super().to_internal_value(data))


class EnvioEmailConteudoSerializer(serializers.ModelSerializer):
    """Serializer para GET dos templates de e-mail por tipo."""

    tipo_display = serializers.CharField(
        source="get_tipo_display", read_only=True
    )
    conteudo = ConteudoHtmlField()
    conteudo_gabarito = ConteudoHtmlField()

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


class EnvioEmailConteudoUpdateSerializer(serializers.ModelSerializer):
    """Serializer para PATCH — apenas o HTML do template."""

    conteudo = ConteudoHtmlField()
    conteudo_gabarito = ConteudoHtmlField()

    class Meta:
        model = EnvioEmailConteudo
        fields = ["assunto", "conteudo", "conteudo_gabarito"]
