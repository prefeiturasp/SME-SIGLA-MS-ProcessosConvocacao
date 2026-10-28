"""Serializers do app cargos."""

from cargos.models import CargoProcesso
from processos.models import ProcessoConvocacao
from rest_framework import serializers

DESCRICOES_CAMPOS = {
    "uuid": {
        "help_text": (
            "Identificador único do vínculo entre o cargo e o processo."
        )
    },
    "cargo_nome": {"help_text": "Nome do cargo."},
    "cargo_uuid": {"help_text": "UUID do cargo no cadastro de cargos."},
    "cargo_codigo": {"help_text": "Código do cargo."},
    "processo": {
        "help_text": (
            "UUID do processo de convocação ao qual o cargo está vinculado."
        )
    },
    "vagas": {
        "help_text": "Total de vagas disponíveis para o cargo no processo."
    },
    "candidatos_geral": {
        "help_text": "Quantidade de candidatos habilitados na lista geral."
    },
    "candidatos_pcd": {
        "help_text": (
            "Quantidade de candidatos habilitados na lista de pessoas com "
            "deficiência (PCD)."
        )
    },
    "candidatos_nna": {
        "help_text": (
            "Quantidade de candidatos habilitados na lista de negros, "
            "negras ou afrodescendentes (NNA)."
        )
    },
    "total_candidatos": {
        "help_text": "Total de candidatos classificados para o cargo."
    },
    "candidatos_uuids": {
        "help_text": (
            "UUIDs dos candidatos convocados para o cargo neste processo."
        )
    },
    "criado_em": {"help_text": "Data e hora de criação do registro."},
    "atualizado_em": {
        "help_text": "Data e hora da última atualização do registro."
    },
}


class CargoProcessoSerializer(serializers.ModelSerializer):
    """Cargo vinculado a um processo de convocação."""

    processo = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=ProcessoConvocacao.objects.all(),
        label="Processo de Convocação",
        help_text=DESCRICOES_CAMPOS["processo"]["help_text"],
    )

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
        extra_kwargs = DESCRICOES_CAMPOS


class CargoProcessoCreateSerializer(serializers.ModelSerializer):
    """Dados de um cargo a vincular ao processo."""

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
        extra_kwargs = DESCRICOES_CAMPOS


class CargoProcessoUpsertSerializer(CargoProcessoCreateSerializer):
    """Cargo a criar ou a atualizar no processo."""

    uuid = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text=(
            "UUID do vínculo cargo–processo já existente. Informe para "
            "atualizar o cargo; omita para criar um novo."
        ),
    )

    class Meta(CargoProcessoCreateSerializer.Meta):
        fields = ["uuid"] + list(CargoProcessoCreateSerializer.Meta.fields)


class ProcessoCargosDadosSerializer(serializers.Serializer):
    """Lista completa de cargos do processo e percentuais de reserva."""

    porcentagem_nna = serializers.FloatField(
        min_value=0.0,
        max_value=1.0,
        required=False,
        help_text=(
            "Fração das vagas reservada a candidatos NNA, de 0 a 1 "
            "(0.2 = 20%). Quando enviada, atualiza o processo."
        ),
    )
    porcentagem_pcd = serializers.FloatField(
        min_value=0.0,
        max_value=1.0,
        required=False,
        help_text=(
            "Fração das vagas reservada a candidatos PCD, de 0 a 1 "
            "(0.05 = 5%). Quando enviada, atualiza o processo."
        ),
    )
    cargos = CargoProcessoUpsertSerializer(
        many=True,
        help_text=(
            "Lista completa de cargos do processo. Cargos já vinculados "
            "que não constarem na lista são removidos."
        ),
    )


class ErroMensagemSerializer(serializers.Serializer):
    """Erro das rotas de cargos quando o processo ou o cargo não existe."""

    error = serializers.CharField(help_text="Mensagem que descreve o erro.")


class ErroItemCargoSerializer(serializers.Serializer):
    """Cargo enviado que não pôde ser processado."""

    uuid = serializers.UUIDField(
        required=False,
        help_text=(
            "UUID do vínculo cargo–processo informado no item. Presente "
            "quando o item trazia `uuid`."
        ),
    )
    cargo = serializers.CharField(
        required=False,
        help_text=(
            "Nome do cargo informado no item. Presente quando o item não "
            "trazia `uuid`."
        ),
    )
    erros = serializers.JSONField(
        help_text=("Mensagem de erro ou mapa de erros de validação do item."),
    )


class SubstituicaoCargosRespostaSerializer(serializers.Serializer):
    """Resultado da substituição dos cargos de um processo."""

    success = serializers.BooleanField(
        help_text="Verdadeiro sempre que a requisição é processada."
    )
    cargos_criados = serializers.IntegerField(
        help_text="Quantidade de cargos criados."
    )
    cargos_atualizados = serializers.IntegerField(
        help_text="Quantidade de cargos atualizados."
    )
    cargos_removidos = serializers.IntegerField(
        help_text=(
            "Quantidade de cargos removidos por não constarem na lista "
            "enviada."
        )
    )
    cargos = CargoProcessoSerializer(
        many=True, help_text="Cargos do processo após a operação."
    )
    erros = ErroItemCargoSerializer(
        many=True,
        required=False,
        help_text=(
            "Itens que não puderam ser processados. Presente apenas na "
            "resposta 207."
        ),
    )
