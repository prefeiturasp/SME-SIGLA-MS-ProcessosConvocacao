"""Repositórios de acesso a dados do app envio_email."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from envio_email.models import (
    EnvioEmail,
    EnvioEmailCandidato,
    EnvioEmailConteudo,
)
from envio_email.serializers import (
    EnvioEmailCandidatoSerializer,
    EnvioEmailConteudoSerializer,
    EnvioEmailDetalheSerializer,
    EnvioEmailSerializer,
)


class EnvioEmailRepository:
    """Consultas e persistência de registros de envio de e-mail."""

    @staticmethod
    def serializar(envio: EnvioEmail) -> dict[str, Any]:
        """Converta um envio de e-mail em dicionário."""
        return EnvioEmailSerializer(envio).data

    @staticmethod
    def serializar_detalhe(envio: EnvioEmail) -> dict[str, Any]:
        """Converta um envio de e-mail com candidatos em dicionário."""
        return EnvioEmailDetalheSerializer(envio).data

    @classmethod
    def serializar_lista(
        cls, envios: list[EnvioEmail]
    ) -> list[dict[str, Any]]:
        """Converta uma lista de envios em dicionários."""
        return EnvioEmailSerializer(envios, many=True).data

    @classmethod
    def listar_todos(cls) -> list[dict[str, Any]]:
        """List all email sends."""
        envios = list(
            EnvioEmail.objects.prefetch_related("candidatos").order_by(
                "-criado_em"
            )
        )
        return cls.serializar_lista(envios)

    @classmethod
    def obter_por_uuid(cls, uuid: UUID) -> dict[str, Any] | None:
        """Retorne o envio pelo UUID ou None."""
        envio = (
            EnvioEmail.objects.prefetch_related("candidatos")
            .filter(uuid=uuid)
            .first()
        )
        if envio is None:
            return None
        return cls.serializar_detalhe(envio)

    @classmethod
    def criar(cls, **dados: Any) -> dict[str, Any]:
        """Crie um registro de envio de e-mail."""
        envio = EnvioEmail.objects.create(**dados)
        return cls.serializar(envio)


class EnvioEmailCandidatoRepository:
    """Consultas e persistência de candidatos no envio de e-mail."""

    @staticmethod
    def serializar(candidato: EnvioEmailCandidato) -> dict[str, Any]:
        """Converta um candidato do envio em dicionário."""
        dados = EnvioEmailCandidatoSerializer(candidato).data
        dados["uuid"] = candidato.uuid
        return dados

    @classmethod
    def criar(cls, **dados: Any) -> dict[str, Any]:
        """Crie um candidato no envio de e-mail."""
        envio_email_uuid = dados.pop("envio_email")
        candidato = EnvioEmailCandidato.objects.create(
            **dados, envio_email_id=UUID(envio_email_uuid)
        )
        return cls.serializar(candidato)

    @classmethod
    def obter_por_uuid(cls, uuid: UUID) -> dict[str, Any] | None:
        """Retorne o candidato pelo UUID ou None."""
        candidato = EnvioEmailCandidato.objects.filter(uuid=uuid).first()
        if candidato is None:
            return None
        return cls.serializar(candidato)

    @classmethod
    def atualizar_status(
        cls,
        uuid: UUID,
        *,
        status: str,
        status_detalhe: str,
    ) -> bool:
        """Atualize o status do candidato. Retorne False se não encontrado."""
        candidato = EnvioEmailCandidato.objects.filter(uuid=uuid).first()
        if candidato is None:
            return False
        candidato.status = status
        candidato.status_detalhe = status_detalhe
        candidato.save(
            update_fields=["status", "status_detalhe", "atualizado_em"]
        )
        return True


class EnvioEmailConteudoRepository:
    """Consultas e persistência de templates de conteúdo de e-mail."""

    @staticmethod
    def serializar(conteudo: EnvioEmailConteudo) -> dict[str, Any]:
        """Converta um template de conteúdo em dicionário."""
        return EnvioEmailConteudoSerializer(conteudo).data

    @classmethod
    def serializar_lista(
        cls, conteudos: list[EnvioEmailConteudo]
    ) -> list[dict[str, Any]]:
        """Converta uma lista de templates em dicionários."""
        return EnvioEmailConteudoSerializer(conteudos, many=True).data

    @classmethod
    def listar(cls, *, tipo: str | None = None) -> list[dict[str, Any]]:
        """List content templates, optionally filtered by type."""
        queryset = EnvioEmailConteudo.objects.all().order_by("tipo")
        if tipo is not None:
            queryset = queryset.filter(tipo=tipo)
        return cls.serializar_lista(list(queryset))

    @classmethod
    def carregar_instancia_por_uuid(
        cls, uuid: UUID
    ) -> EnvioEmailConteudo | None:
        """Carregue instância do template para operações de escrita."""
        return EnvioEmailConteudo.objects.filter(uuid=uuid).first()

    @classmethod
    def obter_por_uuid(cls, uuid: UUID) -> dict[str, Any] | None:
        """Retorne o template pelo UUID ou None."""
        conteudo = cls.carregar_instancia_por_uuid(uuid)
        if conteudo is None:
            return None
        return cls.serializar(conteudo)

    @classmethod
    def obter_por_tipo(cls, tipo: str) -> dict[str, Any] | None:
        """Retorne o template pelo tipo ou None."""
        conteudo = EnvioEmailConteudo.objects.filter(tipo=tipo).first()
        if conteudo is None:
            return None
        return cls.serializar(conteudo)
