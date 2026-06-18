"""Configuração do Django Admin para cargos."""

from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from cargos.models import CargoProcesso


class CargoProcessoInline(admin.TabularInline):
    """Inline para gerenciar cargos do processo."""

    model = CargoProcesso
    extra = 1
    fields = ("cargo_nome",)


@admin.register(CargoProcesso)
class CargoProcessoAdmin(admin.ModelAdmin):
    """Admin for CargoProcesso model."""

    list_display = (
        "processo",
        "cargo_nome",
        "cargo_uuid",
        "cargo_codigo",
        "criado_em",
    )
    list_filter = ("processo", "criado_em")
    search_fields = ("processo__concurso_nome", "cargo_nome")
    ordering = ("processo", "cargo_nome")
    readonly_fields = ("uuid", "criado_em", "atualizado_em")

    fieldsets = (
        (
            "Relacionamento",
            {
                "fields": (
                    "processo",
                    "cargo_nome",
                    "cargo_uuid",
                    "cargo_codigo",
                )
            },
        ),
        (
            "Metadados",
            {
                "fields": ("uuid", "criado_em", "atualizado_em"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[CargoProcesso]:
        return super().get_queryset(request).select_related("processo")
