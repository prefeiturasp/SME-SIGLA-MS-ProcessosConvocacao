"""Tira a FK ``processo`` de ``CargoProcesso`` antes da troca da PK.

A 0021 de ``processos`` só consegue tirar a PK do ``uuid`` de
``ProcessoConvocacao`` quando nenhuma FK aponta para ele. O vínculo fica
guardado em ``processo_novo`` (0002 e 0020) e volta a ser a FK na 0004.
O ``unique_together`` sai antes, porque inclui o campo removido, e a 0004
o recria.

Na volta, a FK é recriada como coluna NOT NULL sem default, o que só
funciona com a tabela vazia.
"""

from django.db import migrations


class Migration(migrations.Migration):
    """Remove o ``unique_together`` e a FK ``processo``."""

    dependencies = [
        ("cargos", "0002_adiciona_novo_id"),
        ("processos", "0020_popula_novo_id"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="cargoprocesso",
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name="cargoprocesso",
            name="processo",
        ),
    ]
