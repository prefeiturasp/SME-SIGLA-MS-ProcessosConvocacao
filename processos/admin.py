"""
Django admin configuration for the processes module.
"""
from django.contrib import admin
from .models import ProcessoConvocacao



@admin.register(ProcessoConvocacao)
class ProcessoConvocacaoAdmin(admin.ModelAdmin):
    """Admin for ProcessoConvocacao model."""
    
    list_display = ['concurso_nome', 'descricao', 'status', 'data_publicacao']
    list_filter = ['status', 'data_publicacao']
    search_fields = ['concurso_nome', 'descricao']
    readonly_fields = ['data_publicacao', 'data_convocacao']
    ordering = ['-data_publicacao']

    
    def get_queryset(self, request):
        """Optimize queryset with related data."""
        return super().get_queryset(request).select_related()

