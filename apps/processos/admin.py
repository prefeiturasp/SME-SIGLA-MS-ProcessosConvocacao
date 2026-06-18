"""Configuração do Django Admin para processos."""

from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from cargos.admin import CargoProcessoInline
from processos.models import ProcessoConvocacao


@admin.register(ProcessoConvocacao)
class ProcessoConvocacaoAdmin(admin.ModelAdmin):
    """Admin for ProcessoConvocacao model."""

    list_display = (
        "concurso_nome",
        "descricao",
        "tipo_escolha",
        "status",
        "data_convocacao",
        "data_corte_vagas",
    )
    list_filter = (
        "status",
        "tipo_escolha",
        "data_convocacao",
        "data_corte_vagas",
    )
    search_fields = ("concurso_nome", "descricao")
    readonly_fields = ("uuid", "criado_em", "atualizado_em")
    ordering = ("-criado_em",)
    inlines = (CargoProcessoInline,)

    fieldsets = (
        (
            "Informações do Concurso",
            {"fields": ("concurso_uuid", "concurso_nome")},
        ),
        (
            "Dados do Processo",
            {"fields": ("descricao", "tipo_escolha", "status")},
        ),
        ("Datas", {"fields": ("data_convocacao", "data_corte_vagas")}),
        (
            "Metadados",
            {
                "fields": ("uuid", "criado_em", "atualizado_em"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(
        self,
        request: HttpRequest,
    ) -> QuerySet[ProcessoConvocacao]:
        return (
            super().get_queryset(request).prefetch_related("cargos_processo")
        )
