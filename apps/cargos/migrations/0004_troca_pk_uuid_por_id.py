"""Troca a PK UUID de ``CargoProcesso`` e refaz a FK para o processo.

Roda depois da 0021 de ``processos``, para a FK recriada a partir de
``processo_novo`` já apontar para o ``id`` de ``ProcessoConvocacao``. O
``unique_together`` que a 0003 tirou volta no fim, com a FK no lugar.
"""

import uuid

import django.db.models.deletion
from django.core.management.color import no_style
from django.db import migrations, models

MODELOS = ["CargoProcesso"]


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
    modelos = [apps.get_model("cargos", nome) for nome in MODELOS]
    with conexao.cursor() as cursor:
        for sql in conexao.ops.sequence_reset_sql(no_style(), modelos):
            cursor.execute(sql)


class Migration(migrations.Migration):
    """Promove ``novo_id`` a PK ``id`` e recria FK e ``unique_together``.

    O nome provisório ``novo_id`` evita colidir com o ``id`` que o Django
    cria no estado intermediário, quando o modelo fica sem PK.
    ``novo_id`` vira NOT NULL antes de virar PK: na volta, o PostgreSQL
    só aceita o DROP NOT NULL depois que a PK sai.
    """

    dependencies = [
        ("cargos", "0003_remove_fk_processo"),
        ("processos", "0021_troca_pk_uuid_por_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cargoprocesso",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, unique=True
            ),
        ),
        migrations.AlterField(
            model_name="cargoprocesso",
            name="novo_id",
            field=models.BigIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name="cargoprocesso",
            name="novo_id",
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name="ID",
            ),
        ),
        migrations.RenameField(
            model_name="cargoprocesso",
            old_name="novo_id",
            new_name="id",
        ),
        migrations.RenameField(
            model_name="cargoprocesso",
            old_name="processo_novo",
            new_name="processo",
        ),
        migrations.AlterField(
            model_name="cargoprocesso",
            name="processo",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cargos_processo",
                to="processos.processoconvocacao",
                verbose_name="Processo de Convocação",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="cargoprocesso",
            unique_together={("processo", "cargo_nome")},
        ),
        migrations.RunPython(reiniciar_sequencias, migrations.RunPython.noop),
    ]
