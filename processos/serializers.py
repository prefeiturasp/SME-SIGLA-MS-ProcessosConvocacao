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
            'tipo_processo', 'status', 'data_publicacao', 'data_convocacao',
            'numero_convocados', 'cargos_processo', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['uuid', 'criado_em', 'atualizado_em']


class ProcessoConvocacaoCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de processo de convocação com cargos."""
    cargos = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = ProcessoConvocacao
        fields = [
            'concurso_uuid', 'concurso_nome', 'descricao', 'tipo_processo',
            'status', 'data_convocacao', 'numero_convocados', 'cargos'
        ]
    
    def validate_concurso_uuid(self, value):
        """Valida se o concurso_uuid é um UUID válido."""
        import uuid
        try:
            uuid.UUID(str(value))
            return value
        except ValueError:
            raise serializers.ValidationError("UUID do concurso inválido.")
    
    def create(self, validated_data):
        cargos_data = validated_data.pop('cargos', [])
        processo = super().create(validated_data)
        
        for cargo_data in cargos_data:
            cargo_nome = cargo_data.get('nome', '')
            
            CargoProcesso.objects.create(
                processo=processo,
                nome=cargo_nome,
                cargo_uuid=cargo_data.get('cargo_uuid', '')
            )
        
        return processo


class ProcessoConvocacaoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de processos de convocação."""
    quantidade_cargos = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcessoConvocacao
        fields = [
            'uuid', 'concurso_nome', 'concurso_uuid', 'descricao', 'tipo_processo', 
            'status', 'data_convocacao', 'numero_convocados',
            'quantidade_cargos', 'criado_em'
        ]
    
    def get_quantidade_cargos(self, obj):
        return obj.cargos_processo.count()


class ProcessoConvocacaoUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de processo de convocação."""
    
    class Meta:
        model = ProcessoConvocacao
        fields = [
            'concurso_nome', 'descricao', 'tipo_processo', 'status', 'data_convocacao',
            'numero_convocados'
        ]
