from rest_framework import serializers

from processos.utils.conteudo_html import normalizar_conteudo_html
from .models import (
    ProcessoConvocacao,
    CargoProcesso,
    EnvioEmail,
    EnvioEmailCandidato,
    EnvioEmailConteudo,
)
from .models.envio_email import ENVIO_EMAIL_TIPO_CHOICES, TIPO_CONVOCACAO


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


class CargoProcessoUpsertSerializer(CargoProcessoCreateSerializer):
    """
    Serializer de entrada para criar/atualizar CargoProcesso.

    - Se vier `uuid`, a view tenta atualizar o registro existente do processo.
    - Se não vier `uuid`, cria um novo registro.
    """

    uuid = serializers.UUIDField(required=False, allow_null=True)

    class Meta(CargoProcessoCreateSerializer.Meta):
        fields = ['uuid'] + list(CargoProcessoCreateSerializer.Meta.fields)


class ProcessoCargosPayloadSerializer(serializers.Serializer):
    """
    Valida o payload do endpoint de substituição de cargos de um processo.

    Exemplo:
    {
      "porcentagem_nna": 0.2,
      "porcentagem_pcd": 0.05,
      "cargos": [ ... ]
    }
    """

    porcentagem_nna = serializers.FloatField(min_value=0.0, max_value=1.0, required=False)
    porcentagem_pcd = serializers.FloatField(min_value=0.0, max_value=1.0, required=False)
    cargos = CargoProcessoUpsertSerializer(many=True)


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
    pode_deletar = serializers.SerializerMethodField()

    class Meta:
        model = ProcessoConvocacao
        fields = [
            'uuid', 'concurso_nome', 'concurso_uuid', 'descricao', 'tipo_escolha',
            'status', 'passo', 'data_convocacao', 'data_corte_vagas',
            'quantidade_cargos', 'pode_deletar', 'criado_em'
        ]

    def get_quantidade_cargos(self, obj):
        return obj.cargos_processo.count()

    def get_pode_deletar(self, obj):
        return bool(obj.pode_deletar())


class ProcessoConvocacaoUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de processo de convocação."""

    class Meta:
        model = ProcessoConvocacao
        fields = [
            'concurso_nome', 'concurso_uuid', 'descricao', 'tipo_escolha', 'status',
            'data_convocacao', 'data_corte_vagas'
        ]


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


class EnvioEmailEnvioSerializer(serializers.Serializer):
    """Serializer para validar o payload do endpoint de envio de e-mail."""

    processo_uuid = serializers.UUIDField(help_text='UUID do processo de convocação')
    processo_nome = serializers.CharField(help_text='Nome do processo')
    tipo = serializers.ChoiceField(choices=ENVIO_EMAIL_TIPO_CHOICES, help_text='Tipo de envio')
    data_publicacao = serializers.DateField(
        required=False,
        input_formats=['%d-%m-%Y'],
        help_text='Data de publicação no formato dd-mm-YYYY',
    )

    def validate_processo_uuid(self, value):
        """Garante que o processo existe."""
        if not ProcessoConvocacao.objects.filter(uuid=value).exists():
            raise serializers.ValidationError('Processo de convocação não encontrado.')
        return value

    def validate(self, attrs):
        tipo = attrs.get('tipo')
        data_publicacao = attrs.get('data_publicacao')

        if tipo == TIPO_CONVOCACAO and not data_publicacao:
            raise serializers.ValidationError({'data_publicacao': 'Este campo é obrigatório.'})

        return attrs


class EnvioEmailSerializer(serializers.ModelSerializer):
    """Serializer para GET /api/v1/envio-email/ (listagem do histórico)."""

    class Meta:
        model = EnvioEmail
        fields = [
            'uuid', 'processo_nome', 'processo_uuid', 'tipo',
            'criado_em', 'quantidade_candidatos',
        ]


class EnvioEmailCandidatoSerializer(serializers.ModelSerializer):
    """Serializer para candidatos no detalhe do envio."""

    class Meta:
        model = EnvioEmailCandidato
        fields = ['nome', 'rf', 'email', 'status', 'status_detalhe', 'conteudo']


class EnvioEmailDetalheSerializer(serializers.ModelSerializer):
    """Serializer para GET /api/v1/envio-email/<uuid>/ (detalhe com candidatos)."""

    candidatos = EnvioEmailCandidatoSerializer(many=True, read_only=True)

    class Meta:
        model = EnvioEmail
        fields = [
            'uuid', 'processo_nome', 'processo_uuid', 'tipo',
            'criado_em', 'quantidade_candidatos', 'candidatos',
        ]


class ConteudoHtmlField(serializers.CharField):
    """Retorna e persiste HTML sem escape JSON duplicado (ex.: \\\"ql-align-center\\\")."""

    def to_representation(self, value):
        if value is None:
            return value
        return normalizar_conteudo_html(value)

    def to_internal_value(self, data):
        return normalizar_conteudo_html(super().to_internal_value(data))


class EnvioEmailConteudoSerializer(serializers.ModelSerializer):
    """Serializer para GET dos templates de e-mail por tipo."""

    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    conteudo = ConteudoHtmlField()

    class Meta:
        model = EnvioEmailConteudo
        fields = ['uuid', 'tipo', 'tipo_display', 'conteudo', 'criado_em', 'atualizado_em']
        read_only_fields = [
            'uuid', 'tipo', 'tipo_display', 'criado_em', 'atualizado_em',
        ]


class EnvioEmailConteudoUpdateSerializer(serializers.ModelSerializer):
    """Serializer para PATCH — apenas o HTML do template."""

    conteudo = ConteudoHtmlField()

    class Meta:
        model = EnvioEmailConteudo
        fields = ['conteudo']
