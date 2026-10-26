"""Modelos compartilhados do projeto."""

import uuid

from django.db import models


class BaseModel(models.Model):
    """Modelo base abstrato com campos comuns.

    A PK é o ``id`` (``BigAutoField``) que o Django cria a partir do
    ``default_auto_field`` do app. O ``uuid`` continua único e segue como
    o identificador público do registro.
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    criado_em = models.DateTimeField(
        auto_now_add=True, verbose_name="Criado em"
    )
    atualizado_em = models.DateTimeField(
        auto_now=True, verbose_name="Atualizado em"
    )

    class Meta:
        abstract = True
        ordering = ["-criado_em"]
