"""
DRF views for the processes module.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from datetime import datetime
import uuid
import logging

from processos.models import ProcessoConvocacao, CargoProcesso
from processos.serializers import (
    ProcessoConvocacaoSerializer, ProcessoConvocacaoCreateSerializer, ProcessoConvocacaoListSerializer,
    ProcessoConvocacaoUpdateSerializer, CargoProcessoSerializer, CargoProcessoCreateSerializer,
    ProcessoConvocacaoSelectSerializer, ProcessoConvocacaoPassoSerializer
)
from processos.utils import CustomPagination
from processos.models.constants import (
    TIPO_ESCOLHA_CHOICES,
    ERROR_PROCESSO_JA_FINALIZADO,
    ERROR_PROCESSO_JA_CANCELADO,
    ERROR_CANDIDATOS_PENDENTES_ESCOLHA,
    ERROR_PROCESSO_NAO_PODE_EDITAR,
)
from processos.services import EscolhasApiService
from processos.services.processo_service import (
    ProcessoConvocacaoService,
    ProcessoServiceError,
)
from sigla_sdk.context import get_correlation_id


logger = logging.getLogger(__name__)

STATUS_EM_ANDAMENTO = 'EM_ANDAMENTO'
STATUS_FINALIZADO = 'FINALIZADO'
STATUS_CANCELADO = 'CANCELADO'

class ProcessoConvocacaoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar processos de convocação.
    """
    queryset = ProcessoConvocacao.objects.filter(esta_ativo=True).prefetch_related('cargos_processo')
    serializer_class = ProcessoConvocacaoSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['concurso_uuid', 'status']
    search_fields = ['concurso_nome', 'descricao']
    ordering_fields = ['data_convocacao', 'data_corte_vagas', 'criado_em']
    ordering = ['-criado_em']
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
            if self.request.query_params.get('formato') == 'select':
                return ProcessoConvocacaoSelectSerializer
            return ProcessoConvocacaoListSerializer
        elif self.action in ['update', 'partial_update']:
            return ProcessoConvocacaoUpdateSerializer
        return ProcessoConvocacaoSerializer

    def list(self, request, *args, **kwargs):
        """
        Lista todos os processos de convocação.
        Se formato=select, retorna sem paginação.
        """
        logger.info(
            'Iniciando lista de processos de convocação',
            extra={
                "params": request.query_params,
                "correlation_id": get_correlation_id(),
                "user": request.user,
                "path": request.path,
                "method": request.method,
            }
        )
        queryset = self.filter_queryset(self.get_queryset())
        if request.query_params.get('formato') == 'select':
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='filtros')
    def filtros(self, request):
        """
        Retorna concursos únicos, cargos únicos e tipos de processo em chaves separadas.
        """
        todos_processos = ProcessoConvocacao.objects.values('concurso_uuid', 'concurso_nome')
        concursos_unicos = {}
        for processo in todos_processos:
            concurso_uuid = processo['concurso_uuid']
            if concurso_uuid not in concursos_unicos:
                concursos_unicos[concurso_uuid] = {
                    'value': concurso_uuid,
                    'label': processo['concurso_nome']
                }

        todos_cargos = CargoProcesso.objects.values('cargo_uuid', 'cargo_nome').order_by('cargo_nome', 'cargo_uuid')
        cargos_unicos = {}
        for cargo in todos_cargos:
            if cargo['cargo_nome'] not in cargos_unicos:
                cargos_unicos[cargo['cargo_nome']] = cargo

        tipos_escolha = [
            {
                'value': choice[0],
                'label': choice[1]
            }
            for choice in TIPO_ESCOLHA_CHOICES
        ]

        resultado = {
            'concursos': list(concursos_unicos.values()),
            'cargos': [
                {
                    'value': cargo['cargo_uuid'],
                    'label': cargo['cargo_nome']
                }
                for cargo in cargos_unicos.values()
            ],
            'tipos_escolha': tipos_escolha
        }

        return Response(resultado)

    @action(detail=True, methods=['post'], url_path='finalizar')
    def finalizar(self, request, pk=None):
        """
        Finaliza o processo de convocação.
        - Só permite se status for EM_ANDAMENTO.
        - Valida se todos os candidatos do processo (candidatos_uuids dos cargos) fizeram
          escolha, reconvocação ou não escolha (via MS-Escolha).
        - Atualiza status para FINALIZADO.
        """
        processo = self.get_object()
        logger.info(
            'Iniciando finalização de processo de convocação',
            extra={
                "processo_uuid": processo.uuid,
                "processo_status": processo.status,
                "correlation_id": get_correlation_id(),
                "user": request.user,
                "path": request.path,
                "method": request.method,
            }
        )

        if processo.status == STATUS_FINALIZADO:
            return Response(
                {'detail': ERROR_PROCESSO_JA_FINALIZADO},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if processo.status == STATUS_CANCELADO:
            return Response(
                {'detail': ERROR_PROCESSO_JA_CANCELADO},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if processo.status != STATUS_EM_ANDAMENTO:
            return Response(
                {'detail': 'Apenas processos em andamento podem ser finalizados.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Candidatos do processo = união dos candidatos_uuids de todos os cargos (mesma lista da tela e do banco)
        habilitados_uuids = {
            str(uuid)
            for cargo in processo.cargos_processo.all()
            for uuid in (cargo.candidatos_uuids or [])
        }

        # Quem fez escolha no concurso (MS-Escolha: escolha, reconvocação ou não escolha)
        try:
            com_escolha = set(EscolhasApiService().buscar_candidatos_com_escolha(str(processo.concurso_uuid)))
        except Exception as exc:
            logger.exception('Erro ao buscar escolhas para finalização: %s', exc)
            return Response(
                {'detail': 'Erro ao consultar escolhas dos candidatos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pendentes = habilitados_uuids - com_escolha
        if pendentes:
            logger.info(
                'Candidatos pendentes de escolha',
                extra={
                    "processo_uuid": processo.uuid,
                    "correlation_id": get_correlation_id(),
                    "pendentes": len(pendentes),
                    "habilitados_uuids": len(habilitados_uuids),
                    "com_escolha": len(com_escolha),
                }
            )
            return Response(
                {'detail': ERROR_CANDIDATOS_PENDENTES_ESCOLHA},
                status=status.HTTP_400_BAD_REQUEST,
            )

        processo.status = STATUS_FINALIZADO
        processo.save()
        serializer = ProcessoConvocacaoSerializer(processo)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        """Bloqueia alteração quando processo está finalizado."""
        instance = self.get_object()
        if instance.status == STATUS_FINALIZADO:
            return Response(
                {'detail': ERROR_PROCESSO_NAO_PODE_EDITAR},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Bloqueia alteração quando processo está finalizado."""
        instance = self.get_object()
        if instance.status == STATUS_FINALIZADO:
            return Response(
                {'detail': ERROR_PROCESSO_NAO_PODE_EDITAR},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=['patch'], url_path='passo')
    def atualizar_passo(self, request, pk=None):
        processo = self.get_object()
        serializer = ProcessoConvocacaoPassoSerializer(
            processo,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ProcessoConvocacaoSerializer(processo).data, status=status.HTTP_200_OK)
    def destroy(self, request, *args, **kwargs):
        """
        Exclui o processo e executa limpeza nos MS dependentes:
        - MS-Agenda: excluir agendas do processo
        - MS-Candidatos: desconvocar candidatos por cargo do processo
        - MS-Escolha: excluir lotes de vagas-escolas do processo
        """
        processo = self.get_object()
        processo_uuid = str(processo.uuid)

        if not processo.pode_deletar():
            return Response(
                {'detail': 'Processo não pode ser deletado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            ProcessoConvocacaoService().excluir_processo_e_dependencias(
                processo=processo,
            )
        except ProcessoServiceError as exc:
            return Response(
                {'detail': str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
