"""Configuração do Django Admin para processos."""

from __future__ import annotations

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import (
    CargoProcesso,
    EnvioEmail,
    EnvioEmailCandidato,
    EnvioEmailConteudo,
    ProcessoConvocacao,
)


class CargoProcessoInline(admin.TabularInline):
    """Inline para gerenciar cargos do processo."""

    model = CargoProcesso
    extra = 1
    fields = ("cargo_nome",)


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
        """Otimiza queryset com cargos relacionados.
        
        Args:
            self: Instância do objeto.
            request: Requisição HTTP recebida.
        
        Returns:
            QuerySet filtrado conforme os parâmetros.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        return (
            super().get_queryset(request).prefetch_related("cargos_processo")
        )


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
        """Otimiza queryset com processo relacionado.
        
        Args:
            self: Instância do objeto.
            request: Requisição HTTP recebida.
        
        Returns:
            QuerySet filtrado conforme os parâmetros.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        return super().get_queryset(request).select_related("processo")


class EnvioEmailCandidatoInline(admin.TabularInline):
    """Inline para candidatos do envio de e-mail."""

    model = EnvioEmailCandidato
    extra = 0
    readonly_fields = ("uuid", "criado_em", "atualizado_em")
    fields = ("nome", "rf", "email", "status", "status_detalhe", "conteudo")


@admin.register(EnvioEmail)
class EnvioEmailAdmin(admin.ModelAdmin):
    """Admin para histórico de envio de e-mail."""

    list_display = (
        "processo_nome",
        "processo_uuid",
        "tipo",
        "quantidade_candidatos",
        "criado_em",
    )
    list_filter = ("tipo", "criado_em")
    search_fields = ("processo_nome",)
    readonly_fields = ("uuid", "criado_em", "atualizado_em")
    ordering = ("-criado_em",)
    inlines = (EnvioEmailCandidatoInline,)


@admin.register(EnvioEmailCandidato)
class EnvioEmailCandidatoAdmin(admin.ModelAdmin):
    """Admin para envio de e-mail por candidato."""

    list_display = (
        "nome",
        "rf",
        "email",
        "status",
        "envio_email",
        "criado_em",
    )
    list_filter = ("status", "envio_email")
    search_fields = ("nome", "email", "rf")
    readonly_fields = ("uuid", "criado_em", "atualizado_em")
    ordering = ("-criado_em",)
    raw_id_fields = ("envio_email",)


@admin.register(EnvioEmailConteudo)
class EnvioEmailConteudoAdmin(admin.ModelAdmin):
    """Admin para templates de conteúdo de e-mail por tipo."""

    list_display = ("tipo", "atualizado_em", "criado_em")
    readonly_fields = ("uuid", "tipo", "criado_em", "atualizado_em")
    fields = ("tipo", "conteudo", "uuid", "criado_em", "atualizado_em")
    ordering = ("tipo",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        """Executa has add permission.
        
        Args:
            self: Instância do objeto.
            request: Requisição HTTP recebida.
        
        Returns:
            Verdadeiro se a condição for satisfeita.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        return False

    def has_delete_permission(
        self,
        request: HttpRequest,
        obj: EnvioEmailConteudo | None = None,
    ) -> bool:
        """Executa has delete permission.
        
        Args:
            self: Instância do objeto.
            request: Requisição HTTP recebida.
            obj: Instância do objeto processado.
        
        Returns:
            Verdadeiro se a condição for satisfeita.
        
        Raises:
            Nenhuma exceção específica documentada.
        """
        return False
