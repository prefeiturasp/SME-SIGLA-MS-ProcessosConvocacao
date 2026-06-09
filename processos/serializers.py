"""Serializers do app processos."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from rest_framework import serializers

from processos.utils.conteudo_html import normalizar_conteudo_html

from .models import (
    CargoProcesso,
    EnvioEmail,
    EnvioEmailCandidato,
    EnvioEmailConteudo,
    ProcessoConvocacao,
)
from .models.envio_email import ENVIO_EMAIL_TIPO_CHOICES


class CargoProcessoSerializer(serializers.ModelSerializer):
    """Serializer para o modelo CargoProcesso."""

    class Meta:
        """Configuração do serializer."""

        model = CargoProcesso
        fields = [
            "uuid",
            "cargo_nome",
            "cargo_uuid",
            "cargo_codigo",
            "processo",
            "vagas",
            "candidatos_geral",
            "candidatos_pcd",
            "candidatos_nna",
            "total_candidatos",
            "candidatos_uuids",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["uuid", "criado_em", "atualizado_em"]


class CargoProcessoCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de CargoProcesso."""

    class Meta:
        """Configuração do serializer."""

        model = CargoProcesso
        fields = [
            "cargo_nome",
            "cargo_uuid",
            "cargo_codigo",
            "candidatos_geral",
            "candidatos_pcd",
            "candidatos_nna",
            "total_candidatos",
            "vagas",
            "candidatos_uuids",
        ]
        read_only_fields = ["uuid", "criado_em", "atualizado_em"]


class CargoProcessoUpsertSerializer(CargoProcessoCreateSerializer):
    """Serializer de entrada para criar/atualizar CargoProcesso."""

    uuid = serializers.UUIDField(required=False, allow_null=True)

    class Meta(CargoProcessoCreateSerializer.Meta):
        """Estende a configuração de criação com campo uuid opcional."""

        fields = ["uuid"] + list(CargoProcessoCreateSerializer.Meta.fields)


class ProcessoCargosPayloadSerializer(serializers.Serializer):
    """Valida payload de substituição de cargos do processo."""

    porcentagem_nna = serializers.FloatField(
        min_value=0.0, max_value=1.0, required=False
    )
    porcentagem_pcd = serializers.FloatField(
        min_value=0.0, max_value=1.0, required=False
    )
    cargos = CargoProcessoUpsertSerializer(many=True)


