"""Serializers do app cargos."""

from cargos.models import CargoProcesso
from rest_framework import serializers


class CargoProcessoSerializer(serializers.ModelSerializer):
    """Serializer para o modelo CargoProcesso."""

    class Meta:
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
        fields = ["uuid"] + list(CargoProcessoCreateSerializer.Meta.fields)


class ProcessoCargosDadosSerializer(serializers.Serializer):
    """Valida o corpo de substituição de cargos do processo."""

    porcentagem_nna = serializers.FloatField(
        min_value=0.0, max_value=1.0, required=False
    )
    porcentagem_pcd = serializers.FloatField(
        min_value=0.0, max_value=1.0, required=False
    )
    cargos = CargoProcessoUpsertSerializer(many=True)
