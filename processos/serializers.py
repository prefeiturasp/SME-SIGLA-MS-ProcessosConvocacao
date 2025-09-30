from rest_framework import serializers
from .models import ProcessoConvocacao, CargoProcesso


class CargoProcessoSerializer(serializers.ModelSerializer):
    """Serializer para o modelo CargoProcesso."""
    
    class Meta:
        model = CargoProcesso
        fields = [
            'uuid', 'nome', 'processo', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['uuid', 'criado_em', 'atualizado_em']


class CargoProcessoCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de CargoProcesso."""
    
    class Meta:
        model = CargoProcesso
        fields = [
            'nome'
        ]


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
    # cargos = serializers.ListField(
    #     child=serializers.DictField(),
    #     write_only=True,
    #     required=False
    # )
    
    class Meta:
        model = ProcessoConvocacao
        fields = [
            'concurso_uuid', 'concurso_nome', 'descricao', 'tipo_escolha',
            'status', 'data_convocacao', 'data_corte_vagas'
        ]
    
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