class ProcessoConvocacaoSerializer(serializers.ModelSerializer):
    """Serializer para o modelo ProcessoConvocacao."""

    cargos_processo = CargoProcessoSerializer(many=True, read_only=True)

    class Meta:
        """Configuração do serializer."""

        model = ProcessoConvocacao
        fields = [
            "uuid",
            "concurso_uuid",
            "concurso_nome",
            "descricao",
            "tipo_escolha",
            "status",
            "data_convocacao",
            "data_corte_vagas",
            "passo",
            "cargos_processo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["uuid", "criado_em", "atualizado_em"]


class ProcessoConvocacaoCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de processo de convocação com cargos."""

    class Meta:
        """Configuração do serializer."""

        model = ProcessoConvocacao
        fields = [
            "uuid",
            "concurso_uuid",
            "concurso_nome",
            "descricao",
            "tipo_escolha",
            "status",
            "data_convocacao",
            "data_corte_vagas",
            "passo",
        ]
        read_only_fields = ["uuid"]

    def validate_concurso_uuid(self, value: UUID | str) -> UUID | str:
        """Valida se o concurso_uuid é um UUID válido.

        Args:
            self: Instância do objeto.
            value: Valor recebido para validação.

        Returns:
            Valor validado do campo concurso uuid.

        Raises:
            ValidationError: Se os dados informados forem inválidos.
        """
        try:
            UUID(str(value))
            return value
        except ValueError:
            raise serializers.ValidationError(
                "UUID do concurso inválido."
            ) from None


class ProcessoConvocacaoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de processos de convocação."""

    quantidade_cargos = serializers.SerializerMethodField()
    pode_deletar = serializers.SerializerMethodField()

    class Meta:
        """Configuração do serializer."""

        model = ProcessoConvocacao
        fields = [
            "uuid",
            "concurso_nome",
            "concurso_uuid",
            "descricao",
            "tipo_escolha",
            "status",
            "passo",
            "data_convocacao",
            "data_corte_vagas",
            "quantidade_cargos",
            "pode_deletar",
            "criado_em",
        ]

    def get_quantidade_cargos(self, obj: ProcessoConvocacao) -> int:
        """Retorna a quantidade de cargos vinculados ao processo.

        Args:
            self: Instância do objeto.
            obj: Instância do objeto processado.

        Returns:
            Valor inteiro calculado.

        Raises:
            Nenhuma exceção específica documentada.
        """
        return obj.cargos_processo.count()

    def get_pode_deletar(self, obj: ProcessoConvocacao) -> bool:
        """Indica se o processo pode ser excluído.

        Args:
            self: Instância do objeto.
            obj: Instância do objeto processado.

        Returns:
            Verdadeiro se a condição for satisfeita.

        Raises:
            Nenhuma exceção específica documentada.
        """
        return bool(obj.pode_deletar())


class ProcessoConvocacaoUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de processo de convocação."""

    class Meta:
        """Configuração do serializer."""

        model = ProcessoConvocacao
        fields = [
            "concurso_nome",
            "concurso_uuid",
            "descricao",
            "tipo_escolha",
            "status",
            "data_convocacao",
            "data_corte_vagas",
        ]


class ProcessoConvocacaoPassoSerializer(serializers.ModelSerializer):
    """Serializer para atualização de passo do processo de convocação."""

    class Meta:
        """Configuração do serializer."""

        model = ProcessoConvocacao
        fields = ["passo"]


class ProcessoConvocacaoSelectSerializer(serializers.ModelSerializer):
    """Serializer para selects/dropdowns no frontend."""

    value = serializers.UUIDField(source="uuid")
    label = serializers.CharField(source="descricao")

    class Meta:
        """Configuração do serializer."""

        model = ProcessoConvocacao
        fields = ["value", "label", "concurso_uuid", "status"]


class EnvioEmailEnvioSerializer(serializers.Serializer):
    """Serializer para validar o payload do endpoint de envio de e-mail."""

    processo_uuid = serializers.UUIDField(
        help_text="UUID do processo de convocação"
    )
    processo_nome = serializers.CharField(help_text="Nome do processo")
    tipo = serializers.ChoiceField(
        choices=ENVIO_EMAIL_TIPO_CHOICES, help_text="Tipo de envio"
    )
    conteudo = serializers.CharField(help_text="Conteúdo do e-mail (HTML)")

    def validate_processo_uuid(self, value: UUID) -> UUID:
        """Garante que o processo existe.

        Args:
            self: Instância do objeto.
            value: Valor recebido para validação.

        Returns:
            Valor validado do campo processo uuid.

        Raises:
            ValidationError: Se os dados informados forem inválidos.
        """
        if not ProcessoConvocacao.objects.filter(uuid=value).exists():
            raise serializers.ValidationError(
                "Processo de convocação não encontrado."
            )
        return value


class EnvioEmailSerializer(serializers.ModelSerializer):
    """Serializer para GET /api/v1/envio-email/ (listagem do histórico)."""

    class Meta:
        """Configuração do serializer."""

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
        """Configuração do serializer."""

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
        """Configuração do serializer."""

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
    """Retorna e persiste HTML sem escape JSON duplicado (ex.:."""

    def to_representation(self, value: str | None) -> str | None:
        """Normaliza HTML na serialização.

        Args:
            self: Instância do objeto.
            value: Valor recebido para validação.

        Returns:
            Texto resultante da operação.

        Raises:
            Nenhuma exceção específica documentada.
        """
        if value is None:
            return value
        return normalizar_conteudo_html(value)

    def to_internal_value(self, data: Any) -> str:
        """Normaliza HTML na desserialização.

        Args:
            self: Instância do objeto.
            data: Dados de entrada.

        Returns:
            Texto resultante da operação.

        Raises:
            Nenhuma exceção específica documentada.
        """
        return normalizar_conteudo_html(super().to_internal_value(data))


class EnvioEmailConteudoSerializer(serializers.ModelSerializer):
    """Serializer para GET dos templates de e-mail por tipo."""

    tipo_display = serializers.CharField(
        source="get_tipo_display", read_only=True
    )
    conteudo = ConteudoHtmlField()

    class Meta:
        """Configuração do serializer."""

        model = EnvioEmailConteudo
        fields = [
            "uuid",
            "tipo",
            "tipo_display",
            "conteudo",
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

    class Meta:
        """Configuração do serializer."""

        model = EnvioEmailConteudo
        fields = ["conteudo"]
