"""
Django admin configuration for the processes module.
"""
from django.contrib import admin
from auditlog.admin import LogEntryAdmin
from auditlog.models import LogEntry
from .models import ProcessoConvocacao, CargoProcesso


class CargoProcessoInline(admin.TabularInline):
    """Inline para gerenciar cargos do processo."""
    model = CargoProcesso
    extra = 1
    fields = ('nome',)


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
        'processo', 'nome', 'cargo_uuid', 'criado_em'
    )
    list_filter = ('processo', 'criado_em')
    search_fields = ('processo__concurso_nome', 'nome')
    ordering = ('processo', 'nome')
    readonly_fields = ('uuid', 'criado_em', 'atualizado_em')
    
    fieldsets = (
        ('Relacionamento', {
            'fields': ('processo', 'nome', 'cargo_uuid')
        }),
        ('Metadados', {
            'fields': ('uuid', 'criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with related data."""
        return super().get_queryset(request).select_related('processo')
