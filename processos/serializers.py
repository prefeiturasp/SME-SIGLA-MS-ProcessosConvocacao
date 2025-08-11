from rest_framework import serializers
from .models import ProcessoConvocacao


class ProcessoConvocacaoSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProcessoConvocacao
        fields = '__all__'
        read_only_fields = ('criado_em', 'atualizado_em')
