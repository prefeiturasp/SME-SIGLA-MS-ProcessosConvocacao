"""
DRF views for the processes module.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from datetime import datetime
import uuid

from processos.models import ProcessoConvocacao, CargoProcesso
from processos.serializers import (
    ProcessoConvocacaoSerializer, ProcessoConvocacaoCreateSerializer, ProcessoConvocacaoListSerializer,
    ProcessoConvocacaoUpdateSerializer, CargoProcessoSerializer, CargoProcessoCreateSerializer
)
from processos.utils import CustomPagination
from processos.models.constants import PROCESSO_TIPOS_CHOICES


class ProcessoConvocacaoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar processos de convocação.
    """
    queryset = ProcessoConvocacao.objects.prefetch_related('cargos_processo')
    serializer_class = ProcessoConvocacaoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['concurso_uuid']
    search_fields = ['concurso_nome', 'descricao']
    ordering_fields = ['data_convocacao', 'data_publicacao', 'numero_convocados', 'criado_em']
    ordering = ['-data_publicacao']
    pagination_class = CustomPagination
    
    def get_queryset(self):
        """Sobrescreve o queryset para aplicar filtros customizados."""
        queryset = super().get_queryset()

        data_inicio = self.request.query_params.get('data_convocacao_inicio')
        data_fim = self.request.query_params.get('data_convocacao_fim')

        if data_inicio:
            try:
                data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                queryset = queryset.filter(data_convocacao__date__gte=data_inicio)
            except ValueError:
                pass

        if data_fim:
            try:
                data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
                queryset = queryset.filter(data_convocacao__date__lte=data_fim)
            except ValueError:
                pass

        cargo_uuid = self.request.query_params.get('cargo_uuid')
        if cargo_uuid:
            try:
                uuid.UUID(cargo_uuid)
                queryset = queryset.filter(cargos_processo__cargo_uuid=cargo_uuid).distinct()
            except ValueError:
                pass

        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return ProcessoConvocacaoCreateSerializer
        elif self.action == 'list':
            return ProcessoConvocacaoListSerializer
        elif self.action in ['update', 'partial_update']:
            return ProcessoConvocacaoUpdateSerializer
        return ProcessoConvocacaoSerializer
    
    @action(detail=False, methods=['get'], url_path='filtros')
    def filtros(self, request):
        """
        Retorna concursos únicos, cargos únicos e tipos de processo em chaves separadas.
        """
        # Buscar todos os concursos únicos usando set para garantir unicidade
        todos_processos = ProcessoConvocacao.objects.values('concurso_uuid', 'concurso_nome')
        
        # Usar set para garantir concursos únicos
        concursos_unicos = {}
        for processo in todos_processos:
            concurso_uuid = processo['concurso_uuid']
            if concurso_uuid not in concursos_unicos:
                concursos_unicos[concurso_uuid] = {
                    'value': concurso_uuid,
                    'label': processo['concurso_nome']
                }
        
        # Buscar todos os cargos e fazer deduplicação por nome em Python
        todos_cargos = CargoProcesso.objects.values('cargo_uuid', 'nome').order_by('nome', 'cargo_uuid')

        # Deduplicar cargos por nome
        cargos_unicos = {}
        for cargo in todos_cargos:
            if cargo['nome'] not in cargos_unicos:
                cargos_unicos[cargo['nome']] = cargo
        
        # Preparar tipos de processo a partir dos choices
        tipos_processos = [
            {
                'value': choice[0],
                'label': choice[1]
            }
            for choice in PROCESSO_TIPOS_CHOICES
        ]

        # Preparar resposta
        resultado = {
            'concursos': list(concursos_unicos.values()),
            'cargos': [
                {
                    'value': cargo['cargo_uuid'],
                    'label': cargo['nome']
                }
                for cargo in cargos_unicos.values()
            ],
            'tipos_processos': tipos_processos
        }
        
        return Response(resultado)

