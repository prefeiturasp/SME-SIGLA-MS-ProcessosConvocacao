"""
DRF views for the processes module.
"""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import ProcessoConvocacao
from .serializers import (
    ProcessoConvocacaoSerializer,
)
from .services import ExternalServices


class ProcessoConvocacaoViewSet(viewsets.ModelViewSet):
    
    queryset = ProcessoConvocacao.objects.all()
    # permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'tipo_processo']
    search_fields = ['concurso_nome', 'descricao']
    ordering_fields = ['concurso_nome', 'data_publicacao', 'criado_em']
    ordering = ['-criado_em']
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'list':
            return ProcessoConvocacaoSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProcessoConvocacaoSerializer
        return ProcessoConvocacaoSerializer
    
    def perform_create(self, serializer):
        """Override to add custom logic on create."""
        processo = serializer.save()
        print(processo)
        ###
    
    def perform_update(self, serializer):
        """Override to add custom logic on update."""
        processo = serializer.save()
        print(processo)
        ###
        
    
    def perform_destroy(self, instance):
        """Override to add custom logic on delete."""
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        """Finalizar um processo."""
        processo = self.get_object()
        
        if not processo.status == 'EM_ANDAMENTO':
            return Response(
                {'error': 'Processo não pode ser finalizado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        processo.status = 'FINALIZADO'
        processo.save()
        
        serializer = self.get_serializer(processo)
        return Response(serializer.data)

