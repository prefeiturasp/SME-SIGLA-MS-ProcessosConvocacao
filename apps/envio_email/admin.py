"""Configuração do Django Admin para envio de e-mail."""

from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest
from envio_email.models import (
    EnvioEmail,
    EnvioEmailCandidato,
    EnvioEmailConteudo,
)


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

    list_display = ("tipo", "assunto", "atualizado_em", "criado_em")
    readonly_fields = ("uuid", "tipo", "criado_em", "atualizado_em")
    fields = (
        "tipo",
        "assunto",
        "conteudo",
        "uuid",
        "criado_em",
        "atualizado_em",
    )
    ordering = ("tipo",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(
        self,
        request: HttpRequest,
        obj: EnvioEmailConteudo | None = None,
    ) -> bool:
        return False
