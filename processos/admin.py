"""
Django admin configuration for the processes module.
"""
from django.contrib import admin
from auditlog.admin import LogEntryAdmin
from auditlog.models import LogEntry
from .models import (
    ProcessoConvocacao,
    CargoProcesso,
    CartaConvocacaoHistorico,
    CartaConvocacaoCandidato,
)


class CargoProcessoInline(admin.TabularInline):
    """Inline para gerenciar cargos do processo."""
    model = CargoProcesso
    extra = 1
    fields = ('cargo_nome',)


@admin.register(ProcessoConvocacao)
class ProcessoConvocacaoAdmin(admin.ModelAdmin):
    """Admin for ProcessoConvocacao model."""
    
    list_display = (
        'concurso_nome', 'descricao', 'tipo_escolha', 'status', 
        'data_convocacao', 'data_corte_vagas', 
    )
    list_filter = ('status', 'tipo_escolha', 'data_convocacao', 'data_corte_vagas')
    search_fields = ('concurso_nome', 'descricao')
    readonly_fields = ('uuid', 'criado_em', 'atualizado_em')
    ordering = ('-criado_em',)
    inlines = (CargoProcessoInline,)
    
    fieldsets = (
        ('Informações do Concurso', {
            'fields': ('concurso_uuid', 'concurso_nome')
        }),
        ('Dados do Processo', {
            'fields': ('descricao', 'tipo_escolha', 'status')
        }),
        ('Datas', {
            'fields': ('data_convocacao', 'data_corte_vagas')
        }),
        ('Metadados', {
            'fields': ('uuid', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with related data."""
        return super().get_queryset(request).prefetch_related('cargos_processo')


@admin.register(CargoProcesso)
class CargoProcessoAdmin(admin.ModelAdmin):
    """Admin for CargoProcesso model."""
    
    list_display = (
        'processo', 'cargo_nome', 'cargo_uuid', 'cargo_codigo', 'criado_em'
    )
    list_filter = ('processo', 'criado_em')
    search_fields = ('processo__concurso_nome', 'cargo_nome')
    ordering = ('processo', 'cargo_nome')
    readonly_fields = ('uuid', 'criado_em', 'atualizado_em')
    
    fieldsets = (
        ('Relacionamento', {
            'fields': ('processo', 'cargo_nome', 'cargo_uuid', 'cargo_codigo')
        }),
        ('Metadados', {
            'fields': ('uuid', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with related data."""
        return super().get_queryset(request).select_related('processo')


class CartaConvocacaoCandidatoInline(admin.TabularInline):
    """Inline para candidatos do histórico de carta de convocação."""
    model = CartaConvocacaoCandidato
    extra = 0
    readonly_fields = ('uuid', 'criado_em', 'atualizado_em')
    fields = ('nome', 'rf', 'email', 'status', 'status_detalhe', 'conteudo')


@admin.register(CartaConvocacaoHistorico)
class CartaConvocacaoHistoricoAdmin(admin.ModelAdmin):
    """Admin para histórico de envio de carta de convocação."""

    list_display = ('processo_nome', 'processo_uuid', 'data', 'quantidade_candidatos', 'criado_em')
    list_filter = ('data', 'criado_em')
    search_fields = ('processo_nome',)
    readonly_fields = ('uuid', 'criado_em', 'atualizado_em')
    ordering = ('-criado_em',)
    inlines = (CartaConvocacaoCandidatoInline,)


@admin.register(CartaConvocacaoCandidato)
class CartaConvocacaoCandidatoAdmin(admin.ModelAdmin):
    """Admin para envio de carta por candidato."""

    list_display = (
        'nome', 'rf', 'email', 'status', 'carta_convocacao_historico', 'criado_em',
    )
    list_filter = ('status', 'carta_convocacao_historico')
    search_fields = ('nome', 'email', 'rf')
    readonly_fields = ('uuid', 'criado_em', 'atualizado_em')
    ordering = ('-criado_em',)
    raw_id_fields = ('carta_convocacao_historico',)
