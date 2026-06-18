"""Serializers do app processos."""

from __future__ import annotations

from uuid import UUID

from cargos.serializers import CargoProcessoSerializer
from rest_framework import serializers

from processos.models import ProcessoConvocacao


class ProcessoConvocacaoSerializer(serializers.ModelSerializer):
    """Serializer para o modelo ProcessoConvocacao."""

    cargos_processo = CargoProcessoSerializer(many=True, read_only=True)

    class Meta:
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
    """Serializer para criação de processo de convocação."""

    class Meta:
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
        try:
            UUID(str(value))
            return value
        except ValueError:
            raise serializers.ValidationError(
                "UUID do concurso inválido."
            ) from None


class ProcessoConvocacaoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de processos."""

    quantidade_cargos = serializers.SerializerMethodField()
    pode_deletar = serializers.SerializerMethodField()

    class Meta:
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
        return obj.cargos_processo.count()

    def get_pode_deletar(self, obj: ProcessoConvocacao) -> bool:
        return bool(obj.pode_deletar())


class ProcessoConvocacaoUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de processo de convocação."""

    class Meta:
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
    """Serializer para atualização de passo do processo."""

    class Meta:
        model = ProcessoConvocacao
        fields = ["passo"]


class ProcessoConvocacaoSelectSerializer(serializers.ModelSerializer):
    """Serializer para selects/dropdowns no frontend."""

    value = serializers.UUIDField(source="uuid")
    label = serializers.CharField(source="descricao")

    class Meta:
        model = ProcessoConvocacao
        fields = ["value", "label", "concurso_uuid", "status"]
