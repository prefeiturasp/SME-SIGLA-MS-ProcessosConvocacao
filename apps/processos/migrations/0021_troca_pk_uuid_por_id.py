"""Troca a PK UUID de ``ProcessoConvocacao`` pelo ``id`` carregado na 0020.

Depende da 0003 de ``cargos``, que tira a FK de ``CargoProcesso`` para o
processo, porque o banco só deixa remover a PK do ``uuid`` quando nenhuma
FK aponta para ela. A 0004 de ``cargos`` recria essa FK apontando para o
``id``.
"""

import uuid

from django.core.management.color import no_style
from django.db import migrations, models

MODELOS = ["ProcessoConvocacao"]


def reiniciar_sequencias(apps, schema_editor):
    """Faz a sequência de cada ``id`` continuar depois do maior valor.

    No PostgreSQL a coluna vira identity começando em 1, e sem este passo
    o primeiro INSERT colidiria com os ids da carga. No SQLite a lista de
    comandos vem vazia.

    Args:
        apps: Registro de modelos históricos da migration.
        schema_editor: Editor de esquema da conexão em uso.
    """
    conexao = schema_editor.connection
    modelos = [apps.get_model("processos", nome) for nome in MODELOS]
    with conexao.cursor() as cursor:
        for sql in conexao.ops.sequence_reset_sql(no_style(), modelos):
            cursor.execute(sql)


class Migration(migrations.Migration):
    """Promove ``novo_id`` a PK ``id`` de ``ProcessoConvocacao``.

    O nome provisório ``novo_id`` evita colidir com o ``id`` que o Django
    cria no estado intermediário, quando o modelo fica sem PK.
    ``novo_id`` vira NOT NULL antes de virar PK: na volta, o PostgreSQL
    só aceita o DROP NOT NULL depois que a PK sai.
    """

    dependencies = [
        ("processos", "0020_popula_novo_id"),
        ("cargos", "0003_remove_fk_processo"),
    ]

    operations = [
        migrations.AlterField(
            model_name="processoconvocacao",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, unique=True
            ),
        ),
        migrations.AlterField(
            model_name="processoconvocacao",
            name="novo_id",
            field=models.BigIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name="processoconvocacao",
            name="novo_id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
        migrations.RenameField(
            model_name="processoconvocacao",
            old_name="novo_id",
            new_name="id",
        ),
        migrations.RunPython(reiniciar_sequencias, migrations.RunPython.noop),
    ]
