from rest_framework import serializers
from .models import ProcessoConvocacao, CargoProcesso, CartaConvocacaoHistorico, CartaConvocacaoCandidato


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
            'data_corte_vagas','passo', 'cargos_processo', 'criado_em', 'atualizado_em'
        ]
        read_only_fields = ['uuid', 'criado_em', 'atualizado_em']


class ProcessoConvocacaoCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de processo de convocação com cargos."""

    class Meta:
        model = ProcessoConvocacao
        fields = [
            'uuid', 'concurso_uuid', 'concurso_nome', 'descricao', 'tipo_escolha',
            'status', 'data_convocacao', 'data_corte_vagas', 'passo'
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
            'status', 'passo', 'data_convocacao', 'data_corte_vagas',
            'quantidade_cargos', 'criado_em'
        ]

    def get_quantidade_cargos(self, obj):
        return obj.cargos_processo.count()


class ProcessoConvocacaoUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de processo de convocação."""

    class Meta:
        model = ProcessoConvocacao
        fields = [
            'concurso_nome', 'concurso_uuid', 'descricao', 'tipo_escolha', 'status', 'passo',
            'data_convocacao', 'data_corte_vagas'
        ]

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError('Informe "status" ou "passo".')

        provided_fields = set(attrs.keys())
        if provided_fields not in ({'status'}, {'passo'}):
            raise serializers.ValidationError(
                'Envie apenas um campo por vez: "status" ou "passo".'
            )

        return attrs


class ProcessoConvocacaoPassoSerializer(serializers.ModelSerializer):
    """Serializer para atualização de passo do processo de convocação."""
    class Meta:
        model = ProcessoConvocacao
        fields = ['passo']

class ProcessoConvocacaoSelectSerializer(serializers.ModelSerializer):
    """
    Serializer para selects/dropdowns no frontend.
    Inclui status para que o front possa filtrar (ex.: não exibir finalizados na Escolha de Candidato).
    """
    value = serializers.UUIDField(source='uuid')
    label = serializers.CharField(source='descricao')

    class Meta:
        model = ProcessoConvocacao
        fields = ['value', 'label', 'concurso_uuid', 'status']


class CartaConvocacaoEnvioSerializer(serializers.Serializer):
    """Serializer para validar o payload do endpoint de carta de convocação."""

    processo_uuid = serializers.UUIDField(help_text='UUID do processo de convocação')
    processo_nome = serializers.CharField(help_text='Nome do processo')
    data = serializers.DateField(
        format='%d-%m-%Y',
        input_formats=['%d-%m-%Y'],
        help_text='Data no formato dd-mm-yyyy',
    )

    def validate_processo_uuid(self, value):
        """Garante que o processo existe."""
        if not ProcessoConvocacao.objects.filter(uuid=value).exists():
            raise serializers.ValidationError('Processo de convocação não encontrado.')
        return value


class CartaConvocacaoHistoricoSerializer(serializers.ModelSerializer):
    """Serializer para GET /api/v1/carta-convocacao/ (listagem do histórico)."""
    quantidade_convocados = serializers.IntegerField(source='quantidade_candidatos', read_only=True)

    class Meta:
        model = CartaConvocacaoHistorico
        fields = ['uuid', 'processo_nome', 'processo_uuid', 'data', 'criado_em', 'quantidade_convocados']


class CartaConvocacaoCandidatoSerializer(serializers.ModelSerializer):
    """Serializer para candidatos no GET /api/v1/carta-convocacao/<uuid>/ (detalhe do histórico)."""

    class Meta:
        model = CartaConvocacaoCandidato
        fields = ['nome', 'rf', 'email', 'status', 'status_detalhe', 'conteudo']


class CartaConvocacaoHistoricoDetalheSerializer(serializers.ModelSerializer):
    """Serializer para GET /api/v1/carta-convocacao/<uuid>/ (detalhe do histórico com candidatos)."""
    quantidade_convocados = serializers.IntegerField(source='quantidade_candidatos', read_only=True)
    candidatos = CartaConvocacaoCandidatoSerializer(many=True, read_only=True)

    class Meta:
        model = CartaConvocacaoHistorico
        fields = ['uuid', 'processo_nome', 'processo_uuid', 'data', 'criado_em', 'quantidade_convocados', 'candidatos']
