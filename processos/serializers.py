from rest_framework import serializers
from .models import ProcessoConvocacao, CargoProcesso


class CargoProcessoSerializer(serializers.ModelSerializer):
    """Serializer para o modelo CargoProcesso."""

    class Meta:
        model = CargoProcesso
        fields = [
            'uuid', 'cargo_nome', 'cargo_uuid', 'cargo_codigo', 'processo', 
            'vagas', 'candidatos_geral', 'candidatos_pcd', 'candidatos_nna', 'total_candidatos',
            'candidatos_uuids',
            'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['uuid', 'criado_em', 'atualizado_em']


class CargoProcessoCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de CargoProcesso."""

    class Meta:
        model = CargoProcesso
        fields = [
            'cargo_nome', 'cargo_uuid', 'cargo_codigo',
            'candidatos_geral', 'candidatos_pcd', 'candidatos_nna', 'total_candidatos', 'vagas',
            'candidatos_uuids'
        ]
        read_only_fields = ['uuid', 'criado_em', 'atualizado_em']


class ProcessoConvocacaoSerializer(serializers.ModelSerializer):
    """Serializer para o modelo ProcessoConvocacao."""
    cargos_processo = CargoProcessoSerializer(many=True, read_only=True)

    class Meta:
        model = ProcessoConvocacao
        fields = [
            'uuid', 'concurso_uuid', 'concurso_nome', 'descricao', 
            'tipo_escolha', 'status', 'data_convocacao',
            'data_corte_vagas', 'cargos_processo', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['uuid', 'criado_em', 'atualizado_em']


class ProcessoConvocacaoCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de processo de convocação com cargos."""

    class Meta:
        model = ProcessoConvocacao
        fields = [
            'uuid', 'concurso_uuid', 'concurso_nome', 'descricao', 'tipo_escolha',
            'status', 'data_convocacao', 'data_corte_vagas'
        ]
        read_only_fields = ['uuid']

    def validate_concurso_uuid(self, value):
        """Valida se o concurso_uuid é um UUID válido."""
        import uuid
        try:
            uuid.UUID(str(value))
            return value
        except ValueError:
            raise serializers.ValidationError("UUID do concurso inválido.")


class ProcessoConvocacaoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de processos de convocação."""
    quantidade_cargos = serializers.SerializerMethodField()

    class Meta:
        model = ProcessoConvocacao
        fields = [
            'uuid', 'concurso_nome', 'concurso_uuid', 'descricao', 'tipo_escolha',
            'status', 'data_convocacao', 'data_corte_vagas',
            'quantidade_cargos', 'criado_em'
        ]

    def get_quantidade_cargos(self, obj):
        return obj.cargos_processo.count()


class ProcessoConvocacaoUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de processo de convocação."""

    class Meta:
        model = ProcessoConvocacao
        fields = [
            'concurso_nome', 'descricao', 'tipo_escolha', 'status', 'data_convocacao',
            'data_corte_vagas'
        ]


class ProcessoConvocacaoSelectSerializer(serializers.ModelSerializer):
    """
    Serializer para selects/dropdowns no frontend.
    """
    value = serializers.UUIDField(source='uuid')
    label = serializers.CharField(source='descricao')

    class Meta:
        model = ProcessoConvocacao
        fields = ['value', 'label', 'concurso_uuid']
