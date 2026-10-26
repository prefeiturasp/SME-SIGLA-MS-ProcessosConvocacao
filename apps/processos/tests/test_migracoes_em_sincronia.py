"""Teste de sincronia entre os models e os arquivos de migration."""

import pytest
from django.core.management import call_command


@pytest.mark.django_db
def test_modelos_e_migrations_em_sincronia(settings):
    """``makemigrations --check`` não encontra mudança pendente.

    A suíte normal desliga as migrations em ``MIGRATION_MODULES``; o
    teste restaura o comportamento padrão para o comando enxergar os
    arquivos reais.
    """
    settings.MIGRATION_MODULES = {}

    call_command("makemigrations", "--check", "--dry-run", verbosity=0)
